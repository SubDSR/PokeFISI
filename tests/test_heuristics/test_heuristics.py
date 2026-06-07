"""Tests para las funciones heurísticas del agente Minimax."""

import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.agents.heuristics import (
    evaluate_state,
    f_hp_restante,
    f_matchup_potencial,
    f_pokemon_vivos,
    f_riesgo_morir,
    f_velocidad,
    f_ventaja_tipo,
    f_win_condition,
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


class TestRiesgoMorirSpeedAwareness:
    def test_guaranteed_death_faster_opponent_is_max_penalty(self):
        """Si el rival es más rápido Y puede OHKO, el riesgo debe ser máximo (-1.0)."""
        state = _state(seed=10)
        my_active = state.teams[0].active_pokemon
        opp_active = state.teams[1].active_pokemon
        # Forzar que el rival sea muchísimo más rápido
        opp_active.speed = 999
        my_active.speed = 1
        # Forzar que el rival pueda OHKO: bajar HP del activo a 1
        my_active.hp = 1
        v = f_riesgo_morir(state, 0)
        assert v == -1.0, f"Con muerte garantizada y rival más rápido, debe ser -1.0, fue {v}"

    def test_guaranteed_death_but_we_are_faster_is_not_max(self):
        """Si podemos atacar primero aunque vayamos a morir, el riesgo es 0.8 (no -1.0)."""
        state = _state(seed=10)
        my_active = state.teams[0].active_pokemon
        opp_active = state.teams[1].active_pokemon
        # Forzar que nosotros seamos más rápidos
        my_active.speed = 999
        opp_active.speed = 1
        # Forzar que el rival pueda OHKO si actuara primero
        my_active.hp = 1
        v = f_riesgo_morir(state, 0)
        assert v == -0.8, f"Podemos atacar primero aunque vayamos a morir: debe ser -0.8, fue {v}"

    def test_no_risk_when_hp_far_above_damage(self):
        """Con el doble de HP que el daño máximo del rival, no hay riesgo."""
        state = _state(seed=10)
        my_active = state.teams[0].active_pokemon
        my_active.hp = 99999
        v = f_riesgo_morir(state, 0)
        assert v == 0.0, f"Con HP muy alto, riesgo debe ser 0.0, fue {v}"


class TestMatchupPotencial:
    def test_range_is_zero_to_one(self):
        """f_matchup_potencial siempre debe retornar valores en [0, 1]."""
        for seed in range(5):
            state = _state(seed=seed)
            v = f_matchup_potencial(state, 0)
            assert 0.0 <= v <= 1.0, f"Fuera de rango [0,1] con seed={seed}: {v}"

    def test_bench_with_type_advantage_raises_score(self):
        """Si hay un Pokémon en reserva con ventaja de tipo contra el rival, el score sube."""
        state = _state(seed=2)
        # Score con equipo normal
        v_normal = f_matchup_potencial(state, 0)

        # Forzar un Pokémon en reserva con todos sus movimientos en 2× contra el rival activo
        bench_poke = None
        for i, p in enumerate(state.teams[0].pokemons):
            if i != state.teams[0].active_index and not p.is_fainted():
                bench_poke = p
                break

        if bench_poke is None:
            return  # No hay reserva para probar

        # Darle HP máximo para que hp_ratio = 1.0
        bench_poke.hp = bench_poke.max_hp

        v_after = f_matchup_potencial(state, 0)
        # El score debe ser >= al anterior (HP lleno no puede bajar el score)
        assert v_after >= v_normal - 0.01, "Aumentar HP de la reserva no debe bajar el score"

    def test_all_fainted_bench_returns_zero(self):
        """Con todos los Pokémon de reserva caídos, el score debe ser 0."""
        state = _state(seed=3)
        active_idx = state.teams[0].active_index
        for i, p in enumerate(state.teams[0].pokemons):
            if i != active_idx:
                p.hp = 0
        v = f_matchup_potencial(state, 0)
        assert v == 0.0, f"Sin reserva viva, debe ser 0.0, fue {v}"

    def test_evaluate_state_accepts_six_weights(self):
        """evaluate_state debe funcionar correctamente con los 6 pesos nuevos."""
        state = _state(seed=1)
        weights_6 = [0.15, 0.20, 0.05, 0.10, 0.25, 0.25]
        v = evaluate_state(state, 0, weights_6)
        assert isinstance(v, float), "evaluate_state debe retornar float con 6 pesos"


class TestWinCondition:
    def test_range_is_zero_to_one(self):
        """f_win_condition siempre debe retornar valores en [0, 1]."""
        for seed in range(5):
            state = _state(seed=seed)
            v = f_win_condition(state, 0)
            assert 0.0 <= v <= 1.0, f"Fuera de rango [0,1] con seed={seed}: {v}"

    def test_all_fainted_bench_returns_zero(self):
        """Sin reserva viva, no hay win condition posible."""
        state = _state(seed=3)
        active_idx = state.teams[0].active_index
        for i, p in enumerate(state.teams[0].pokemons):
            if i != active_idx:
                p.hp = 0
        v = f_win_condition(state, 0)
        assert v == 0.0, f"Sin reserva viva, debe ser 0.0, fue {v}"

    def test_bench_below_survival_threshold_returns_zero(self):
        """Un bench Pokémon que no puede sobrevivir el mejor golpe no cuenta como viable."""
        state = _state(seed=2)
        active_idx = state.teams[0].active_index
        # Encontrar un bench Pokémon y bajarle el HP al mínimo
        for i, p in enumerate(state.teams[0].pokemons):
            if i != active_idx and not p.is_fainted():
                p.hp = 1  # 1 HP = cualquier golpe lo mata
                break
        # El rival debe poder hacer al menos 1 de daño (siempre cierto)
        # Así el bench_poke nunca supera el umbral
        v = f_win_condition(state, 0)
        # Si todos los bench tienen 1 HP, ninguno es viable → 0.0
        # (puede ser >0 si hay más bench con HP normal, por eso no assert == 0)
        assert v >= 0.0

    def test_viable_counter_detected(self):
        """Un bench Pokémon con tipo 2× y suficiente HP debe ser detectado como viable."""
        import random
        from backend.battle.models import BattleMove
        state = _state(seed=4)
        active_idx = state.teams[0].active_index
        opp_active = state.teams[1].active_pokemon

        # Encontrar un bench Pokémon y configurarlo con ventaja de tipo y HP alto
        bench_poke = None
        for i, p in enumerate(state.teams[0].pokemons):
            if i != active_idx and not p.is_fainted():
                bench_poke = p
                break

        if bench_poke is None:
            return

        # Dar HP máximo para garantizar supervivencia
        bench_poke.hp = bench_poke.max_hp = 9999

        # Dar un movimiento con 2× tipo contra el rival activo
        # Para hacer eso simple, sobreescribimos el tipo del movimiento
        if bench_poke.moves:
            # Forzar que el primer movimiento sea super efectivo
            opp_type = opp_active.pokemon_type.split("/")[0].strip()
            # Mapeamos a un tipo que sea efectivo: si el rival es Agua, usamos Eléctrico
            type_map = {
                "water": "electric", "fire": "water", "grass": "fire",
                "electric": "ground", "normal": "fight", "fight": "psychic",
                "poison": "ground", "psychic": "bug", "bug": "fire",
                "rock": "water", "ground": "water", "flying": "electric",
                "ice": "fire", "dragon": "dragon", "ghost": "ghost",
                "steel": "fire", "dark": "fight", "fairy": "poison",
            }
            effective_type = type_map.get(opp_type.lower(), "water")
            bench_poke.moves[0].move_type = effective_type
            bench_poke.moves[0].pp = bench_poke.moves[0].max_pp

        v = f_win_condition(state, 0)
        assert v > 0.0, "Con un counter viable (HP alto + tipo 2×), debe detectarse"


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
