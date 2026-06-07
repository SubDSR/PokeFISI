"""Simulación sin efectos secundarios para el árbol de búsqueda Minimax.

Ninguna función aquí modifica el estado real de una batalla activa.
Todas operan sobre copias clonadas (BattleState.clone()).
"""

from __future__ import annotations

import random

from backend.battle.damage import calculate_damage
from backend.battle.models import BattleAction, BattlePokemon, TeamState
from backend.battle.state import BattleState


def _auto_switch_fainted(state: BattleState, player_index: int) -> None:
    """Cambia automáticamente al primer Pokémon vivo si el activo está debilitado."""
    team = state.team_of(player_index)
    if team.all_fainted() or not team.active_pokemon.is_fainted():
        return
    for i, pokemon in enumerate(team.pokemons):
        if not pokemon.is_fainted():
            team.active_index = i
            return


def _exec_switch(state: BattleState, player_index: int, switch_index: int) -> None:
    team = state.team_of(player_index)
    if switch_index < 0 or switch_index >= len(team.pokemons):
        return
    target = team.pokemons[switch_index]
    if target.is_fainted() or switch_index == team.active_index:
        return
    team.active_index = switch_index


def _exec_move(
    state: BattleState,
    player_index: int,
    move_index: int,
    rng: random.Random,
) -> None:
    attacker_team = state.team_of(player_index)
    defender_team = state.opponent_of(player_index)
    attacker = attacker_team.active_pokemon
    defender = defender_team.active_pokemon

    if attacker.is_fainted():
        return
    if move_index < 0 or move_index >= len(attacker.moves):
        return

    move = attacker.moves[move_index]
    if not move.has_pp():
        return

    move.consume_pp()
    if rng.random() > move.accuracy:
        return  # falla

    damage = calculate_damage(attacker, defender, move)
    defender.hp = max(0, defender.hp - damage)


def _exec_struggle(state: BattleState, player_index: int) -> None:
    attacker = state.team_of(player_index).active_pokemon
    defender = state.opponent_of(player_index).active_pokemon
    if attacker.is_fainted():
        return
    damage = max(1, int(attacker.attack * 0.5))
    recoil = max(1, damage // 4)
    defender.hp = max(0, defender.hp - damage)
    attacker.hp = max(0, attacker.hp - recoil)


def simulate_action(
    state: BattleState,
    player_index: int,
    action: BattleAction,
    rng: random.Random,
) -> None:
    """Aplica UNA acción de un jugador sobre el estado (ya clonado) in-place.

    No retorna nada — modifica el clon. No toca el estado original.
    """
    if action.action_type == "switch":
        _exec_switch(state, player_index, action.index)
    elif action.action_type == "move":
        _exec_move(state, player_index, action.index, rng)
    elif action.action_type == "struggle":
        _exec_struggle(state, player_index)
    # "pass" se ignora


def simulate_turn(
    state: BattleState,
    action_p0: BattleAction,
    action_p1: BattleAction,
    rng: random.Random | None = None,
) -> BattleState:
    """Simula un turno completo con las acciones de ambos jugadores.

    Respeta:
      - Prioridad de cambio de Pokémon (switches van primero)
      - Orden por velocidad (mayor velocidad actúa antes)
      - Precisión de movimientos (determinista con la semilla dada)
      - Auto-switch tras debilitamiento

    Args:
        state: Estado original (NO se modifica).
        action_p0: Acción del jugador 0.
        action_p1: Acción del jugador 1.
        rng: Generador aleatorio reproducible.

    Returns:
        Nuevo BattleState resultado del turno.
    """
    if rng is None:
        rng = random.Random(0)

    cloned = state.clone()
    actions = [(0, action_p0), (1, action_p1)]

    # Ordenar: switches primero, luego por velocidad descendente
    def _sort_key(entry: tuple[int, BattleAction]) -> tuple[int, int]:
        player_idx, action = entry
        priority = 0 if action.action_type == "switch" else 1
        speed = cloned.team_of(player_idx).active_pokemon.speed
        return (priority, -speed)

    ordered = sorted(actions, key=_sort_key)

    # Registrar qué Pokémon estaba activo al inicio del turno para cada jugador.
    # Si un Pokémon muere por el ataque del rival (va primero por velocidad) y el
    # simulador hace auto-switch, el Pokémon de reemplazo NO debe ejecutar la acción
    # que había elegido el Pokémon caído — ese ataque se cancela.
    initial_active_idx = [cloned.teams[0].active_index, cloned.teams[1].active_index]

    for player_idx, action in ordered:
        if cloned.battle_over():
            break

        # Cancelar un movimiento si el Pokémon que lo eligió ya cayó y fue reemplazado
        if action.action_type == "move":
            current_idx = cloned.teams[player_idx].active_index
            original_pokemon = cloned.teams[player_idx].pokemons[initial_active_idx[player_idx]]
            if current_idx != initial_active_idx[player_idx] and original_pokemon.is_fainted():
                _auto_switch_fainted(cloned, 1 - player_idx)
                continue

        simulate_action(cloned, player_idx, action, rng)
        # Resolver cambio forzado del oponente tras debilitamiento
        _auto_switch_fainted(cloned, 1 - player_idx)

    # Resolver cambios forzados pendientes al final del turno
    for pi in range(2):
        _auto_switch_fainted(cloned, pi)

    cloned.turn_number += 1
    return cloned
