"""Modelo de daño para el simulador académico de combate.

Fórmula (Dr. Sobrevilla, extendida con modificador de tipo):
    Damage = Max(1, Int(Round(
        (Attack / Max(1, Defense_op)) × BasePower × TypeModifier − Speed_op × K
    )))
"""

from backend.battle.models import BattleMove, BattlePokemon
from backend.data.types import get_type_multiplier

K = 0.5  # factor de ajuste: velocidad del defensor reduce el daño recibido


def calculate_damage(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    move: BattleMove,
) -> int:
    """Calcula el daño del movimiento respetando efectividad de tipo.

    Returns:
        Daño entero positivo (mínimo 1).
    """
    type_mod = get_type_multiplier(move.move_type, defender.pokemon_type)
    raw = (
        (attacker.attack / max(1, defender.defense))
        * move.base_power
        * type_mod
        - defender.speed * K
    )
    return max(1, int(round(raw)))
