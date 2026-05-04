"""Turn-based battle engine with move and switch resolution."""

from __future__ import annotations

import random

from backend.battle.damage import calculate_damage
from backend.battle.models import BattleAction, BattleResult
from backend.battle.state import BattleState


class BattleEngine:
    def __init__(self, state: BattleState, agents: list, ui=None, rng: random.Random | None = None):
        self.state = state
        self.agents = agents
        self.ui = ui
        self.rng = rng or random.Random()

    def run(self) -> BattleResult:
        if self.ui:
            self.ui.show_battle_intro(self.state)

        while not self.state.battle_over():
            self._resolve_forced_switches()
            if self.state.battle_over():
                break

            if self.ui:
                self.ui.show_turn(self.state)

            actions = [
                self._select_action(player_index)
                for player_index in range(2)
            ]
            ordered_actions = self._sort_actions(actions)

            for player_index, action in ordered_actions:
                if self.state.battle_over():
                    break
                self._execute_action(player_index, action)

            self.state.turn_number += 1

        winner = self.state.winner() or "Empate"
        if self.ui:
            self.ui.show_winner(winner, self.state)
        return BattleResult(winner=winner, turns=self.state.turn_number - 1, log=list(self.state.log))

    def _resolve_forced_switches(self) -> None:
        for player_index in range(2):
            team = self.state.team_of(player_index)
            if team.all_fainted() or not team.active_pokemon.is_fainted():
                continue

            legal_actions = self.state.get_legal_actions(player_index)
            if not legal_actions:
                continue

            chosen_action = self.agents[player_index].choose_action(self.state, player_index, legal_actions)
            if chosen_action.action_type != "switch":
                final_action = legal_actions[0]
            else:
                final_action = chosen_action
            self._call_ui_hook(
                "on_action_selection",
                self.state,
                player_index,
                legal_actions,
                chosen_action,
                final_action,
                getattr(self.agents[player_index], "last_choice_details", None),
                True,
            )
            self._execute_action(player_index, final_action, forced=True)

    def _select_action(self, player_index: int) -> BattleAction:
        legal_actions = self.state.get_legal_actions(player_index)
        if not legal_actions:
            return BattleAction("pass", -1, "Sin acciones")

        chosen_action = self.agents[player_index].choose_action(self.state, player_index, legal_actions)
        final_action = chosen_action if chosen_action in legal_actions else legal_actions[0]
        self._call_ui_hook(
            "on_action_selection",
            self.state,
            player_index,
            legal_actions,
            chosen_action,
            final_action,
            getattr(self.agents[player_index], "last_choice_details", None),
            False,
        )
        return final_action

    def _sort_actions(self, actions: list[BattleAction]) -> list[tuple[int, BattleAction]]:
        orderable_actions = list(enumerate(actions))

        def sort_key(entry: tuple[int, BattleAction]) -> tuple[int, int, float]:
            player_index, action = entry
            priority = 0 if action.action_type == "switch" else 1
            speed = self.state.team_of(player_index).active_pokemon.speed
            return priority, -speed, self.rng.random()

        return sorted(orderable_actions, key=sort_key)

    def _execute_action(self, player_index: int, action: BattleAction, forced: bool = False) -> None:
        if action.action_type == "switch":
            self._execute_switch(player_index, action.index, forced=forced)
            return
        if action.action_type == "move":
            self._execute_move(player_index, action.index)

    def _execute_switch(self, player_index: int, switch_index: int, forced: bool = False) -> None:
        team = self.state.team_of(player_index)
        if switch_index == team.active_index:
            return
        if switch_index < 0 or switch_index >= len(team.pokemons):
            return
        if team.pokemons[switch_index].is_fainted():
            return

        previous = team.active_pokemon.name
        team.active_index = switch_index
        self._call_ui_hook(
            "on_switch",
            self.state,
            player_index,
            previous,
            team.active_pokemon.name,
            forced,
        )
        message = f"{team.trainer_name} cambia de {previous} a {team.active_pokemon.name}."
        if forced:
            message = f"{team.trainer_name} envia a {team.active_pokemon.name} tras una derrota."
        self._log(message)

    def _execute_move(self, player_index: int, move_index: int) -> None:
        attacker_team = self.state.team_of(player_index)
        defender_team = self.state.opponent_of(player_index)
        attacker = attacker_team.active_pokemon
        defender = defender_team.active_pokemon

        if attacker.is_fainted():
            return
        if move_index < 0 or move_index >= len(attacker.moves):
            return

        move = attacker.moves[move_index]

        if self.rng.random() > move.accuracy:
            self._call_ui_hook("on_move", self.state, player_index, move.name, 0, attacker.name, defender.name)
            self._log(f"{attacker.name} usa {move.name} pero falla!")
            return

        damage = calculate_damage(attacker, defender, move)
        defender.hp = max(0, defender.hp - damage)

        self._call_ui_hook(
            "on_move",
            self.state,
            player_index,
            move.name,
            damage,
            attacker.name,
            defender.name,
        )

        self._log(
            f"{attacker_team.trainer_name} usa {move.name} con {attacker.name} y causa {damage} de dano a {defender.name}."
        )
        self._log(f"{defender.name} queda con {defender.hp}/{defender.max_hp} HP.")

        if defender.is_fainted():
            self._call_ui_hook("on_faint", self.state, 1 - player_index, defender.name)
            self._log(f"{defender_team.trainer_name} pierde a {defender.name}.")

    def _log(self, message: str) -> None:
        self.state.log.append(message)
        if self.ui:
            self.ui.log(message)

    def _call_ui_hook(self, hook_name: str, *args) -> None:
        if not self.ui:
            return
        hook = getattr(self.ui, hook_name, None)
        if hook:
            hook(*args)
