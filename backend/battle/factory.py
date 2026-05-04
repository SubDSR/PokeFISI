"""Factory helpers to instantiate runtime battle objects from static data."""

from __future__ import annotations

import random

from backend.battle.models import BattleMove, BattlePokemon, TeamState
from backend.data import MOVEDEX, POKEDEX


def build_battle_pokemon(species_id: str, rng: random.Random) -> BattlePokemon:
    species = POKEDEX[species_id]
    selected_move_ids = rng.sample(species.move_ids, 4)
    moves = [
        BattleMove(
            id=MOVEDEX[move_id].id,
            name=MOVEDEX[move_id].name,
            base_power=MOVEDEX[move_id].base_power,
            accuracy=MOVEDEX[move_id].accuracy,
            move_type=MOVEDEX[move_id].move_type,
            description=MOVEDEX[move_id].description,
        )
        for move_id in selected_move_ids
    ]
    return BattlePokemon(
        species_id=species.id,
        name=species.name,
        level=species.level,
        max_hp=species.hp,
        hp=species.hp,
        attack=species.attack,
        defense=species.defense,
        speed=species.speed,
        moves=moves,
        sprite_front_url=species.sprite_front_url,
        sprite_back_url=species.sprite_back_url,
    )


def build_team_from_species(trainer_name: str, species_ids: list[str], rng: random.Random) -> TeamState:
    pokemons = [build_battle_pokemon(species_id, rng) for species_id in species_ids]
    return TeamState(trainer_name=trainer_name, pokemons=pokemons)


def build_random_team(
    trainer_name: str,
    team_size: int,
    rng: random.Random,
    species_pool: list[str] | None = None,
) -> TeamState:
    if team_size not in (3, 4):
        raise ValueError("El tamano del equipo debe ser 3 o 4.")

    available_species = species_pool or list(POKEDEX.keys())
    if len(available_species) < team_size:
        raise ValueError("No hay suficientes especies para construir el equipo.")

    selected_species = rng.sample(available_species, team_size)
    return build_team_from_species(trainer_name, selected_species, rng)
