"""Serializable battle view state for renderers independent from battle logic."""

from __future__ import annotations

from backend.battle.models import BattleAction, BattlePokemon, TeamState
from backend.battle.state import BattleState


def _hp_color(hp_ratio: float) -> str:
    if hp_ratio > 0.5:
        return "#66d15f"
    if hp_ratio > 0.2:
        return "#e5c84c"
    return "#e05b63"


def _serialize_move_slots(actions: list[BattleAction]) -> list[dict]:
    slots: list[dict] = []
    for action in actions[:4]:
        slots.append(
            {
                "type": action.action_type,
                "label": action.label.upper(),
                "index": action.index,
                "enabled": True,
            }
        )

    while len(slots) < 4:
        slots.append({"type": "empty", "label": "-", "index": -1, "enabled": False})
    return slots


def _serialize_action_groups(actions: list[BattleAction], forced_switch: bool) -> dict:
    moves = []
    switches = []
    for action in actions:
        serialized = {
            "actionType": action.action_type,
            "index": action.index,
            "label": action.label,
        }
        if action.action_type == "move":
            moves.append(serialized)
        elif action.action_type == "switch":
            switches.append(serialized)

    return {
        "moves": moves,
        "switches": switches,
        "forcedSwitch": forced_switch,
    }


def _serialize_party(team: TeamState) -> list[dict]:
    return [
        {
            "name": pokemon.name,
            "fainted": pokemon.is_fainted(),
            "active": index == team.active_index,
            "hpRatio": round(pokemon.hp_ratio, 4),
            "status": "fainted" if pokemon.is_fainted() else ("active" if index == team.active_index else "available"),
        }
        for index, pokemon in enumerate(team.pokemons)
    ]


def _serialize_pokemon(pokemon: BattlePokemon, perspective: str) -> dict:
    sprite_url = pokemon.sprite_back_url if perspective == "player" else pokemon.sprite_front_url
    return {
        "name": pokemon.name,
        "level": pokemon.level,
        "currentHp": pokemon.hp,
        "maxHp": pokemon.max_hp,
        "hpRatio": round(pokemon.hp_ratio, 4),
        "hpPercent": round(pokemon.hp_ratio * 100, 2),
        "hpColor": _hp_color(pokemon.hp_ratio),
        "attack": pokemon.attack,
        "defense": pokemon.defense,
        "speed": pokemon.speed,
        "spriteUrl": sprite_url,
        "moves": [move.name for move in pokemon.moves],
        "fainted": pokemon.is_fainted(),
    }


def build_view_state(
    state: BattleState,
    message: str,
    player_actions: list[BattleAction] | None = None,
    panel: dict | None = None,
) -> dict:
    player_team = state.team_of(0)
    enemy_team = state.team_of(1)
    actions = player_actions if player_actions is not None else state.get_legal_actions(0)
    forced_switch = bool(actions) and all(action.action_type == "switch" for action in actions)

    panel_state = {
        "menu": "switch" if forced_switch else "root",
        "selectedGroup": None,
        "selectedIndex": None,
        "locked": False,
    }
    if panel:
        panel_state.update(panel)

    return {
        "turn": state.turn_number,
        "message": message,
        "player": {
            "trainer": player_team.trainer_name,
            "active": _serialize_pokemon(player_team.active_pokemon, perspective="player"),
            "party": _serialize_party(player_team),
        },
        "enemy": {
            "trainer": enemy_team.trainer_name,
            "active": _serialize_pokemon(enemy_team.active_pokemon, perspective="enemy"),
            "party": _serialize_party(enemy_team),
        },
        "actions": _serialize_move_slots(actions),
        "actionGroups": _serialize_action_groups(actions, forced_switch),
        "panel": panel_state,
    }
