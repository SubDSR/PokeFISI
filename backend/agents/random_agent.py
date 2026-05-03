from __future__ import annotations

import random

from backend.agents.base import BaseAgent
from backend.battle.models import BattleAction
from backend.battle.state import BattleState


class RandomAgent(BaseAgent):
    def __init__(self, name: str = "RandomAgent", rng: random.Random | None = None):
        super().__init__(name)
        self.rng = rng or random.Random()
        self.last_choice_details: dict | None = None

    def choose_action(
        self,
        state: BattleState,
        player_index: int,
        legal_actions: list[BattleAction],
    ) -> BattleAction:
        choice_index = self.rng.randrange(len(legal_actions))
        chosen_action = legal_actions[choice_index]
        self.last_choice_details = {
            "strategy": "random",
            "choice_index": choice_index,
            "options_count": len(legal_actions),
            "chosen_label": chosen_action.label,
            "player_index": player_index,
        }
        return chosen_action
