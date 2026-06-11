"""Tabla de efectividad elemental de tipos Pokémon (Gen 3).

Fuente oficial: https://play.pokemonshowdown.com/data/
Todas las entradas no-unitarias (≠ 1.0) del chart oficial Gen 3.

Correcciones respecto a la versión anterior:
  - Añadidas las entradas completas del tipo BUG (faltaban todas).
  - Añadidas entradas de DRAGON (faltaban todas).
  - Añadidas resistencias faltantes de FIRE, WATER, ELECTRIC, GRASS,
    ICE, FIGHTING, GROUND, FLYING, ROCK, GHOST vs BUG y DRAGON.
  - Añadida ghost vs steel = 0.5 (Steel resiste Ghost desde Gen 2+).
  - Añadida ground vs bug = 0.5.
"""

from __future__ import annotations

# (tipo_atacante, tipo_defensor) → multiplicador
# Solo se registran entradas no-unitarias (≠ 1.0)
_TYPE_CHART: dict[tuple[str, str], float] = {
    # ── NORMAL atacando ────────────────────────────────────────────────
    ("normal", "rock"):       0.5,
    ("normal", "steel"):      0.5,
    ("normal", "ghost"):      0.0,

    # ── FIRE atacando ──────────────────────────────────────────────────
    ("fire", "grass"):        2.0,
    ("fire", "ice"):          2.0,
    ("fire", "bug"):          2.0,   # AÑADIDO: faltaba en versión anterior
    ("fire", "steel"):        2.0,
    ("fire", "fire"):         0.5,
    ("fire", "water"):        0.5,
    ("fire", "rock"):         0.5,
    ("fire", "dragon"):       0.5,   # AÑADIDO

    # ── WATER atacando ─────────────────────────────────────────────────
    ("water", "fire"):        2.0,
    ("water", "ground"):      2.0,
    ("water", "rock"):        2.0,
    ("water", "water"):       0.5,
    ("water", "grass"):       0.5,
    ("water", "dragon"):      0.5,   # AÑADIDO

    # ── ELECTRIC atacando ──────────────────────────────────────────────
    ("electric", "water"):    2.0,
    ("electric", "flying"):   2.0,
    ("electric", "electric"): 0.5,
    ("electric", "grass"):    0.5,
    ("electric", "dragon"):   0.5,   # AÑADIDO
    ("electric", "ground"):   0.0,

    # ── GRASS atacando ─────────────────────────────────────────────────
    ("grass", "water"):       2.0,
    ("grass", "ground"):      2.0,
    ("grass", "rock"):        2.0,
    ("grass", "fire"):        0.5,
    ("grass", "grass"):       0.5,
    ("grass", "poison"):      0.5,
    ("grass", "flying"):      0.5,
    ("grass", "bug"):         0.5,   # AÑADIDO
    ("grass", "steel"):       0.5,
    ("grass", "dragon"):      0.5,   # AÑADIDO

    # ── ICE atacando ───────────────────────────────────────────────────
    ("ice", "grass"):         2.0,
    ("ice", "ground"):        2.0,
    ("ice", "flying"):        2.0,
    ("ice", "dragon"):        2.0,   # AÑADIDO
    ("ice", "water"):         0.5,
    ("ice", "ice"):           0.5,
    ("ice", "fire"):          0.5,
    ("ice", "steel"):         0.5,

    # ── FIGHTING atacando ──────────────────────────────────────────────
    ("fighting", "normal"):   2.0,
    ("fighting", "ice"):      2.0,
    ("fighting", "rock"):     2.0,
    ("fighting", "dark"):     2.0,
    ("fighting", "steel"):    2.0,
    ("fighting", "poison"):   0.5,
    ("fighting", "flying"):   0.5,
    ("fighting", "psychic"):  0.5,
    ("fighting", "bug"):      0.5,   # AÑADIDO
    ("fighting", "ghost"):    0.0,

    # ── POISON atacando ────────────────────────────────────────────────
    ("poison", "grass"):      2.0,
    ("poison", "poison"):     0.5,
    ("poison", "ground"):     0.5,
    ("poison", "rock"):       0.5,
    ("poison", "ghost"):      0.5,
    ("poison", "steel"):      0.0,

    # ── GROUND atacando ────────────────────────────────────────────────
    ("ground", "fire"):       2.0,
    ("ground", "electric"):   2.0,
    ("ground", "poison"):     2.0,
    ("ground", "rock"):       2.0,
    ("ground", "steel"):      2.0,
    ("ground", "grass"):      0.5,
    ("ground", "bug"):        0.5,   # AÑADIDO
    ("ground", "flying"):     0.0,

    # ── FLYING atacando ────────────────────────────────────────────────
    ("flying", "grass"):      2.0,
    ("flying", "fighting"):   2.0,
    ("flying", "bug"):        2.0,   # AÑADIDO
    ("flying", "rock"):       0.5,
    ("flying", "steel"):      0.5,
    ("flying", "electric"):   0.5,

    # ── PSYCHIC atacando ───────────────────────────────────────────────
    ("psychic", "fighting"):  2.0,
    ("psychic", "poison"):    2.0,
    ("psychic", "psychic"):   0.5,
    ("psychic", "steel"):     0.5,
    ("psychic", "dark"):      0.0,

    # ── BUG atacando ───────────────────────────────────────────────────
    # SECCIÓN COMPLETA AÑADIDA: faltaba enteramente en la versión anterior
    ("bug", "grass"):         2.0,
    ("bug", "psychic"):       2.0,
    ("bug", "dark"):          2.0,
    ("bug", "fire"):          0.5,
    ("bug", "fighting"):      0.5,
    ("bug", "flying"):        0.5,
    ("bug", "ghost"):         0.5,
    ("bug", "steel"):         0.5,
    ("bug", "poison"):        0.5,

    # ── ROCK atacando ──────────────────────────────────────────────────
    ("rock", "fire"):         2.0,
    ("rock", "ice"):          2.0,
    ("rock", "flying"):       2.0,
    ("rock", "bug"):          2.0,   # AÑADIDO
    ("rock", "fighting"):     0.5,
    ("rock", "ground"):       0.5,
    ("rock", "steel"):        0.5,

    # ── GHOST atacando ─────────────────────────────────────────────────
    ("ghost", "normal"):      0.0,
    ("ghost", "psychic"):     2.0,
    ("ghost", "ghost"):       2.0,
    ("ghost", "dark"):        0.5,
    ("ghost", "steel"):       0.5,   # AÑADIDO: steel resiste ghost desde Gen 2

    # ── DARK atacando ──────────────────────────────────────────────────
    ("dark", "psychic"):      2.0,
    ("dark", "ghost"):        2.0,
    ("dark", "dark"):         0.5,
    ("dark", "fighting"):     0.5,
    ("dark", "steel"):        0.5,

    # ── STEEL atacando ─────────────────────────────────────────────────
    ("steel", "ice"):         2.0,
    ("steel", "rock"):        2.0,
    ("steel", "steel"):       0.5,
    ("steel", "fire"):        0.5,
    ("steel", "water"):       0.5,
    ("steel", "electric"):    0.5,

    # ── DRAGON atacando ────────────────────────────────────────────────
    # SECCIÓN AÑADIDA: faltaba enteramente en la versión anterior
    ("dragon", "dragon"):     2.0,
    ("dragon", "steel"):      0.5,
}


def parse_types(pokemon_type: str) -> list[str]:
    """Convierte "grass/poison" → ["grass", "poison"]."""
    return [t.strip().lower() for t in pokemon_type.split("/") if t.strip()]


def get_type_multiplier(move_type: str, defender_pokemon_type: str) -> float:
    """Devuelve el multiplicador total para move_type contra defender_pokemon_type.

    Maneja tipos dobles: "grass/poison" aplica multiplicadores en cascada.
    Ejemplos:
      fire vs grass/poison  → 2.0 × 1.0 = 2.0
      bug  vs grass/poison  → 2.0 × 0.5 = 1.0  (grass-bug resistido por poison)
      electric vs ground    → 0.0
    """
    defending_types = parse_types(defender_pokemon_type)
    multiplier = 1.0
    for def_type in defending_types:
        multiplier *= _TYPE_CHART.get((move_type.lower(), def_type), 1.0)
    return multiplier
