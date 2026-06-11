"""Factory helpers to instantiate runtime battle objects from static data."""

from __future__ import annotations

import random

from backend.battle.models import BattleMove, BattlePokemon, TeamState
from backend.battle.stats import calculate_hp
from backend.data import MOVEDEX, POKEDEX
from backend.data.types import get_type_multiplier, parse_types


# ─── Clasificación por Tier de potencia (BST = HP + ATK + DEF + SPD) ─────────
#
# TIER A (≥225): Pokémon más fuertes — Mankey, Growlithe, Machop, Slowpoke,
#                Doduo, Geodude, Pidgeotto, Sandshrew, Ponyta
# TIER B (195-224): Potencia media — Charmander, Squirtle, Bellsprout, Spearow,
#                   Psyduck, Meowth, Seel, Venonat, Pikachu, Poliwag
# TIER C (<195):  Más débiles — Abra, Magnemite, Oddish, Vulpix, Paras,
#                 Tentacool, Bulbasaur, Nidoran M/F, Rattata, Ekans
#
# Equipo de 3: 1 de cada tier → diferencia máxima de BST ≈ 60 pts entre equipos.
# Equipo de 4: 1 Tier A + 2 Tier B + 1 Tier C.

def _bst(species_id: str) -> int:
    p = POKEDEX[species_id]
    return p.hp + p.attack + p.defense + p.speed


def _primary_type(species_id: str) -> str:
    return POKEDEX[species_id].pokemon_type.split("/")[0]


_ALL_SPECIES: list[str] = list(POKEDEX.keys())

TIER_A: list[str] = [pid for pid in _ALL_SPECIES if _bst(pid) >= 225]
TIER_B: list[str] = [pid for pid in _ALL_SPECIES if 195 <= _bst(pid) < 225]
TIER_C: list[str] = [pid for pid in _ALL_SPECIES if _bst(pid) < 195]

_ATTACK_TYPES: list[str] = [
    "normal", "fire", "water", "electric", "grass", "ice", "fighting",
    "poison", "ground", "flying", "psychic", "bug", "rock", "ghost",
    "dark", "steel", "dragon",
]


# ─── Validadores de equipo ────────────────────────────────────────────────────

def _unique_primary_types(team_ids: list[str]) -> bool:
    """Regla 2: todos los Pokémon del equipo tienen tipo primario distinto."""
    types = [_primary_type(pid) for pid in team_ids]
    return len(set(types)) == len(types)


def _has_shared_weakness(team_ids: list[str]) -> bool:
    """Regla 3: devuelve True si 2+ Pokémon son débiles (≥2×) al mismo tipo."""
    for attack_type in _ATTACK_TYPES:
        vulnerable = sum(
            1 for pid in team_ids
            if get_type_multiplier(attack_type, POKEDEX[pid].pokemon_type) >= 2.0
        )
        if vulnerable >= 2:
            return True
    return False


# ─── Construcción de un Pokémon de batalla ────────────────────────────────────

def build_battle_pokemon(species_id: str, rng: random.Random) -> BattlePokemon:
    """Regla 4: garantiza al menos 1 movimiento STAB en los 4 seleccionados."""
    species = POKEDEX[species_id]
    pokemon_types = parse_types(species.pokemon_type)

    stab_ids = [mid for mid in species.move_ids if MOVEDEX[mid].move_type in pokemon_types]
    other_ids = [mid for mid in species.move_ids if MOVEDEX[mid].move_type not in pokemon_types]

    selected: list[str] = []
    if stab_ids:
        selected.append(rng.choice(stab_ids))

    pool = [m for m in stab_ids if m not in selected] + other_ids
    rng.shuffle(pool)
    selected.extend(pool[: 4 - len(selected)])

    moves = [
        BattleMove(
            id=MOVEDEX[mid].id,
            name=MOVEDEX[mid].name,
            base_power=MOVEDEX[mid].base_power,
            accuracy=MOVEDEX[mid].accuracy,
            move_type=MOVEDEX[mid].move_type,
            description=MOVEDEX[mid].description,
            max_pp=MOVEDEX[mid].pp,
            pp=MOVEDEX[mid].pp,
        )
        for mid in selected
    ]

    calculated_hp = calculate_hp(species.hp, level=species.level)

    return BattlePokemon(
        species_id=species.id,
        name=species.name,
        level=species.level,
        max_hp=calculated_hp,
        hp=calculated_hp,
        attack=species.attack,
        defense=species.defense,
        speed=species.speed,
        pokemon_type=species.pokemon_type,
        moves=moves,
        sprite_front_url=species.sprite_front_url,
        sprite_back_url=species.sprite_back_url,
    )


def build_team_from_species(
    trainer_name: str, species_ids: list[str], rng: random.Random
) -> TeamState:
    pokemons = [build_battle_pokemon(species_id, rng) for species_id in species_ids]
    return TeamState(trainer_name=trainer_name, pokemons=pokemons)


# ─── Selección de especies balanceadas ────────────────────────────────────────

def _select_species(
    pools: list[list[str]],
    picks_per_pool: list[int],
    rng: random.Random,
) -> list[str] | None:
    """
    Intenta seleccionar Pokémon de los pools dado el número de picks por pool.
    Aplica Regla 2 (tipos únicos) y Regla 3 (sin debilidad compartida).
    Retorna lista de IDs o None si no encontró combinación válida en 100 intentos.
    """
    for _ in range(100):
        candidates: list[str] = []
        for pool, n in zip(pools, picks_per_pool):
            if n == 1:
                candidates.append(rng.choice(pool))
            else:
                candidates.extend(rng.sample(pool, n))

        if _unique_primary_types(candidates) and not _has_shared_weakness(candidates):
            return candidates
    return None


