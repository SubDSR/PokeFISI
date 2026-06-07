import random

from backend.battle.factory import build_battle_pokemon, build_random_team
from backend.data import POKEDEX


def test_pokedex_has_60_species():
    assert len(POKEDEX) == 60


def test_random_team_generation_has_variety():
    rng = random.Random(123)
    teams = {
        tuple(sorted(p.species_id for p in build_random_team("A", 3, rng).pokemons))
        for _ in range(20)
    }
    assert len(teams) >= 8
