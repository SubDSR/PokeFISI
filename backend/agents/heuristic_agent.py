"""Nivel 2 - Agente Heurístico (greedy depth-1).

Evalúa cada acción legal simulando el daño esperado y elige la que
maximiza h(n) = HP_total_propio - HP_total_rival.
"""

from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.battle.damage import calculate_damage
from backend.battle.models import BattleAction
from backend.battle.state import BattleState


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
            # Daño esperado = daño_si_impacta * probabilidad_de_impacto
            expected_damage = calculate_damage(attacker, defender, move) * move.accuracy
            opp_hp = max(0, opp_hp - expected_damage)

        # h(n) = HP_total_propio - HP_total_rival
        return my_hp - opp_hp
