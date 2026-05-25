"""Funciones heurísticas puras y normalizadas para el agente Minimax.

Cada función:
  - Es pura (sin efectos secundarios ni estado mutable).
  - Retorna un valor en [-1, 1] (o [-1, 0] / [0, 1] según se indica).
  - Es testeable unitariamente de forma independiente.
"""

from __future__ import annotations

import math

from backend.battle.damage import calculate_damage
from backend.battle.models import BattlePokemon
from backend.battle.state import BattleState
from backend.data.types import get_type_multiplier, parse_types


# ──────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────

def _best_move_type_multiplier(attacker: BattlePokemon, defender: BattlePokemon) -> float:
    """Máximo multiplicador de tipo entre todos los movimientos del atacante."""
    best = 1.0
    for move in attacker.moves:
        if move.has_pp():
            mult = get_type_multiplier(move.move_type, defender.pokemon_type)
            if mult > best:
                best = mult
    return best


def _max_expected_damage(attacker: BattlePokemon, defender: BattlePokemon) -> float:
    """Daño esperado máximo que puede infligir el atacante con su mejor movimiento."""
    best = 0.0
    for move in attacker.moves:
        if move.has_pp():
            dmg = calculate_damage(attacker, defender, move) * move.accuracy
            if dmg > best:
                best = dmg
    return best


# ──────────────────────────────────────────────
# Factores individuales
# ──────────────────────────────────────────────

def f_pokemon_vivos(state: BattleState, player_index: int) -> float:
    """Diferencia relativa de Pokémon vivos.

    Fórmula: (vivos_propio - vivos_rival) / tamaño_equipo
    Rango: [-1, 1]
    """
    my_team = state.team_of(player_index)
    opp_team = state.opponent_of(player_index)
    team_size = max(1, len(my_team.pokemons))

    alive_mine = sum(1 for p in my_team.pokemons if not p.is_fainted())
    alive_opp = sum(1 for p in opp_team.pokemons if not p.is_fainted())
    return (alive_mine - alive_opp) / team_size


def f_ventaja_tipo(state: BattleState, player_index: int) -> float:
    """Ventaja de tipo del Pokémon activo propio vs rival.

    Considera el mejor ataque propio contra el rival
    y el mejor ataque rival contra el propio.
    Fórmula: (mult_nuestro - mult_rival) / 2
    Rango: [-1, 1]  (teórico hasta ±2 con inmunidad, dividido por 2 queda ≤ ±1.5;
                     en la práctica la pared de 2.0 máx da ≤ 1.0 con tipos simples)
    """
    my_active = state.team_of(player_index).active_pokemon
    opp_active = state.opponent_of(player_index).active_pokemon

    mult_mine = _best_move_type_multiplier(my_active, opp_active)
    mult_opp = _best_move_type_multiplier(opp_active, my_active)

    raw = (mult_mine - mult_opp) / 2.0
    return max(-1.0, min(1.0, raw))


def f_velocidad(state: BattleState, player_index: int) -> float:
    """Ventaja de velocidad del Pokémon activo propio vs rival.

    Fórmula: tanh((speed_propio - speed_rival) / 100)
    Rango: (-1, 1)
    """
    my_speed = state.team_of(player_index).active_pokemon.speed
    opp_speed = state.opponent_of(player_index).active_pokemon.speed
    return math.tanh((my_speed - opp_speed) / 100.0)


def f_hp_restante(state: BattleState, player_index: int) -> float:
    """Ventaja de HP total normalizado del equipo propio vs rival.

    Fórmula: (hp_ratio_propio) - (hp_ratio_rival)
    Rango: [-1, 1]
    """
    my_team = state.team_of(player_index)
    opp_team = state.opponent_of(player_index)

    def _team_hp_ratio(team) -> float:
        total_hp = sum(p.hp for p in team.pokemons)
        total_max = sum(p.max_hp for p in team.pokemons)
        return total_hp / max(1, total_max)

    return _team_hp_ratio(my_team) - _team_hp_ratio(opp_team)


def f_riesgo_morir(state: BattleState, player_index: int) -> float:
    """Penalización por riesgo de que el Pokémon activo propio sea debilitado.

    Cálculo:
      1. Daño máximo que puede infligir el rival con su mejor movimiento.
      2. Si hp_actual ≤ daño_máximo → riesgo = 1.0
      3. Si hp_actual ≥ 2 × daño_máximo → riesgo = 0.0
      4. Interpolación lineal entre esos extremos.
      5. Si el rival es más rápido (ataca primero) → riesgo × 1.5 (cap 1.0).

    Retorno normalizado a [-1, 0]: valores negativos son penalizaciones.
    Rango: [-1, 0]
    """
    my_active = state.team_of(player_index).active_pokemon
    opp_active = state.opponent_of(player_index).active_pokemon

    max_opp_damage = _max_expected_damage(opp_active, my_active)

    if max_opp_damage <= 0:
        return 0.0

    hp = my_active.hp

    if hp <= max_opp_damage:
        riesgo = 1.0
    elif hp >= 2 * max_opp_damage:
        riesgo = 0.0
    else:
        riesgo = 1.0 - (hp - max_opp_damage) / max_opp_damage

    # Si el rival es más rápido, el riesgo se agrava
    if opp_active.speed > my_active.speed:
        riesgo = min(1.0, riesgo * 1.5)

    return -riesgo  # penalización negativa


# ──────────────────────────────────────────────
# Función heurística compuesta
# ──────────────────────────────────────────────

DEFAULT_WEIGHTS: list[float] = [0.4, 0.2, 0.1, 0.2, 0.1]

WIN_VALUE = 1000.0
LOSS_VALUE = -1000.0
DRAW_VALUE = 0.0


def evaluate_state(
    state: BattleState,
    player_index: int,
    weights: list[float] | None = None,
) -> float:
    """Función heurística compuesta y normalizada.

    h = W1·f_pokemon_vivos + W2·f_ventaja_tipo + W3·f_velocidad
      + W4·f_hp_restante + W5·f_riesgo_morir

    Para estados terminales retorna ±1000 (sin evaluar factores).
    """
    w = weights if weights is not None else DEFAULT_WEIGHTS

    if state.battle_over():
        winner = state.winner()
        my_name = state.team_of(player_index).trainer_name
        if winner == my_name:
            return WIN_VALUE
        if winner == "Empate":
            return DRAW_VALUE
        return LOSS_VALUE

    f1 = f_pokemon_vivos(state, player_index)
    f2 = f_ventaja_tipo(state, player_index)
    f3 = f_velocidad(state, player_index)
    f4 = f_hp_restante(state, player_index)
    f5 = f_riesgo_morir(state, player_index)

    return w[0] * f1 + w[1] * f2 + w[2] * f3 + w[3] * f4 + w[4] * f5
