"""Tests for battle stat calculations."""

import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from backend.battle.factory import build_battle_pokemon
from backend.battle.stats import calculate_hp
from backend.data import POKEDEX


class TestCalculateHp:
    @pytest.mark.parametrize(
        ("base", "expected"),
        [
            (45, 120),
            (39, 114),
            (44, 119),
            (35, 110),
            (70, 145),
            (90, 165),
        ],
    )
    def test_default_project_values(self, base: int, expected: int):
        assert calculate_hp(base) == expected

    def test_formula_accepts_custom_values(self):
        assert calculate_hp(base=45, iv=31, ev=252, level=50) == 152

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"base": 0}, "base HP"),
            ({"base": 45, "iv": 32}, "IV"),
            ({"base": 45, "ev": -1}, "EV"),
            ({"base": 45, "level": 0}, "level"),
        ],
    )
    def test_rejects_invalid_values(self, kwargs: dict, message: str):
        with pytest.raises(ValueError, match=message):
            calculate_hp(**kwargs)


class TestBattlePokemonHp:
    def test_factory_uses_calculated_hp(self):
        rng = random.Random(7)
        pokemon = build_battle_pokemon("bulbasaur", rng)

        assert pokemon.max_hp == 120
        assert pokemon.hp == pokemon.max_hp

    def test_factory_uses_species_base_hp_as_base_stat(self):
        rng = random.Random(7)
        species = POKEDEX["machop"]
        pokemon = build_battle_pokemon("machop", rng)

        assert pokemon.max_hp == calculate_hp(species.hp, level=species.level)
        assert pokemon.max_hp != species.hp
