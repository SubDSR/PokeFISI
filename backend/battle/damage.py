"""Damage model for the simplified academic battle simulator."""

from backend.battle.models import BattleMove, BattlePokemon


def calculate_damage(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    move: BattleMove,
    speed_penalty_factor: float,
) -> int:
    raw_damage = (attacker.attack / max(1, defender.defense)) * move.base_power
    raw_damage -= defender.speed * speed_penalty_factor
    return max(1, int(round(raw_damage)))
