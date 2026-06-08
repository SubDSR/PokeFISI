"""Stat calculations for runtime battle Pokemon."""

DEFAULT_IV = 31
DEFAULT_EV = 0
DEFAULT_LEVEL = 50


def calculate_hp(
    base: int,
    iv: int = DEFAULT_IV,
    ev: int = DEFAULT_EV,
    level: int = DEFAULT_LEVEL,
) -> int:
    """Calculate final HP using the standard Pokemon HP formula.

    Formula:
        floor((((2 * Base + IV + floor(EV / 4)) * Level) / 100))
        + Level + 10

    PokeFISI currently uses IV=31, EV=0 and level=50, but the full formula
    is kept parameterized so future stat customization does not require a
    rewrite.
    """
    if base < 1:
        raise ValueError("base HP must be positive")
    if not 0 <= iv <= 31:
        raise ValueError("IV must be between 0 and 31")
    if ev < 0:
        raise ValueError("EV must be non-negative")
    if level < 1:
        raise ValueError("level must be positive")

    return ((2 * base + iv + (ev // 4)) * level) // 100 + level + 10
