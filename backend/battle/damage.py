"""Modelo de daño para el simulador académico de combate.

Fórmula base (Dr. Sobrevilla):
    Damage = (Attack / Defense_op) × BasePower − Speed_op × K

Extendida con modificador de tipo y escala global:
    Damage = Max(1, Int(Round(
        ((Attack / Max(1, Defense_op)) × BasePower × TypeModifier − Speed_op × K)
        / DAMAGE_SCALE
    )))

Parámetros de calibración:
    K            = 0.1  -- La velocidad del defensor actúa como un pequeño
                          modificador de esquive. Con K=0.5 (valor original),
                          atacantes con ratio Atk/Def bajo producen daño ≈ 0
                          porque el término de velocidad los supera.
                          Con K=0.1 la velocidad sigue importando pero no domina.

    DAMAGE_SCALE = 2    -- Divide el resultado bruto a la mitad. Los HP en el
                          Pokédex están en rango 25-90; sin este divisor un
                          Machop (atk=80) vs Rattata (def=35) con Earthquake
                          produce 181 de daño de un solo golpe (OHKO).
                          Con DAMAGE_SCALE=2 ese mismo golpe hace ~90 daño y
                          Rattata (HP=360 escalado) sobrevive ~4 ataques.

Efecto sobre ventajas de tipo:
    - Matchup neutro (1.0x):    ~5-15 golpes para KO (batallas largas)
    - Super efectivo (2.0x):    ~3-7 golpes (incentivo real para cambiar)
    - No muy efectivo (0.5x):   ~10-30 golpes (defensor aguanta mucho)
    - Inmune (0.0x):            1 de daño mínimo (no mata de un golpe)

    Esto crea diferenciación táctica clara: si tu Charmander enfrenta
    a un Squirtle (fuego vs agua = 0.5x), tardarás 33 golpes en KO.
    Si cambias a Bulbasaur (planta vs agua = 2.0x), tardas solo 6.
"""

from backend.battle.models import BattleMove, BattlePokemon
from backend.data.types import get_type_multiplier

K = 0.1            # factor de ajuste: velocidad del defensor reduce ligeramente el daño
DAMAGE_SCALE = 2   # divisor global que normaliza el daño al rango de los HP escalados


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
    return max(1, int(round(raw / DAMAGE_SCALE)))
