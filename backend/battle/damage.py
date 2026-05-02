"""Damage model for the simplified academic battle simulator."""

from backend.battle.models import BattleMove, BattlePokemon


def calculate_damage(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    move: BattleMove,
) -> int:
    raw_damage = (attacker.attack / max(1, defender.defense)) * move.base_power
    return max(1, int(round(raw_damage)))
