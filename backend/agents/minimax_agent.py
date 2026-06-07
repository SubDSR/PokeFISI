"""Nivel 3 - Agente Minimax con poda Alfa-Beta y optimizaciones.

Optimizaciones implementadas:
  A) Poda alfa-beta canónica.
  B) Ordenamiento heurístico de acciones para mejorar la poda alfa-beta.
  C) Early cutoffs en estados terminales.
  D) Tabla de transposición (memoización).
  E) Control de branching factor (top-K acciones).

Mejoras respecto a la versión anterior:
  - _quick_score() para acciones SWITCH ahora incorpora ventaja de tipo
    del Pokémon entrante vs el rival activo, en lugar de solo hp_ratio.
    Antes: score_switch = hp_ratio_entrante  (ignora si el cambio mejora
    la situación táctica o la empeora)
    Ahora: score_switch = type_advantage × 0.5 + hp_ratio × 0.4
           + vulnerability_reduction × 0.1
    Esto hace que Minimax explore primero los cambios tácticamente buenos
    (ej: cambiar a Bulbasaur cuando el rival usa un Pokémon de agua),
    mejorando la poda alfa-beta y la calidad de las decisiones.

Complejidad:
  - Sin poda:  O((b·b)^d)  donde b = branching factor, d = profundidad
  - Con poda:  O((b·b)^(d/2)) en mejor caso con buen ordenamiento
"""

from __future__ import annotations

import random
import time

from backend.agents.base import BaseAgent
from backend.agents.heuristics import evaluate_state
from backend.battle.damage import calculate_damage
from backend.battle.models import BattleAction
from backend.battle.simulator import simulate_action, simulate_turn
from backend.battle.state import BattleState
from backend.data.types import get_type_multiplier

_INF = float("inf")


