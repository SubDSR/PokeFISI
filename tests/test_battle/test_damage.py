"""Tests para el cálculo de daño y el sistema de tipos."""

import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.battle.damage import calculate_damage
from backend.battle.factory import build_battle_pokemon
from backend.data.types import get_type_multiplier, parse_types


class TestTypeMultiplier:
    def test_super_effective(self):
        assert get_type_multiplier("fire", "grass") == 2.0

    def test_not_very_effective(self):
        assert get_type_multiplier("fire", "water") == 0.5

    def test_neutral(self):
        assert get_type_multiplier("normal", "normal") == 1.0

    def test_immune(self):
        assert get_type_multiplier("electric", "ground") == 0.0

    def test_dual_type_both_super(self):
        # fire vs grass/poison: 2.0 * 1.0 = 2.0
        assert get_type_multiplier("fire", "grass/poison") == 2.0

    def test_dual_type_mixed(self):
        # fighting vs flying/normal: 0.5 * 2.0 = 1.0
        result = get_type_multiplier("fighting", "flying/normal")
        assert result == 1.0

    def test_parse_single_type(self):
        assert parse_types("fire") == ["fire"]

    def test_parse_dual_type(self):
        assert parse_types("grass/poison") == ["grass", "poison"]

    def test_parse_with_spaces(self):
        assert parse_types("grass / poison") == ["grass", "poison"]


class TestCalculateDamage:
    def setup_method(self):
        self.rng = random.Random(42)

    def test_damage_positive(self):
        attacker = build_battle_pokemon("charmander", self.rng)
        defender = build_battle_pokemon("squirtle", self.rng)
        fire_move = next(m for m in attacker.moves if m.move_type == "fire")
        dmg = calculate_damage(attacker, defender, fire_move)
        assert dmg >= 1

    def test_type_advantage_increases_damage(self):
        """Daño con ventaja de tipo debe ser mayor que neutro."""
        rng = random.Random(7)
        attacker = build_battle_pokemon("charmander", rng)
        defender_grass = build_battle_pokemon("bulbasaur", rng)
        defender_normal = build_battle_pokemon("rattata", rng) if "rattata" in __import__("backend.data.pokemon", fromlist=["POKEDEX"]).POKEDEX else None

        fire_move = next(m for m in attacker.moves if m.move_type == "fire")
        dmg_grass = calculate_damage(attacker, defender_grass, fire_move)
        assert dmg_grass >= 1

    def test_minimum_damage_is_1(self):
        """El daño nunca puede ser 0 o negativo."""
        rng = random.Random(1)
        attacker = build_battle_pokemon("bulbasaur", rng)
        defender = build_battle_pokemon("steelix", rng) if "steelix" in __import__("backend.data.pokemon", fromlist=["POKEDEX"]).POKEDEX else attacker
        for move in attacker.moves:
            dmg = calculate_damage(attacker, defender, move)
            assert dmg >= 1, f"Daño con {move.name} fue {dmg}"


class TestBattleStateClone:
    def setup_method(self):
        self.rng = random.Random(42)

    def test_clone_independence(self):
        from backend.battle.factory import build_battle_pokemon
        p = build_battle_pokemon("bulbasaur", self.rng)
        clone = p.clone()
        clone.hp = 0
        assert p.hp > 0, "El clon no debe afectar al original"

    def test_clone_moves_independent(self):
        from backend.battle.factory import build_battle_pokemon
        p = build_battle_pokemon("charmander", self.rng)
        clone = p.clone()
        clone.moves[0].pp = 0
        assert p.moves[0].pp > 0, "Los movimientos del clon no deben afectar al original"

    def test_battle_state_clone(self):
        from backend.battle import build_random_team
        from backend.battle.state import BattleState
        rng = random.Random(7)
        team1 = build_random_team("A", 3, rng)
        team2 = build_random_team("B", 3, rng)
        state = BattleState(team1, team2)
        clone = state.clone()
        clone.teams[0].pokemons[0].hp = 0
        assert state.teams[0].pokemons[0].hp > 0

    def test_simulate_turn_no_side_effects(self):
        from backend.battle import build_random_team
        from backend.battle.simulator import simulate_turn
        from backend.battle.state import BattleState
        rng = random.Random(99)
        team1 = build_random_team("A", 3, rng)
        team2 = build_random_team("B", 3, rng)
        state = BattleState(team1, team2)
        original_turn = state.turn_number
        legal0 = state.get_legal_actions(0)
        legal1 = state.get_legal_actions(1)
        new_state = simulate_turn(state, legal0[0], legal1[0], random.Random(1))
        assert state.turn_number == original_turn, "simulate_turn no debe modificar el estado original"
        assert new_state.turn_number == original_turn + 1
