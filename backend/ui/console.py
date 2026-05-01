"""Simple console visualization for battle flow."""

from backend.battle.state import BattleState


class ConsoleBattleUI:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def show_battle_intro(self, state: BattleState) -> None:
        team1 = state.team_of(0)
        team2 = state.team_of(1)
        self.log(f"Batalla: {team1.trainer_name} vs {team2.trainer_name}")
        self.log(self._team_summary(team1, perspective="player"))
        self.log(self._team_summary(team2, perspective="ai"))

    def show_turn(self, state: BattleState) -> None:
        team1 = state.team_of(0)
        team2 = state.team_of(1)
        self.log(f"\nTurno {state.turn_number}")
        self.log(self._active_summary(team1, perspective="player"))
        self.log(self._active_summary(team2, perspective="ai"))

    def show_winner(self, winner: str, state: BattleState) -> None:
        self.log(f"\nCombate finalizado en {state.turn_number - 1} turnos. Ganador: {winner}")

    def log(self, message: str) -> None:
        if self.verbose:
            print(message)

    def _team_summary(self, team, perspective: str) -> str:
        members = ", ".join(pokemon.name for pokemon in team.pokemons)
        active = team.active_pokemon
        sprite = active.sprite_back_url if perspective == "player" else active.sprite_front_url
        return f"{team.trainer_name}: [{members}] | Sprite activo: {sprite}"

    def _active_summary(self, team, perspective: str) -> str:
        active = team.active_pokemon
        sprite = active.sprite_back_url if perspective == "player" else active.sprite_front_url
        return (
            f"{team.trainer_name} activo -> {active.name} "
            f"HP {active.hp}/{active.max_hp} ATK {active.attack} DEF {active.defense} SPD {active.speed} | {sprite}"
        )
