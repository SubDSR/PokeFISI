"""DTOs para serializar datos de la capa de datos al formato esperado por el frontend."""

from __future__ import annotations


def serialize_pokedex() -> list[dict]:
    from backend.data.pokemon import POKEDEX
    result = []
    for entry in POKEDEX.values():
        result.append({
            "id": entry.id,
            "name": entry.name,
            "level": entry.level,
            "hp": entry.hp,
            "attack": entry.attack,
            "defense": entry.defense,
            "speed": entry.speed,
            "types": entry.pokemon_type.split("/"),
            "moveIds": list(entry.move_ids),
            "spriteFrontUrl": entry.sprite_front_url,
            "spriteBackUrl": entry.sprite_back_url,
        })
    return result


DIFFICULTIES_CONFIG: list[dict] = [
    {"label": "Facil", "uiValue": "facil", "apiValue": "easy", "agent": "random"},
    {"label": "Medio", "uiValue": "medio", "apiValue": "medium", "agent": "heuristic"},
    {"label": "Dificil", "uiValue": "dificil", "apiValue": "hard", "agent": "minimax"},
    {
        "label": "Maestro-Sobrevilla",
        "uiValue": "maestro-sobrevilla",
        "apiValue": "sobrevilla",
        "agent": "minimax_optimized",
    },
]
