"""Simple console visualization for battle flow."""

import time

from backend.battle.models import BattleAction
from backend.battle.state import BattleState


class ConsoleBattleUI:
    def __init__(
        self,
        verbose: bool = True,
        message_delay: float = 0.35,
        decision_delay: float = 1.0,
    ):
        self.verbose = verbose
        self.message_delay = max(0.0, message_delay)
        self.decision_delay = max(0.0, decision_delay)

    def show_battle_intro(self, state: BattleState) -> None:
        team1 = state.team_of(0)
        team2 = state.team_of(1)
        self.log(f"Batalla: {team1.trainer_name} vs {team2.trainer_name}")
        self.log(self._team_summary(team1, perspective="player"))
        self.log(self._team_summary(team2, perspective="ai"))
        self.log("Las IAs aleatorias no calculan la mejor jugada: sortean una accion valida por indice.")

    def show_turn(self, state: BattleState) -> None:
        team1 = state.team_of(0)
        team2 = state.team_of(1)
        self.log(f"\nTurno {state.turn_number}")
        self.log(self._active_summary(team1, perspective="player"))
        self.log(self._active_summary(team2, perspective="ai"))

    def show_winner(self, winner: str, state: BattleState) -> None:
        self.log(f"\nCombate finalizado en {state.turn_number - 1} turnos. Ganador: {winner}")

    def on_action_selection(
        self,
        state: BattleState,
        player_index: int,
        legal_actions: list[BattleAction],
        proposed_action: BattleAction,
        final_action: BattleAction,
        decision_details: dict | None = None,
        forced: bool = False,
    ) -> None:
        trainer_name = state.team_of(player_index).trainer_name
        context = " para cambio forzado" if forced else ""
        self.log(f"{trainer_name} analiza {len(legal_actions)} acciones legales{context}:", pause=0.0)
        for action_index, action in enumerate(legal_actions):
            self.log(f"  [{action_index}] {action.label}", pause=0.0)

        self._pause(self.decision_delay)
        self._describe_random_choice(trainer_name, legal_actions, proposed_action, decision_details)
        if proposed_action != final_action:
            self.log(
                f"{trainer_name} propuso una accion invalida; se reemplaza por {final_action.label}.",
                pause=0.0,
            )
        self._pause(self.decision_delay)
        self.log(f"{trainer_name} ejecuta: {final_action.label}")

    def log(self, message: str, pause: float | None = None) -> None:
        if self.verbose:
            print(message)
            self._pause(self.message_delay if pause is None else pause)

    def _describe_random_choice(
        self,
        trainer_name: str,
        legal_actions: list[BattleAction],
        proposed_action: BattleAction,
        decision_details: dict | None,
    ) -> None:
        selected_index = None
        if decision_details and decision_details.get("strategy") == "random":
            selected_index = decision_details.get("choice_index")
        elif proposed_action in legal_actions:
            selected_index = legal_actions.index(proposed_action)

        if selected_index is None:
            self.log(f"{trainer_name} no devolvio una accion valida.", pause=0.0)
            return

        max_index = len(legal_actions) - 1
        self.log(
            f"{trainer_name} hace un sorteo uniforme entre 0 y {max_index}: sale [{selected_index}].",
            pause=0.0,
        )
        self.log(f"El indice [{selected_index}] corresponde a {proposed_action.label}.", pause=0.0)

    def _pause(self, seconds: float) -> None:
        if self.verbose and seconds > 0:
            time.sleep(seconds)

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
