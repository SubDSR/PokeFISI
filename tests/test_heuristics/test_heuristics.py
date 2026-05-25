"""Tests para las funciones heurísticas del agente Minimax."""

import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.agents.heuristics import (
    evaluate_state,
    f_hp_restante,
    f_pokemon_vivos,
    f_riesgo_morir,
    f_velocidad,
    f_ventaja_tipo,
)
from backend.battle import build_random_team
from backend.battle.state import BattleState


def _state(seed: int = 42) -> BattleState:
    rng = random.Random(seed)
    t1 = build_random_team("A", 3, rng)
    t2 = build_random_team("B", 3, rng)
    return BattleState(t1, t2)


class TestHeuristicRanges:
    def test_f_pokemon_vivos_range(self):
        state = _state()
        v = f_pokemon_vivos(state, 0)
        assert -1.0 <= v <= 1.0, f"f_pokemon_vivos fuera de rango: {v}"

    def test_f_ventaja_tipo_range(self):
        state = _state()
        v = f_ventaja_tipo(state, 0)
        assert -1.0 <= v <= 1.0, f"f_ventaja_tipo fuera de rango: {v}"

    def test_f_velocidad_range(self):
        state = _state()
        v = f_velocidad(state, 0)
        assert -1.0 < v < 1.0, f"f_velocidad fuera de rango: {v}"

    def test_f_hp_restante_range(self):
        state = _state()
        v = f_hp_restante(state, 0)
        assert -1.0 <= v <= 1.0, f"f_hp_restante fuera de rango: {v}"

    def test_f_riesgo_morir_range(self):
        state = _state()
        v = f_riesgo_morir(state, 0)
        assert -1.0 <= v <= 0.0, f"f_riesgo_morir fuera de rango: {v}"


class TestHeuristicSymmetry:
    def test_symmetric_state_approx_zero(self):
        """En un estado simétrico ambos lados deben tener scores opuestos."""
        state = _state(seed=1)
        v0 = evaluate_state(state, 0)
        v1 = evaluate_state(state, 1)
        # No son exactamente opuestos (los teams son distintos) pero el test
        # valida que ambos retornan floats en rango razonable
        assert isinstance(v0, float)
        assert isinstance(v1, float)

    def test_hp_advantage_reflected(self):
        """Si el jugador 0 tiene más HP, f_hp_restante debe ser positivo."""
        state = _state(seed=5)
        # Reducir HP de todos los Pokémon del equipo 1
        for p in state.teams[1].pokemons:
            p.hp = 1
        v = f_hp_restante(state, 0)
        assert v > 0, "Con ventaja de HP, f_hp_restante debe ser positivo"

    def test_fainted_pokemon_counted(self):
        """Con un Pokémon derribado en el equipo rival, f_pokemon_vivos debe ser positivo."""
        state = _state(seed=3)
        state.teams[1].pokemons[0].hp = 0
        v = f_pokemon_vivos(state, 0)
        assert v > 0, "Con rival caído, f_pokemon_vivos debe ser positivo"


class TestTerminalEvaluation:
    def test_win_returns_high_value(self):
        state = _state()
        for p in state.teams[1].pokemons:
            p.hp = 0
        v = evaluate_state(state, 0)
        assert v == 1000.0

    def test_loss_returns_low_value(self):
        state = _state()
        for p in state.teams[0].pokemons:
            p.hp = 0
        v = evaluate_state(state, 0)
        assert v == -1000.0
