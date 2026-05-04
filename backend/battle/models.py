from dataclasses import dataclass, field


@dataclass(frozen=True)
class BattleMove:
    id: str
    name: str
    base_power: int
    accuracy: float
    move_type: str
    description: str


@dataclass
class BattlePokemon:
    species_id: str
    name: str
    level: int
    max_hp: int
    hp: int
    attack: int
    defense: int
    speed: int
    moves: list[BattleMove]
    sprite_front_url: str
    sprite_back_url: str

    def is_fainted(self) -> bool:
        return self.hp <= 0

    @property
    def hp_ratio(self) -> float:
        return self.hp / self.max_hp if self.max_hp else 0.0


@dataclass(frozen=True)
class BattleAction:
    action_type: str
    index: int
    label: str


@dataclass
class TeamState:
    trainer_name: str
    pokemons: list[BattlePokemon]
    active_index: int = 0

    @property
    def active_pokemon(self) -> BattlePokemon:
        return self.pokemons[self.active_index]

    def all_fainted(self) -> bool:
        return all(pokemon.is_fainted() for pokemon in self.pokemons)

    def available_switches(self) -> list[tuple[int, BattlePokemon]]:
        switches: list[tuple[int, BattlePokemon]] = []
        for index, pokemon in enumerate(self.pokemons):
            if index == self.active_index or pokemon.is_fainted():
                continue
            switches.append((index, pokemon))
        return switches


@dataclass
class BattleResult:
    winner: str
    turns: int
    log: list[str] = field(default_factory=list)