class MinimaxAgent(BaseAgent):
    """Agente adversarial Minimax con poda alfa-beta."""

    def __init__(
        self,
        name: str = "MinimaxAgent",
        depth: int = 3,
        weights: list[float] | None = None,
        enable_transposition_table: bool = True,
        top_k_actions: int = 4,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(name)
        self.depth = max(1, depth)
        self.weights = list(weights) if weights else [0.20, 0.10, 0.05, 0.15, 0.30, 0.10, 0.10]
        self.enable_transposition_table = enable_transposition_table
        self.top_k_actions = top_k_actions
        self._rng_seed: int = rng.randrange(1 << 31) if rng else 42

        self._nodes: int = 0
        self._pruned: int = 0
        self._tt_hits: int = 0
        self._player_index: int = 0
        self._tt: dict[int, tuple[int, float]] = {}
        self._last_action_type: str = ""  # tracks last chosen action type across turns

        self.last_choice_details: dict = {}

    # ──────────────────────────────────────────
    # API pública
    # ──────────────────────────────────────────

    def choose_action(
        self,
        state: BattleState,
        player_index: int,
        legal_actions: list[BattleAction],
    ) -> BattleAction:
        """Selecciona la mejor acción legal usando Minimax con poda alfa-beta."""
        if not legal_actions:
            raise ValueError("Lista de acciones legales vacía.")

        t0 = time.perf_counter()
        self._nodes = 0
        self._pruned = 0
        self._tt_hits = 0
        self._player_index = player_index
        if self.enable_transposition_table:
            self._tt = {}

        best_action = legal_actions[0]
        best_val = -_INF
        alpha = -_INF
        beta = _INF

        opp_index = 1 - player_index
        opp_legal = state.get_legal_actions(opp_index)
        if not opp_legal:
            return legal_actions[0]

        ranking_state_mine = self._get_ranking_state_for_my_actions(state, opp_legal)
        ordered_mine = self._rank_actions(
            ranking_state_mine, legal_actions, player_index, maximize=True,
            prev_switch=(self._last_action_type == "switch"),
        )
        ordered_mine = self._apply_topk_with_move_guarantee(ordered_mine)

        for action in ordered_mine:
            worst = self._minimize_over_opponent(
                state, action, opp_legal, alpha, beta, self.depth,
                next_prev_my_switch=(action.action_type == "switch"),
            )
            if worst > best_val:
                best_val = worst
                best_action = action
            alpha = max(alpha, best_val)
            if alpha >= beta:
                self._pruned += 1
                break

        self._last_action_type = best_action.action_type
        elapsed = time.perf_counter() - t0
        self.last_choice_details = {
            "strategy": "minimax",
            "depth_reached": self.depth,
            "nodes_evaluated": self._nodes,
            "nodes_pruned": self._pruned,
            "transposition_hits": self._tt_hits,
            "time_taken": round(elapsed, 4),
            "chosen_action": best_action.label,
            "evaluation_score": round(best_val, 4),
            "player_index": player_index,
        }
        return best_action

    # ──────────────────────────────────────────
    # Núcleo del algoritmo
    # ──────────────────────────────────────────

    def _minimize_over_opponent(
        self,
        state: BattleState,
        my_action: BattleAction,
        opp_legal: list[BattleAction],
        alpha: float,
        beta: float,
        depth: int,
        next_prev_my_switch: bool = False,
    ) -> float:
        """Para una acción propia fija, devuelve el valor mínimo que puede lograr el oponente.

        Se usa maximize=True para ordenar las acciones del oponente de mayor a menor score
        (sus movimientos mas dañinos primero). Esto garantiza dos cosas:
          1. El top_k selecciona los movimientos MAS PELIGROSOS del rival (no los mas debiles).
          2. Las ramas con mayor daño se exploran primero, maximizando los cortes beta.
        Usar maximize=False (el bug anterior) ordenaba ascendente: el movimiento letal del rival
        quedaba en la ultima posicion y podia ser excluido por top_k, haciendo creer al Minimax
        que ciertas posiciones eran seguras cuando no lo eran.
        """
        # Bug 6: si el agente hace switch, el oponente enfrentará un Pokémon diferente.
        # Rankear sus acciones sobre el estado post-switch para no excluir por top_k
        # ataques que serían devastadores contra el entrante pero parecían débiles antes.
        ranking_state = state
        if my_action.action_type == "switch":
            temp = state.clone()
            branch_rng = random.Random(self._rng_seed ^ self._hash_state(state))
            simulate_action(temp, self._player_index, my_action, branch_rng)
            ranking_state = temp

        ordered_opp = self._rank_actions(
            ranking_state, opp_legal, 1 - self._player_index, maximize=True
        )
        ordered_opp = ordered_opp[: self.top_k_actions]

        worst = _INF
        inner_beta = beta

        for opp_action in ordered_opp:
            new_state = self._simulate(state, my_action, opp_action)
            val = self._search(new_state, depth - 1, alpha, inner_beta,
                               prev_my_switch=next_prev_my_switch)

            if val < worst:
                worst = val
            inner_beta = min(inner_beta, worst)
            if worst <= alpha:
                self._pruned += 1
                break

        return worst

    def _search(
        self, state: BattleState, depth: int, alpha: float, beta: float,
        prev_my_switch: bool = False,
    ) -> float:
        """Minimax recursivo con poda alfa-beta desde la perspectiva del jugador."""
        self._nodes += 1

        if self.enable_transposition_table:
            h = self._hash_state(state)
            cached = self._tt.get(h)
            if cached is not None and cached[0] >= depth:
                self._tt_hits += 1
                return cached[1]

        if state.battle_over():
            return self._terminal_value(state)

        if depth == 0:
            return evaluate_state(state, self._player_index, self.weights)

        my_legal = state.get_legal_actions(self._player_index)
        opp_legal = state.get_legal_actions(1 - self._player_index)

        if not my_legal or not opp_legal:
            return evaluate_state(state, self._player_index, self.weights)

        ranking_state_mine = self._get_ranking_state_for_my_actions(state, opp_legal)
        ordered_mine = self._rank_actions(
            ranking_state_mine, my_legal, self._player_index, maximize=True,
            prev_switch=prev_my_switch,
        )
        ordered_mine = self._apply_topk_with_move_guarantee(ordered_mine)

        best = -_INF
        for my_action in ordered_mine:
            worst = self._minimize_over_opponent(
                state, my_action, opp_legal, alpha, beta, depth,
                next_prev_my_switch=(my_action.action_type == "switch"),
            )
            if worst > best:
                best = worst
            alpha = max(alpha, best)
            if alpha >= beta:
                self._pruned += 1
                break

        if self.enable_transposition_table:
            self._tt[h] = (depth, best)

        return best

    # ──────────────────────────────────────────
    # Ordenamiento heurístico
    # ──────────────────────────────────────────

    def _rank_actions(
        self,
        state: BattleState,
        actions: list[BattleAction],
        acting_player: int,
        maximize: bool,
        prev_switch: bool = False,
    ) -> list[BattleAction]:
        """Ordena acciones por valor heurístico estimado.

        Explorar primero las ramas más prometedoras maximiza los cortes alfa-beta.
        Si el turno anterior fue un switch propio (prev_switch=True), penaliza
        volver a hacer switch para desincentivar el bucle switch-ping-pong.
        """
        scored: list[tuple[float, BattleAction]] = []
        for action in actions:
            score = self._quick_score(state, acting_player, action)
            # Penalizar switch consecutivo propio: desincentivar ping-pong sin bloquearlo
            if (prev_switch
                    and action.action_type == "switch"
                    and acting_player == self._player_index):
                score -= 0.50
            scored.append((score, action))

        scored.sort(key=lambda x: x[0], reverse=maximize)
        return [a for _, a in scored]

    def _apply_topk_with_move_guarantee(
        self, ranked: list[BattleAction]
    ) -> list[BattleAction]:
        """Toma top_k acciones garantizando que al menos un movimiento (move) esté incluido.

        Sin esta garantía, cuando el oponente puede OHKOar al activo, _quick_score
        devuelve -2.0 para todos los movimientos y los switches puntúan más alto.
        El resultado es que top_k queda formado solo por switches y el árbol Minimax
        nunca explora ramas de ataque, causando el bucle de switches infinito.
        """
        top_k = ranked[: self.top_k_actions]
        if any(a.action_type == "move" for a in top_k):
            return top_k
        best_move = next((a for a in ranked if a.action_type == "move"), None)
        if best_move is None:
            return top_k  # Solo hay switches disponibles (situación de lucha pura)
        result = list(top_k)
        # Reemplaza el switch de menor prioridad con el mejor movimiento disponible
        for i in range(len(result) - 1, -1, -1):
            if result[i].action_type == "switch":
                result[i] = best_move
                return result
        return result

    def _quick_score(
        self, state: BattleState, acting_player: int, action: BattleAction
    ) -> float:
        """Puntuación rápida de una acción sin simular el turno completo."""
        my_team = state.team_of(acting_player)
        opp_team = state.opponent_of(acting_player)
        attacker = my_team.active_pokemon
        defender = opp_team.active_pokemon

        if action.action_type == "move":
            if action.index < 0 or action.index >= len(attacker.moves):
                return 0.0
            move = attacker.moves[action.index]
            if not move.has_pp():
                return -10.0

            type_mod = get_type_multiplier(move.move_type, defender.pokemon_type)
            if type_mod == 0.0:
                return -5.0  # movimiento inútil (inmunidad de tipo)

            expected_dmg = calculate_damage(attacker, defender, move) * move.accuracy

            if expected_dmg >= defender.hp:
                # El KO solo tiene valor si el movimiento llega a ejecutarse.
                # Si el rival va primero y puede OHKOarme, muero antes de atacar
                # → el turno se cancela → el KO es ilusorio y no debe premiarse.
                if attacker.speed >= defender.speed:
                    return 2.0  # voy primero: KO garantizado y real
                max_opp_dmg = max(
                    (calculate_damage(defender, attacker, m) * m.accuracy
                     for m in defender.moves if m.has_pp()),
                    default=0.0,
                )
                if max_opp_dmg >= attacker.hp:
                    return -2.0  # rival va primero y me mata: movimiento nunca se ejecuta
                return 2.0  # rival va primero pero no puede OHKOarme: KO real

            # Solo penalizamos nuestras propias acciones cuando el rival va primero y
            # puede matarnos sin que lo matemos nosotros (Bugs 4+1 del prompt anterior).
            if acting_player == self._player_index and defender.speed > attacker.speed:
                max_opp_dmg = max(
                    (calculate_damage(defender, attacker, m) * m.accuracy
                     for m in defender.moves if m.has_pp()),
                    default=0.0,
                )
                if max_opp_dmg >= attacker.hp:
                    return -2.0  # muere antes de actuar sin matar al rival

            base_score = expected_dmg / max(1, defender.max_hp)

            # Penalizar ataques de tipo resistido para que nunca superen a ataques
            # neutros de mayor poder base, incluso considerando mejor precisión.
            # Sin esto, BubbleBeam (acc=1.0, 0.5×) puede superar a ZenHeadbutt
            # (acc=0.9, 1.0×) cuando el Minimax prioriza certeza sobre daño bruto.
            if type_mod < 1.0:
                base_score *= type_mod

            return base_score

        if action.action_type == "switch":
            return self._score_switch(action, my_team, opp_team)

        if action.action_type == "struggle":
            return 0.01

        return 0.0

    def _score_switch(self, action: BattleAction, my_team, opp_team) -> float:
        """Evalúa la calidad de un cambio considerando ventaja de tipo.

        Componentes:
          - Penalización switch suicida (-2.0): entrante muere garantizadamente Y el
            activo actual no muere este turno (switch genuinamente evitable).
          - Penalización suave (hasta -0.5): todos los switches son arriesgados porque
            el activo actual también moriría; el agente elige el menos malo.
          - type_advantage (peso 0.35): multiplicador de tipo del mejor movimiento
            del Pokémon entrante vs el rival activo. Normalizado a [0, 1].
          - hp_ratio (peso 0.25): HP actual / HP máximo del Pokémon entrante.
          - vulnerability_score (peso 0.25): 1 − vulnerabilidad ante el activo rival.
          - team_vulnerability (peso 0.15): 1 − vulnerabilidad ante TODO el equipo rival.
            Penaliza switches que son "seguros ahora" pero crean matchups futuros malos.

        El score final está en [-2.0, 1.0].
        """
        if action.index < 0 or action.index >= len(my_team.pokemons):
            return 0.0

        incoming = my_team.pokemons[action.index]
        opp_active = opp_team.active_pokemon
        current_active = my_team.active_pokemon

        # Bug 2: detectar si el activo actual también va a morir este turno.
        # Si es así, ningún switch es seguro y penalizar con -2.0 bloquea todas las opciones.
        current_also_dies = False
        if opp_active.speed > current_active.speed:
            opp_vs_current = max(
                (calculate_damage(opp_active, current_active, m) * m.accuracy
                 for m in opp_active.moves if m.has_pp()),
                default=0.0,
            )
            if opp_vs_current >= current_active.hp:
                current_also_dies = True

        # Penalización por switch suicida garantizado
        if opp_active.speed > incoming.speed:
            opp_best_dmg = max(
                (calculate_damage(opp_active, incoming, m) * m.accuracy
                 for m in opp_active.moves if m.has_pp()),
                default=0.0,
            )
            if opp_best_dmg >= incoming.hp:
                if current_also_dies:
                    # Activo también muere: usar penalización proporcional para elegir el menos malo
                    damage_ratio = min(1.0, opp_best_dmg / max(1, incoming.hp))
                    return -0.5 * damage_ratio
                return -2.0  # Switch genuinamente suicida y evitable

        # Ventaja de tipo: mejor multiplicador del entrante
        best_mult_incoming = max(
            (get_type_multiplier(m.move_type, opp_active.pokemon_type)
             for m in incoming.moves if m.has_pp()),
            default=1.0,
        )
        type_advantage = min(best_mult_incoming / 4.0, 1.0)

        # HP del entrante normalizado
        hp_ratio = incoming.hp / max(1, incoming.max_hp)

        # Vulnerabilidad ante el activo rival
        best_mult_opp_vs_incoming = max(
            (get_type_multiplier(m.move_type, incoming.pokemon_type)
             for m in opp_active.moves if m.has_pp()),
            default=1.0,
        )
        vulnerability_score = 1.0 - min(best_mult_opp_vs_incoming / 4.0, 1.0)

        # Vulnerabilidad ante TODO el equipo rival
        opp_alive = [p for p in opp_team.pokemons if not p.is_fainted()]
        worst_opp_mult = max(
            (get_type_multiplier(m.move_type, incoming.pokemon_type)
             for opp in opp_alive
             for m in opp.moves if m.has_pp()),
            default=1.0,
        )
        team_vulnerability = 1.0 - min(worst_opp_mult / 4.0, 1.0)

        # Penaliza cambiar a un Pokémon que también pierde el matchup actual.
        incoming_best_dmg = max(
            (calculate_damage(incoming, opp_active, m) * m.accuracy
             for m in incoming.moves if m.has_pp()),
            default=0.0,
        )
        opp_best_dmg_vs_incoming = max(
            (calculate_damage(opp_active, incoming, m) * m.accuracy
             for m in opp_active.moves if m.has_pp()),
            default=0.0,
        )
        dmg_ratio_in = incoming_best_dmg / max(1, opp_active.max_hp)
        dmg_ratio_out = opp_best_dmg_vs_incoming / max(1, incoming.max_hp)
        matchup_gain = max(-1.0, min(1.0, dmg_ratio_in - dmg_ratio_out))

        # Costo de oportunidad: penalizar el switch cuando el activo actual puede infligir
        # daño relevante y el entrante no mejora la ventaja de tipo. Cambiar en esa
        # situación desperdicia el turno de ataque sin ningún beneficio táctico.
        current_best_dmg = max(
            (calculate_damage(current_active, opp_active, m) * m.accuracy
             for m in current_active.moves if m.has_pp()),
            default=0.0,
        )
        current_dmg_ratio = current_best_dmg / max(1, opp_active.max_hp)
        opportunity_penalty = 0.0
        if current_dmg_ratio > 0.06 and best_mult_incoming <= 1.0:
            # El activo puede hacer daño y el entrante no tiene ventaja de tipo:
            # el switch no mejora el matchup y cuesta el turno de ataque.
            opportunity_penalty = min(0.30, current_dmg_ratio * 2.5)

        return (0.28 * type_advantage
                + 0.20 * hp_ratio
                + 0.20 * vulnerability_score
                + 0.12 * team_vulnerability
                + 0.20 * matchup_gain
                - opportunity_penalty)

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _get_ranking_state_for_my_actions(
        self,
        state: BattleState,
        opp_legal: list[BattleAction],
    ) -> BattleState:
        """Estado representativo para rankear las acciones propias del agente.

        Los switches resuelven antes que los ataques. Si el rival puede cambiar,
        el Pokémon entrante estará en campo cuando el agente ataque, no el saliente.
        Sin este ajuste, el ranking puede poner en top_k ataques con ventaja de tipo
        contra el Pokémon saliente que resultan perjudiciales contra el entrante.

        Estrategia: simular el switch rival más amenazante (el que envía al Pokémon
        con mayor daño potencial al activo propio) y usar ese estado solo para rankear.
        La simulación real en _simulate() sigue usando el estado original.
        """
        opp_switches = [a for a in opp_legal if a.action_type == "switch"]
        if not opp_switches:
            return state

        my_active = state.team_of(self._player_index).active_pokemon
        opp_team = state.opponent_of(self._player_index)

        best_switch_state = state
        best_threat = 0.0
        for switch_action in opp_switches:
            incoming = opp_team.pokemons[switch_action.index]
            if incoming.is_fainted():
                continue
            threat = max(
                (calculate_damage(incoming, my_active, m) * m.accuracy
                 for m in incoming.moves if m.has_pp()),
                default=0.0,
            )
            if threat > best_threat:
                best_threat = threat
                temp = state.clone()
                branch_rng = random.Random(self._rng_seed)
                simulate_action(temp, 1 - self._player_index, switch_action, branch_rng)
                best_switch_state = temp

        return best_switch_state

    def _simulate(
        self,
        state: BattleState,
        my_action: BattleAction,
        opp_action: BattleAction,
    ) -> BattleState:
        """Simula un turno usando un rng derivado del estado actual.

        Usar un rng derivado del hash del estado garantiza que dos ramas que
        lleguen al mismo estado por caminos distintos usen el mismo rng,
        eliminando el sesgo por orden de exploración que afecta movimientos
        con precisión < 1.0 (como ZenHeadbutt acc=0.9 vs BubbleBeam acc=1.0).
        """
        branch_rng = random.Random(self._rng_seed ^ self._hash_state(state))
        if self._player_index == 0:
            return simulate_turn(state, my_action, opp_action, branch_rng)
        return simulate_turn(state, opp_action, my_action, branch_rng)

    def _terminal_value(self, state: BattleState) -> float:
        winner = state.winner()
        my_name = state.team_of(self._player_index).trainer_name
        if winner == my_name:
            return 1000.0
        if winner == "Empate":
            return 0.0
        return -1000.0

    def _hash_state(self, state: BattleState) -> int:
        """Hash rápido y reproducible del estado para la tabla de transposición."""
        parts: list[int] = [state.turn_number]
        for team in state.teams:
            parts.append(team.active_index)
            for p in team.pokemons:
                parts.append(p.hp)
                for m in p.moves:
                    parts.append(m.pp)
        return hash(tuple(parts))
