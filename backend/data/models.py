from dataclasses import dataclass


@dataclass(frozen=True)
class MoveData:
    id: str
    name: str
    base_power: int
    description: str


@dataclass(frozen=True)
class PokemonSpecies:
    id: str
    name: str
    level: int
    hp: int
    attack: int
    defense: int
    speed: int
    move_ids: list[str]
    sprite_front_url: str
    sprite_back_url: str
