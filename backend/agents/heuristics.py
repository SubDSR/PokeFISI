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
from backend.data.types import get_type_multiplier


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
    """Ventaja de HP ponderado del equipo propio vs rival.

    El Pokémon activo pesa 2× respecto a la banca porque es el que está en
    riesgo inmediato. Sin este peso, perder el activo tiene el mismo impacto
    en el ratio que perder un Pokémon de reserva, suavizando demasiado la señal.
    Rango: [-1, 1]
    """
    def _weighted_hp_ratio(team) -> float:
        active = team.active_pokemon
        active_ratio = active.hp / max(1, active.max_hp)
        bench = [p for i, p in enumerate(team.pokemons)
                 if i != team.active_index and not p.is_fainted()]
        if not bench:
            return active_ratio
        bench_ratio = sum(p.hp / max(1, p.max_hp) for p in bench) / len(bench)
        return (2 * active_ratio + bench_ratio) / 3

    return _weighted_hp_ratio(state.team_of(player_index)) - \
           _weighted_hp_ratio(state.opponent_of(player_index))


def f_riesgo_morir(state: BattleState, player_index: int) -> float:
    """Penalización por riesgo de que el Pokémon activo propio sea debilitado.

    Cálculo:
      1. Daño máximo que puede infligir el rival con su mejor movimiento.
      2. Si hp_actual ≤ daño_máximo Y rival más rápido → riesgo = 1.0 (muerte antes de atacar)
      3. Si hp_actual ≤ daño_máximo (pero propio más rápido) → riesgo = 0.85 (puede atacar primero)
      4. Si hp_actual ≥ 2 × daño_máximo → riesgo = 0.0
      5. Interpolación lineal entre esos extremos; si rival es más rápido → × 1.5 (cap 1.0).
      6. Bug B: si riesgo ≥ 0.85 y hay un Pokémon de banca que absorbería el golpe,
         penalizar 0.15 extra (el agente está desperdiciando el turno al quedarse).

    Retorno normalizado a [-1, 0]: valores negativos son penalizaciones.
    Rango: [-1, 0]
    """
    my_team = state.team_of(player_index)
    my_active = my_team.active_pokemon
    opp_active = state.opponent_of(player_index).active_pokemon

    max_opp_damage = _max_expected_damage(opp_active, my_active)

    if max_opp_damage <= 0:
        return 0.0

    hp = my_active.hp
    opp_faster = opp_active.speed > my_active.speed

    if hp <= max_opp_damage:
        riesgo = 1.0 if opp_faster else 0.85
    elif hp >= 2 * max_opp_damage:
        riesgo = 0.0
    else:
        riesgo = 1.0 - (hp - max_opp_damage) / max_opp_damage
        if opp_faster:
            riesgo = min(1.0, riesgo * 1.5)

    # Bug B: penalizar el "sacrificio gratuito": quedarse cuando hay banca que sobreviviría.
    # Sin este bonus, hacer daño antes de morir puede superar la penalización base,
    # porque f_hp_restante sube al dañar al rival aunque el activo muera después.
    if riesgo >= 0.85:
        bench = [p for i, p in enumerate(my_team.pokemons)
                 if i != my_team.active_index and not p.is_fainted()]
        if bench:
            min_bench_dmg_ratio = min(
                max_opp_damage / max(1, p.hp) for p in bench
            )
            if min_bench_dmg_ratio < 0.7:  # algún Pokémon de banca sobreviviría con >30% HP
                riesgo = min(1.0, riesgo + 0.15)

    return -riesgo  # penalización negativa


