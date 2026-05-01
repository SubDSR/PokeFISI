from __future__ import annotations

import random

from backend.agents.base import BaseAgent
from backend.battle.models import BattleAction
from backend.battle.state import BattleState


class RandomAgent(BaseAgent):
    def __init__(self, name: str = "RandomAgent", rng: random.Random | None = None):
        super().__init__(name)
        self.rng = rng or random.Random()

    def choose_action(
        self,
        state: BattleState,
        player_index: int,
        legal_actions: list[BattleAction],
    ) -> BattleAction:
        return self.rng.choice(legal_actions)
