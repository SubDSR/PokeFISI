"""Nivel 3 - Agente Minimax con poda Alfa-Beta y optimizaciones.

Optimizaciones implementadas:
  A) Poda alfa-beta canónica.
  B) Ordenamiento heurístico de acciones (inspirado en A*).
  C) Early cutoffs en estados terminales.
  D) Tabla de transposición (memoización).
  E) Control de branching factor (top-K acciones).

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
from backend.battle.simulator import simulate_turn
from backend.battle.state import BattleState
from backend.data.types import get_type_multiplier

_INF = float("inf")


class MinimaxAgent(BaseAgent):
    """Agente adversarial Minimax con poda alfa-beta."""

    def __init__(
        self,
        name: str = "MinimaxAgent",
        depth: int = 2,
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
        # RNG para la simulación interna (reproducible)
        self._sim_rng = rng or random.Random(42)

        # Contadores de telemetría (reseteados por choose_action)
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

        ordered_mine = self._rank_actions(state, legal_actions, player_index, maximize=True)
        ordered_mine = ordered_mine[: self.top_k_actions]

        for action in ordered_mine:
            # Peor respuesta del oponente a esta acción propia
            worst = self._minimize_over_opponent(state, action, opp_legal, alpha, beta, self.depth)
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
        """Para una acción propia fija, devuelve el valor mínimo que puede lograr el oponente."""
        ordered_opp = self._rank_actions(
            state, opp_legal, 1 - self._player_index, maximize=False
        )
        ordered_opp = ordered_opp[: self.top_k_actions]

        worst = _INF
        inner_beta = beta

        for opp_action in ordered_opp:
            new_state = self._simulate(state, my_action, opp_action)
            val = self._search(new_state, depth - 1, alpha, inner_beta)

            if val < worst:
                worst = val
            inner_beta = min(inner_beta, worst)
            if worst <= alpha:  # Alpha cutoff
                self._pruned += 1
                break

        return worst

    def _search(
        self, state: BattleState, depth: int, alpha: float, beta: float
    ) -> float:
        """Minimax recursivo con poda alfa-beta desde la perspectiva del jugador."""
        self._nodes += 1

        # Transposition table lookup
        if self.enable_transposition_table:
            h = self._hash_state(state)
            cached = self._tt.get(h)
            if cached is not None and cached[0] >= depth:
                self._tt_hits += 1
                return cached[1]

        # Estado terminal o hoja
        if state.battle_over():
            return self._terminal_value(state)

        if depth == 0:
            val = evaluate_state(state, self._player_index, self.weights)
            return val

        my_legal = state.get_legal_actions(self._player_index)
        opp_legal = state.get_legal_actions(1 - self._player_index)

        if not my_legal or not opp_legal:
            return evaluate_state(state, self._player_index, self.weights)

        ordered_mine = self._rank_actions(state, my_legal, self._player_index, maximize=True)
        ordered_mine = ordered_mine[: self.top_k_actions]

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
    # Ordenamiento heurístico (move ordering)
    # ──────────────────────────────────────────

    def _rank_actions(
        self,
        state: BattleState,
        actions: list[BattleAction],
        acting_player: int,
        maximize: bool,
    ) -> list[BattleAction]:
        """Ordena acciones por valor heurístico estimado (inspirado en A*).

        Explorar primero las ramas más prometedoras maximiza los cortes alfa-beta.
        """
        scored: list[tuple[float, BattleAction]] = []
        for action in actions:
            score = self._quick_score(state, acting_player, action)
            scored.append((score, action))

        scored.sort(key=lambda x: x[0], reverse=maximize)
        return [a for _, a in scored]

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
            # Daño esperado normalizado por HP del defensor
            expected_dmg = calculate_damage(attacker, defender, move) * move.accuracy * type_mod
            return expected_dmg / max(1, defender.max_hp)

        if action.action_type == "switch":
            if action.index < 0 or action.index >= len(my_team.pokemons):
                return 0.0
            switch_in = my_team.pokemons[action.index]
            return switch_in.hp_ratio  # preferir Pokémon con más HP

        if action.action_type == "struggle":
            return 0.01  # Struggle es un último recurso

        return 0.0

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
            return simulate_turn(state, my_action, opp_action, self._sim_rng)
        return simulate_turn(state, opp_action, my_action, self._sim_rng)

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
