from dataclasses import dataclass, field


@dataclass
class BattleMove:
    id: str
    name: str
    base_power: int
    accuracy: float
    move_type: str
    description: str
    max_pp: int
    pp: int

    def has_pp(self) -> bool:
        return self.pp > 0

    def consume_pp(self) -> None:
        if self.pp > 0:
            self.pp -= 1

    def clone(self) -> "BattleMove":
        return BattleMove(
            id=self.id,
            name=self.name,
            base_power=self.base_power,
            accuracy=self.accuracy,
            move_type=self.move_type,
            description=self.description,
            max_pp=self.max_pp,
            pp=self.pp,
        )


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
    pokemon_type: str
    moves: list[BattleMove]
    sprite_front_url: str
    sprite_back_url: str

    def is_fainted(self) -> bool:
        return self.hp <= 0

    @property
    def hp_ratio(self) -> float:
        return self.hp / self.max_hp if self.max_hp else 0.0

    def has_usable_moves(self) -> bool:
        return any(move.has_pp() for move in self.moves)

    def clone(self) -> "BattlePokemon":
        return BattlePokemon(
            species_id=self.species_id,
            name=self.name,
            level=self.level,
            max_hp=self.max_hp,
            hp=self.hp,
            attack=self.attack,
            defense=self.defense,
            speed=self.speed,
            pokemon_type=self.pokemon_type,
            moves=[m.clone() for m in self.moves],
            sprite_front_url=self.sprite_front_url,
            sprite_back_url=self.sprite_back_url,
        )


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

    def clone(self) -> "TeamState":
        return TeamState(
            trainer_name=self.trainer_name,
            pokemons=[p.clone() for p in self.pokemons],
            active_index=self.active_index,
        )

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
