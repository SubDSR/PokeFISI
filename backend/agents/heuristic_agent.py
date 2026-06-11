"""Nivel 2 - Agente Heurístico (greedy depth-1).

Evalúa cada acción legal simulando el daño esperado y elige la que
maximiza h(n) = HP_total_propio - HP_total_rival.

Mejoras respecto a la versión anterior:
  - Los movimientos de tipo SWITCH ahora son evaluados correctamente.
    Antes, cambiar de Pokémon recibía score = 0 (neutro), lo que hacía
    que el agente NUNCA cambiara voluntariamente incluso estando en gran
    desventaja de tipo. Ahora el score del switch incluye:
      1. Ventaja de tipo del Pokémon entrante vs el activo rival.
      2. Penalización por vulnerabilidad de tipo del Pokémon actual.
      3. Bonus por HP ratio del Pokémon entrante.
    Esto permite que el agente cambie cuando está en desventaja real.
"""

from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.battle.damage import calculate_damage
from backend.battle.models import BattleAction
from backend.battle.state import BattleState
from backend.data.types import get_type_multiplier


class HeuristicAgent(BaseAgent):
    def __init__(self, name: str = "HeuristicAgent"):
        super().__init__(name)
        self.last_choice_details: dict | None = None

    def choose_action(
        self,
        state: BattleState,
        player_index: int,
        legal_actions: list[BattleAction],
    ) -> BattleAction:
        best_action = legal_actions[0]
        best_score = float("-inf")

        my_team = state.team_of(player_index)
        opp_team = state.opponent_of(player_index)

        for action in legal_actions:
            score = self._evaluate(action, my_team, opp_team)
            if score > best_score:
                best_score = score
                best_action = action

        self.last_choice_details = {
            "strategy": "heuristic",
            "chosen_label": best_action.label,
            "score": round(best_score, 2),
            "player_index": player_index,
        }
        return best_action

    def _evaluate(self, action: BattleAction, my_team, opp_team) -> float:
        my_hp = sum(p.hp for p in my_team.pokemons)
        opp_hp = sum(p.hp for p in opp_team.pokemons)

        if action.action_type == "move":
            attacker = my_team.active_pokemon
            defender = opp_team.active_pokemon
            move = attacker.moves[action.index]
            # Daño esperado = daño_si_impacta × probabilidad_de_impacto
            expected_damage = calculate_damage(attacker, defender, move) * move.accuracy
            opp_hp = max(0, opp_hp - expected_damage)
            # h(n) = HP_total_propio - HP_total_rival
            return my_hp - opp_hp

        if action.action_type == "switch":
            return self._evaluate_switch(action, my_team, opp_team, my_hp, opp_hp)

        # struggle u otros: neutro
        return my_hp - opp_hp

    def _evaluate_switch(
        self, action: BattleAction, my_team, opp_team, my_hp: float, opp_hp: float
    ) -> float:
        """Evalúa el beneficio de cambiar al Pokémon en action.index.

        Componentes del score:
          A) type_gain: ventaja de tipo del Pokémon entrante vs el rival activo.
             Toma el mejor multiplicador entre los movimientos del entrante.
          B) current_vulnerability: cuán vulnerable es el Pokémon actual al rival.
             Si el rival tiene 2x contra el activo → penalización fuerte.
          C) hp_bonus: HP normalizado del Pokémon entrante (preferir más HP).

        El score final se suma al balance de HP para que sea comparable
        con el score de los movimientos.
        """
        if action.index < 0 or action.index >= len(my_team.pokemons):
            return my_hp - opp_hp

        incoming = my_team.pokemons[action.index]
        current = my_team.active_pokemon
        opp_active = opp_team.active_pokemon

        # A) Ventaja de tipo del entrante (mejor multiplicador de sus movimientos)
        best_mult_incoming = max(
            (get_type_multiplier(m.move_type, opp_active.pokemon_type)
             for m in incoming.moves if m.has_pp()),
            default=1.0,
        )

        # B) Vulnerabilidad del Pokémon actual frente al rival
        best_mult_opp_vs_current = max(
            (get_type_multiplier(m.move_type, current.pokemon_type)
             for m in opp_active.moves if m.has_pp()),
            default=1.0,
        )
        best_mult_opp_vs_incoming = max(
            (get_type_multiplier(m.move_type, incoming.pokemon_type)
             for m in opp_active.moves if m.has_pp()),
            default=1.0,
        )

        # Ganancia neta de tipo al hacer el cambio
        type_gain = (best_mult_incoming - 1.0) * 30.0

        # Reducción de vulnerabilidad
        vulnerability_reduction = (best_mult_opp_vs_current - best_mult_opp_vs_incoming) * 20.0

        # C) Bonus por HP del entrante (normalizado a escala similar)
        hp_bonus = (incoming.hp / max(1, incoming.max_hp)) * 10.0

        base_score = my_hp - opp_hp
        return base_score + type_gain + vulnerability_reduction + hp_bonus
