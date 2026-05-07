from backend.agents.base import BaseAgent
from backend.battle.models import BattleAction
from backend.battle.state import BattleState


class HumanAgent(BaseAgent):
    def __init__(self, name: str = "Humano"):
        super().__init__(name)

    def choose_action(self, state: BattleState, player_index: int, legal_actions: list[BattleAction]) -> BattleAction:
        print("\n[INPUT] Tu turno")
        for i, action in enumerate(legal_actions):
            print(f"  {i + 1}. {action.label}")

        while True:
            try:
                raw = input(f"[INPUT] Elige una accion (1-{len(legal_actions)}): ").strip()
                index = int(raw) - 1
                if 0 <= index < len(legal_actions):
                    return legal_actions[index]
                print(f"[ERROR] Numero fuera de rango. Elige entre 1 y {len(legal_actions)}.")
            except ValueError:
                print("[ERROR] Entrada invalida. Ingresa un numero.")
            except EOFError:
                return legal_actions[0]
