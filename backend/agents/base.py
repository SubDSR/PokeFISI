from __future__ import annotations

from abc import ABC, abstractmethod

from backend.battle.models import BattleAction
from backend.battle.state import BattleState


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def choose_action(
        self,
        state: BattleState,
        player_index: int,
        legal_actions: list[BattleAction],
    ) -> BattleAction:
        raise NotImplementedError
