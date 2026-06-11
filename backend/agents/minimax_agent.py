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
from backend.battle.models import BattleAction, BattleMove, BattlePokemon
from backend.battle.simulator import simulate_turn
from backend.battle.state import BattleState
from backend.data.types import get_type_multiplier

_INF = float("inf")


class MinimaxAgent(BaseAgent):
    """Agente adversarial Minimax con poda alfa-beta."""

    def __init__(
        self,
        name: str = "MinimaxAgent",
        depth: int = 4,
        weights: list[float] | None = None,
        enable_transposition_table: bool = True,
        top_k_actions: int = 6,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(name)
        self.depth = max(1, depth)
        self.weights = list(weights) if weights else [0.4, 0.2, 0.1, 0.2, 0.1]
        self.enable_transposition_table = enable_transposition_table
        self.top_k_actions = top_k_actions
        self._sim_rng = rng or random.Random(42)

        self._nodes: int = 0
        self._pruned: int = 0
        self._tt_hits: int = 0
        self._player_index: int = 0
        self._tt: dict[int, tuple[int, float]] = {}

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

        ordered_mine = self._select_search_actions(
            state, legal_actions, player_index, maximize=True
        )
        candidate_scores: list[dict] = []

        for action in ordered_mine:
            worst = self._minimize_over_opponent(state, action, opp_legal, alpha, beta, self.depth)
            candidate_scores.append(
                self._candidate_details(state, player_index, action, worst)
            )
            if worst > best_val:
                best_val = worst
                best_action = action
            alpha = max(alpha, best_val)
            if alpha >= beta:
                self._pruned += 1
                break

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
            "candidate_scores": candidate_scores,
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
        ordered_opp = self._select_search_actions(
            state, opp_legal, 1 - self._player_index, maximize=True
        )

        worst = _INF
        inner_beta = beta

        for opp_action in ordered_opp:
            new_state = self._simulate(state, my_action, opp_action)
            val = self._search(new_state, depth - 1, alpha, inner_beta)

            if val < worst:
                worst = val
            inner_beta = min(inner_beta, worst)
            if worst <= alpha:
                self._pruned += 1
                break

        return worst

    def _search(
        self, state: BattleState, depth: int, alpha: float, beta: float
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

        ordered_mine = self._select_search_actions(
            state, my_legal, self._player_index, maximize=True
        )

        best = -_INF
        for my_action in ordered_mine:
            worst = self._minimize_over_opponent(state, my_action, opp_legal, alpha, beta, depth)
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
    ) -> list[BattleAction]:
        """Ordena acciones por valor heurístico estimado.

        Explorar primero las ramas más prometedoras maximiza los cortes alfa-beta.
        """
        scored: list[tuple[float, BattleAction]] = []
        for action in actions:
            score = self._quick_score(state, acting_player, action)
            if self._is_repeated_opponent_action(state, acting_player, action):
                score += 0.25
            scored.append((score, action))

        scored.sort(key=lambda x: x[0], reverse=maximize)
        return [a for _, a in scored]

    def _select_search_actions(
        self,
        state: BattleState,
        actions: list[BattleAction],
        acting_player: int,
        maximize: bool,
    ) -> list[BattleAction]:
        """Aplica top-K sin excluir acciones tacticamente criticas."""
        ordered = self._rank_actions(state, actions, acting_player, maximize=maximize)
        critical = self._critical_actions(state, actions, acting_player)

        selected: list[BattleAction] = []
        for action in critical + ordered[: self.top_k_actions]:
            if action not in selected:
                selected.append(action)
        return selected

    def _critical_actions(
        self,
        state: BattleState,
        actions: list[BattleAction],
        acting_player: int,
    ) -> list[BattleAction]:
        """Devuelve KOs inmediatos y switches defensivos que no deben podarse."""
        my_team = state.team_of(acting_player)
        opp_team = state.opponent_of(acting_player)
        attacker = my_team.active_pokemon
        defender = opp_team.active_pokemon
        active_at_risk = self._active_can_be_koed(state, acting_player)

        knockout_actions: list[BattleAction] = []
        tempo_attacks: list[BattleAction] = []
        defensive_switches: list[BattleAction] = []
        fallback_switches: list[BattleAction] = []
        best_tempo_damage = 0.0

        for action in actions:
            if action.action_type == "move" and 0 <= action.index < len(attacker.moves):
                move = attacker.moves[action.index]
                if not move.has_pp():
                    continue
                expected_damage = self._expected_damage(attacker, defender, move)
                if (
                    expected_damage >= defender.hp
                ):
                    knockout_actions.append(action)
                if active_at_risk and expected_damage > best_tempo_damage:
                    best_tempo_damage = expected_damage
                    tempo_attacks = [action]
            elif action.action_type == "switch" and active_at_risk:
                if self._switch_survives_best_hit(state, acting_player, action):
                    fallback_switches.append(action)
                if self._switch_reduces_expected_damage(state, acting_player, action):
                    defensive_switches.append(action)

        critical = knockout_actions + tempo_attacks + (defensive_switches or fallback_switches)
        selected: list[BattleAction] = []
        for action in critical:
            if action not in selected:
                selected.append(action)
        return selected

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
            # Daño esperado normalizado por HP del defensor
            expected_dmg = self._expected_damage(attacker, defender, move)
            return expected_dmg / max(1, defender.max_hp)

        if action.action_type == "switch":
            return self._score_switch(action, my_team, opp_team)

        if action.action_type == "struggle":
            return 0.01

        return 0.0

    def _score_switch(self, action: BattleAction, my_team, opp_team) -> float:
        """Evalúa la calidad de un cambio considerando ventaja de tipo.

        Penaliza explicitamente cambios que entran al mejor golpe esperado del rival,
        porque cambiar consume el turno ofensivo y puede regalar material.
        """
        if action.index < 0 or action.index >= len(my_team.pokemons):
            return 0.0

        incoming = my_team.pokemons[action.index]
        current = my_team.active_pokemon
        opp_active = opp_team.active_pokemon

        # Ventaja de tipo: mejor multiplicador de los movimientos del entrante
        # Normalizado por 4.0 (máximo posible con tipos duales) en vez de 2.0
        best_mult_incoming = max(
            (get_type_multiplier(m.move_type, opp_active.pokemon_type)
             for m in incoming.moves if m.has_pp()),
            default=1.0,
        )
        type_advantage = min(best_mult_incoming / 4.0, 1.0)

        # HP del entrante normalizado
        hp_ratio = incoming.hp / max(1, incoming.max_hp)

        # Vulnerabilidad del entrante ante el rival
        # Normalizado por 4.0: una debilidad 4× queda en 1.0 → vulnerability_score = 0.0
        best_mult_opp_vs_incoming = max(
            (get_type_multiplier(m.move_type, incoming.pokemon_type)
             for m in opp_active.moves if m.has_pp()),
            default=1.0,
        )
        vulnerability = min(best_mult_opp_vs_incoming / 4.0, 1.0)
        vulnerability_score = 1.0 - vulnerability

        incoming_damage = self._max_expected_damage(opp_active, incoming)
        current_damage = self._max_expected_damage(opp_active, current)
        active_damage = self._max_expected_damage(current, opp_active)

        remaining_hp = incoming.hp - incoming_damage
        survival_score = max(0.0, remaining_hp) / max(1, incoming.max_hp)
        tempo_penalty = active_damage / max(1, opp_active.max_hp) * 0.25
        bad_switch_penalty = self._bad_switch_penalty(
            incoming=incoming,
            incoming_damage=incoming_damage,
            current_damage=current_damage,
        )

        return (
            0.25 * type_advantage
            + 0.20 * hp_ratio
            + 0.30 * vulnerability_score
            + 0.25 * survival_score
            - tempo_penalty
            - bad_switch_penalty
        )

    def _candidate_details(
        self,
        state: BattleState,
        player_index: int,
        action: BattleAction,
        value: float,
    ) -> dict:
        details = {
            "action": action.label,
            "type": action.action_type,
            "value": round(value, 4),
            "quick_score": round(self._quick_score(state, player_index, action), 4),
        }
        if action.action_type == "switch":
            details.update(self._switch_risk_details(state, player_index, action))
        return details

    def _switch_risk_details(
        self,
        state: BattleState,
        acting_player: int,
        action: BattleAction,
    ) -> dict:
        my_team = state.team_of(acting_player)
        if action.index < 0 or action.index >= len(my_team.pokemons):
            return {}

        incoming = my_team.pokemons[action.index]
        opp_active = state.opponent_of(acting_player).active_pokemon
        expected_damage = self._max_expected_damage(opp_active, incoming)
        expected_hp = max(0.0, incoming.hp - expected_damage)
        return {
            "incoming": incoming.name,
            "expected_damage_taken": round(expected_damage, 2),
            "expected_hp_after_switch": round(expected_hp, 2),
            "lethal_switch": expected_damage >= incoming.hp,
        }

    def _bad_switch_penalty(
        self,
        incoming: BattlePokemon,
        incoming_damage: float,
        current_damage: float,
    ) -> float:
        """Castiga switches que pierden material o empeoran el daño recibido."""
        penalty = 0.0
        remaining_hp = incoming.hp - incoming_damage

        if remaining_hp <= 0:
            penalty += 1.25
        elif remaining_hp / max(1, incoming.max_hp) <= 0.25:
            penalty += 0.4

        if incoming_damage > current_damage:
            penalty += 0.2

        return penalty

    def _expected_damage(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move: BattleMove,
    ) -> float:
        """Daño esperado usado por ordenamiento y detección de acciones críticas."""
        return calculate_damage(attacker, defender, move) * move.accuracy

    def _max_expected_damage(self, attacker: BattlePokemon, defender: BattlePokemon) -> float:
        return max(
            (
                self._expected_damage(attacker, defender, move)
                for move in attacker.moves
                if move.has_pp()
            ),
            default=0.0,
        )

    def _active_can_be_koed(self, state: BattleState, acting_player: int) -> bool:
        my_active = state.team_of(acting_player).active_pokemon
        opp_active = state.opponent_of(acting_player).active_pokemon
        return self._max_expected_damage(opp_active, my_active) >= my_active.hp

    def _switch_reduces_expected_damage(
        self,
        state: BattleState,
        acting_player: int,
        action: BattleAction,
    ) -> bool:
        my_team = state.team_of(acting_player)
        opp_active = state.opponent_of(acting_player).active_pokemon
        if action.index < 0 or action.index >= len(my_team.pokemons):
            return False

        current = my_team.active_pokemon
        incoming = my_team.pokemons[action.index]
        if incoming.is_fainted() or incoming is current:
            return False

        current_damage = self._max_expected_damage(opp_active, current)
        incoming_damage = self._max_expected_damage(opp_active, incoming)
        return incoming_damage < current_damage and incoming_damage < incoming.hp

    def _switch_survives_best_hit(
        self,
        state: BattleState,
        acting_player: int,
        action: BattleAction,
    ) -> bool:
        my_team = state.team_of(acting_player)
        if action.index < 0 or action.index >= len(my_team.pokemons):
            return False

        incoming = my_team.pokemons[action.index]
        opp_active = state.opponent_of(acting_player).active_pokemon
        if incoming.is_fainted() or incoming is my_team.active_pokemon:
            return False
        return self._max_expected_damage(opp_active, incoming) < incoming.hp

    def _is_repeated_opponent_action(
        self,
        state: BattleState,
        acting_player: int,
        action: BattleAction,
    ) -> bool:
        if acting_player == self._player_index:
            return False
        if action.action_type != "move":
            return False

        last_actions = getattr(state, "last_actions", [None, None])
        last_action = last_actions[acting_player]
        if last_action is None:
            return False
        return last_action.action_type == action.action_type and last_action.index == action.index

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _simulate(
        self,
        state: BattleState,
        my_action: BattleAction,
        opp_action: BattleAction,
    ) -> BattleState:
        """Envuelve simulate_turn asignando acciones según player_index."""
        if self._player_index == 0:
            return simulate_turn(
                state,
                my_action,
                opp_action,
                self._sim_rng,
                deterministic=True,
                forced_switch_selector=self._select_forced_switch,
            )
        return simulate_turn(
            state,
            opp_action,
            my_action,
            self._sim_rng,
            deterministic=True,
            forced_switch_selector=self._select_forced_switch,
        )

    def _select_forced_switch(self, state: BattleState, player_index: int) -> int | None:
        """Elige reemplazos forzados desde la perspectiva del Minimax actual."""
        team = state.team_of(player_index)
        switches = team.available_switches()
        if not switches:
            return None

        best_index: int | None = None
        best_value = -_INF if player_index == self._player_index else _INF

        for switch_index, _ in switches:
            trial = state.clone()
            trial.team_of(player_index).active_index = switch_index
            value = evaluate_state(trial, self._player_index, self.weights)

            if player_index == self._player_index:
                if value > best_value:
                    best_value = value
                    best_index = switch_index
            elif value < best_value:
                best_value = value
                best_index = switch_index

        return best_index

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
        for action in getattr(state, "last_actions", [None, None]):
            if action is None:
                parts.extend((-1, -1))
            else:
                action_type_id = {"move": 0, "switch": 1, "struggle": 2, "pass": 3}.get(
                    action.action_type,
                    9,
                )
                parts.extend((action_type_id, action.index))
        return hash(tuple(parts))