def f_win_condition(state: BattleState, player_index: int) -> float:
    """Counters VIABLES en reserva: sobreviven un golpe del rival Y tienen ventaja de tipo.

    Un Pokémon en reserva es 'counter viable' solo si cumple AMBAS condiciones:
      1. HP actual > daño esperado del mejor ataque rival (sobrevive al menos un turno)
      2. Ventaja de tipo real (≥ 2×) contra algún rival vivo

    Por qué es mejor que f_matchup_potencial (hp_ratio lineal):
      - f_matchup_potencial: Psyduck 50HP → 0.50, Psyduck 18HP → 0.18 (diferencia: 0.32)
      - f_win_condition:     Psyduck 50HP → 0.50, Psyduck 18HP → 0.00 (diferencia: 0.50)
    El umbral de supervivencia crea una señal binaria exactamente donde importa:
    cruzar de 50HP a 18HP frente a Ponyta no es 'perder algo de valor', es
    PERDER COMPLETAMENTE la condición de victoria.

    Rango: [0, 1]
    """
    my_team = state.team_of(player_index)
    opp_team = state.opponent_of(player_index)

    bench = [
        p for i, p in enumerate(my_team.pokemons)
        if not p.is_fainted() and i != my_team.active_index
    ]
    opp_alive = [p for p in opp_team.pokemons if not p.is_fainted()]

    if not bench or not opp_alive:
        return 0.0

    viable = 0
    for bench_poke in bench:
        for opp_poke in opp_alive:
            best_mult = max(
                (get_type_multiplier(m.move_type, opp_poke.pokemon_type)
                 for m in bench_poke.moves if m.has_pp()),
                default=1.0,
            )
            if best_mult < 2.0:
                continue  # Sin ventaja de tipo real contra este rival
            opp_best_dmg = _max_expected_damage(opp_poke, bench_poke)
            if bench_poke.hp > opp_best_dmg:
                viable += 1
                break  # Este bench_poke ya cuenta como viable

    return min(1.0, viable / max(1, len(bench)))


def f_accion_util(state: BattleState, player_index: int) -> float:
    """Diferencia de daño esperado normalizado entre el activo propio y el rival.

    Cuando el activo propio no puede infligir daño significativo (matchup resistido),
    la señal baja, indicando que un cambio tiene sentido. Si el entrante tampoco puede
    atacar bien, el score se mantiene bajo y el agente ve que ninguna opción es buena,
    que es la verdad táctica — reduciendo el ping-pong de switches improductivos.

    Rango: [-1, 1]
    """
    my_active = state.team_of(player_index).active_pokemon
    opp_active = state.opponent_of(player_index).active_pokemon

    my_best_dmg = max(
        (calculate_damage(my_active, opp_active, m) * m.accuracy
         for m in my_active.moves if m.has_pp()),
        default=0.0,
    )
    opp_best_dmg = max(
        (calculate_damage(opp_active, my_active, m) * m.accuracy
         for m in opp_active.moves if m.has_pp()),
        default=0.0,
    )

    my_dmg_ratio = my_best_dmg / max(1, opp_active.max_hp)
    opp_dmg_ratio = opp_best_dmg / max(1, my_active.max_hp)

    return max(-1.0, min(1.0, my_dmg_ratio - opp_dmg_ratio))


# ──────────────────────────────────────────────
# Función heurística compuesta
# ──────────────────────────────────────────────

DEFAULT_WEIGHTS: list[float] = [0.20, 0.10, 0.05, 0.15, 0.30, 0.10, 0.10]

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
      + W4·f_hp_restante + W5·f_riesgo_morir + W6·f_win_condition
      + W7·f_accion_util

    Para estados terminales retorna ±1000 (sin evaluar factores).
    """
    if weights is None:
        w = DEFAULT_WEIGHTS
    else:
        # Compatibilidad con configuraciones antiguas de 6 pesos: el bonus
        # de HP en banca adopta el peso por defecto en lugar de fallar.
        w = list(weights[: len(DEFAULT_WEIGHTS)])
        if len(w) < len(DEFAULT_WEIGHTS):
            w.extend(DEFAULT_WEIGHTS[len(w):])

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
    f6 = f_win_condition(state, player_index)
    f7 = f_accion_util(state, player_index)

    return w[0]*f1 + w[1]*f2 + w[2]*f3 + w[3]*f4 + w[4]*f5 + w[5]*f6 + w[6]*f7
