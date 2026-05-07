"""Damage model for the simplified academic battle simulator.

Formula (Dr. Sobrevilla):
    Damage = (Attack / Defense_op) * BasePower - Speed_op * K
"""

from backend.battle.models import BattleMove, BattlePokemon

K = 0.5  # adjustment factor: defender speed reduces damage taken


def calculate_damage(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    move: BattleMove,
) -> int:
    raw_damage = (attacker.attack / max(1, defender.defense)) * move.base_power - defender.speed * K
    return max(1, int(round(raw_damage)))