def _select_species_relaxed(
    pools: list[list[str]],
    picks_per_pool: list[int],
    rng: random.Random,
) -> list[str]:
    """
    Igual que _select_species pero sin Regla 3 (solo Regla 2).
    Fallback cuando la combinación de Reglas 2+3 es imposible.
    """
    for _ in range(100):
        candidates: list[str] = []
        for pool, n in zip(pools, picks_per_pool):
            if n == 1:
                candidates.append(rng.choice(pool))
            else:
                candidates.extend(rng.sample(pool, n))

        if _unique_primary_types(candidates):
            return candidates

    # Último recurso: solo Regla 1 (un Pokémon de cada tier)
    candidates = []
    for pool, n in zip(pools, picks_per_pool):
        if n == 1:
            candidates.append(rng.choice(pool))
        else:
            candidates.extend(rng.sample(pool, min(n, len(pool))))
    return candidates


# ─── API pública ──────────────────────────────────────────────────────────────

def build_random_team(
    trainer_name: str,
    team_size: int,
    rng: random.Random,
    species_pool: list[str] | None = None,
) -> TeamState:
    """Construye un equipo aleatorio con reglas de balance.

    Regla 1 — Un Pokémon de cada Tier (BST balanceado entre equipos).
    Regla 2 — Tipos primarios distintos dentro del equipo.
    Regla 3 — Sin debilidad compartida: ningún tipo golpea ≥2× a 2+ Pokémon.
    Regla 4 — Al menos 1 movimiento STAB garantizado por Pokémon.

    Degradación progresiva si los constraints no se pueden satisfacer:
      1° intento: Reglas 1+2+3   (100 tries)
      2° intento: Reglas 1+2     (100 tries)
      3° intento: Solo Regla 1   (1 try)
    """
    if team_size not in (3, 4):
        raise ValueError("El tamano del equipo debe ser 3 o 4.")

    available = species_pool or _ALL_SPECIES
    pool_a = [p for p in TIER_A if p in available]
    pool_b = [p for p in TIER_B if p in available]
    pool_c = [p for p in TIER_C if p in available]

    # Si algún tier está vacío, usar comportamiento original
    if not pool_a or not pool_b or not pool_c:
        selected = rng.sample(available, min(team_size, len(available)))
        return build_team_from_species(trainer_name, selected, rng)

    if team_size == 3:
        pools = [pool_a, pool_b, pool_c]
        picks = [1, 1, 1]
    else:
        pools = [pool_a, pool_b, pool_c]
        picks = [1, 2, 1]
        if len(pool_b) < 2:
            selected = rng.sample(available, 4)
            return build_team_from_species(trainer_name, selected, rng)

    species_ids = _select_species(pools, picks, rng)
    if species_ids is None:
        species_ids = _select_species_relaxed(pools, picks, rng)

    rng.shuffle(species_ids)  # aleatorizar quién lidera el equipo
    return build_team_from_species(trainer_name, species_ids, rng)


def _count_type_advantages(attacking: TeamState, defending: TeamState) -> int:
    """Pokémon del equipo atacante que tienen al menos un matchup ≥2× contra el defensor."""
    count = 0
    for attacker in attacking.pokemons:
        has_adv = any(
            get_type_multiplier(move.move_type, defender.pokemon_type) >= 2.0
            for move in attacker.moves
            for defender in defending.pokemons
        )
        if has_adv:
            count += 1
    return count


def build_balanced_teams(
    trainer1_name: str,
    trainer2_name: str,
    team_size: int,
    rng: random.Random,
    species_pool: list[str] | None = None,
) -> tuple[TeamState, TeamState]:
    """Construye dos equipos balanceados con balance cruzado de ventajas de tipo.

    Aplica las Reglas 1-4 a cada equipo y:
    - Regla 5: ningún Pokémon puede aparecer en ambos equipos simultáneamente.
    - Bonus:   verifica que la diferencia de ventajas de tipo entre equipos ≤ 2.
               Si supera, reconstruye el equipo menos favorecido (hasta 5 intentos).
    """
    available = species_pool or _ALL_SPECIES

    # Construir equipo 1
    team1 = build_random_team(trainer1_name, team_size, rng, available)

    # Regla 5: excluir las especies del equipo 1 del pool del equipo 2
    used = {p.species_id for p in team1.pokemons}
    pool_for_team2 = [s for s in available if s not in used]

    team2 = build_random_team(trainer2_name, team_size, rng, pool_for_team2)

    # Balance cruzado: reconstruir el equipo menos favorecido si la diferencia > 2
    for _ in range(5):
        adv1 = _count_type_advantages(team1, team2)
        adv2 = _count_type_advantages(team2, team1)
        if abs(adv1 - adv2) <= 2:
            break
        if adv1 < adv2:
            used2 = {p.species_id for p in team2.pokemons}
            team1 = build_random_team(trainer1_name, team_size, rng,
                                      [s for s in available if s not in used2])
        else:
            used1 = {p.species_id for p in team1.pokemons}
            team2 = build_random_team(trainer2_name, team_size, rng,
                                      [s for s in available if s not in used1])

    return team1, team2
