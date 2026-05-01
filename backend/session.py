"""Interactive battle sessions for the web frontend."""

from __future__ import annotations

import random
import uuid

from backend.agents import RandomAgent
from backend.battle import BattleEngine, BattleState, build_random_team
from backend.battle.models import BattleAction
from backend.ui.view_state import build_view_state


class SessionFrameCollector:
    def __init__(self):
        self.frames: list[dict] = []

    def clear(self) -> None:
        self.frames.clear()

    def add_frame(
        self,
        state: BattleState,
        frame_type: str,
        message: str,
        animation: dict | None = None,
        player_actions: list[BattleAction] | None = None,
    ) -> None:
        self.frames.append(
            {
                "type": frame_type,
                "animation": animation or {"type": "idle"},
                "state": build_view_state(
                    state,
                    message=message,
                    player_actions=player_actions,
                ),
            }
        )

    def on_switch(
        self,
        state: BattleState,
        player_index: int,
        previous_name: str,
        incoming_name: str,
        forced: bool,
    ) -> None:
        trainer_name = state.team_of(player_index).trainer_name
        if forced:
            message = f"{trainer_name} envia a {incoming_name}."
        else:
            message = f"{trainer_name} cambia de {previous_name} a {incoming_name}."
        self.add_frame(
            state,
            frame_type="switch",
            message=message,
            animation={"type": "switch", "side": "player" if player_index == 0 else "enemy"},
        )

    def on_move(
        self,
        state: BattleState,
        player_index: int,
        move_name: str,
        damage: int,
        attacker_name: str,
        defender_name: str,
    ) -> None:
        self.add_frame(
            state,
            frame_type="attack",
            message=f"{attacker_name} uso {move_name}. {defender_name} recibe {damage} de dano.",
            animation={
                "type": "attack",
                "side": "player" if player_index == 0 else "enemy",
                "target": "enemy" if player_index == 0 else "player",
            },
        )

    def on_faint(self, state: BattleState, fainted_player_index: int, pokemon_name: str) -> None:
        self.add_frame(
            state,
            frame_type="faint",
            message=f"{pokemon_name} ha caido.",
            animation={"type": "faint", "side": "player" if fainted_player_index == 0 else "enemy"},
        )

    def log(self, message: str) -> None:
        return


class BattleSession:
    def __init__(self, mode: str, team_size: int = 3, seed: int | None = None):
        self.session_id = uuid.uuid4().hex
        self.mode = mode
        self.seed = seed if seed is not None else random.randrange(1, 10_000_000)
        self.rng = random.Random(self.seed)
        self.collector = SessionFrameCollector()

        player_name = "Jugador" if mode == "human-vs-ai" else "IA 1"
        team1 = build_random_team(player_name, team_size, self.rng)
        team2 = build_random_team("IA 2", team_size, self.rng)
        self.state = BattleState(team1, team2)
        self.agents = [self._build_player_agent(), RandomAgent(name="IA 2", rng=self.rng)]
        self.engine = BattleEngine(self.state, self.agents, ui=self.collector, rng=self.rng)

    def start(self) -> dict:
        self.collector.clear()
        self.collector.add_frame(
            self.state,
            frame_type="intro",
            message=f"{self.state.team_of(0).trainer_name} reta a {self.state.team_of(1).trainer_name}.",
        )
        self.collector.add_frame(
            self.state,
            frame_type="prompt",
            message=self._build_prompt(),
            player_actions=self._player_actions_for_view(),
        )
        return self._build_response(self.collector.frames)

    def step_ai_turn(self) -> dict:
        if self.mode != "ai-vs-ai":
            raise ValueError("El modo actual no permite autoejecucion de IA contra IA.")

        return self._play_turn(None)

    def handle_human_action(self, action_type: str, index: int) -> dict:
        if self.mode != "human-vs-ai":
            raise ValueError("El modo actual no admite acciones humanas.")
        if self.state.battle_over():
            return self._build_response([])

        legal_actions = self.state.get_legal_actions(0)
        chosen_action = self._find_legal_action(legal_actions, action_type, index)
        if chosen_action is None:
            raise ValueError("La accion seleccionada no es valida en el estado actual.")

        forced_switch_only = self._human_forced_switch()
        if forced_switch_only:
            self.collector.clear()
            self.engine._execute_action(0, chosen_action, forced=True)
            self._resolve_ai_forced_switches()
            if not self.state.battle_over():
                self.collector.add_frame(
                    self.state,
                    frame_type="prompt",
                    message=self._build_prompt(),
                    player_actions=self._player_actions_for_view(),
                )
            else:
                self._append_result_frame()
            return self._build_response(self.collector.frames)

        return self._play_turn(chosen_action)

    def _play_turn(self, human_action: BattleAction | None) -> dict:
        self.collector.clear()
        self._resolve_ai_forced_switches()
        if self.state.battle_over():
            self._append_result_frame()
            return self._build_response(self.collector.frames)

        if self.mode == "human-vs-ai" and human_action is None:
            raise ValueError("Se requiere una accion humana para este turno.")

        self.collector.add_frame(self.state, frame_type="turn", message=f"Turno {self.state.turn_number}")
        actions = [
            human_action if human_action is not None else self._select_agent_action(0),
            self._select_agent_action(1),
        ]
        ordered_actions = self.engine._sort_actions(actions)
        for player_index, action in ordered_actions:
            if self.state.battle_over():
                break
            self.engine._execute_action(player_index, action)

        self.state.turn_number += 1
        self._resolve_ai_forced_switches()

        if self.state.battle_over():
            self._append_result_frame()
        else:
            self.collector.add_frame(
                self.state,
                frame_type="prompt",
                message=self._build_prompt(),
                player_actions=self._player_actions_for_view(),
            )
        return self._build_response(self.collector.frames)

    def _resolve_ai_forced_switches(self) -> None:
        for player_index in range(2):
            team = self.state.team_of(player_index)
            if team.all_fainted() or not team.active_pokemon.is_fainted():
                continue
            if self.mode == "human-vs-ai" and player_index == 0:
                continue

            legal_actions = self.state.get_legal_actions(player_index)
            if not legal_actions:
                continue

            chosen_action = self._select_agent_action(player_index, legal_actions=legal_actions)
            if chosen_action.action_type != "switch":
                chosen_action = legal_actions[0]
            self.engine._execute_action(player_index, chosen_action, forced=True)

    def _select_agent_action(
        self,
        player_index: int,
        legal_actions: list[BattleAction] | None = None,
    ) -> BattleAction:
        actions = legal_actions or self.state.get_legal_actions(player_index)
        agent = self.agents[player_index]
        if agent is None:
            raise ValueError("El jugador humano no puede ser resuelto automaticamente.")
        return agent.choose_action(self.state, player_index, actions)

    def _build_player_agent(self):
        if self.mode == "human-vs-ai":
            return None
        return RandomAgent(name="IA 1", rng=self.rng)

    def _player_actions_for_view(self) -> list[BattleAction]:
        if self.mode != "human-vs-ai" or self.state.battle_over():
            return []
        return self.state.get_legal_actions(0)

    def _human_forced_switch(self) -> bool:
        legal_actions = self.state.get_legal_actions(0)
        return bool(legal_actions) and all(action.action_type == "switch" for action in legal_actions)

    def _build_prompt(self) -> str:
        if self.state.battle_over():
            winner = self.state.winner() or "Empate"
            return f"La batalla termino. Ganador: {winner}."

        if self.mode == "ai-vs-ai":
            return f"Listo para ejecutar el turno {self.state.turn_number}."

        if self._human_forced_switch():
            return "Tu Pokemon cayo. Elige a quien enviar al combate."

        return "Elige una accion: atacar o cambiar de Pokemon."

    def _append_result_frame(self) -> None:
        winner = self.state.winner() or "Empate"
        winning_side = "player"
        if winner == self.state.team_of(1).trainer_name:
            winning_side = "enemy"
        self.collector.add_frame(
            self.state,
            frame_type="result",
            message=f"Combate finalizado. Ganador: {winner}.",
            animation={"type": "victory", "side": winning_side},
            player_actions=[],
        )

    def _find_legal_action(
        self,
        legal_actions: list[BattleAction],
        action_type: str,
        index: int,
    ) -> BattleAction | None:
        for action in legal_actions:
            if action.action_type == action_type and action.index == index:
                return action
        return None

    def _build_response(self, frames: list[dict]) -> dict:
        current_state = frames[-1]["state"] if frames else build_view_state(
            self.state,
            message=self._build_prompt(),
            player_actions=self._player_actions_for_view(),
        )
        return {
            "sessionId": self.session_id,
            "mode": self.mode,
            "over": self.state.battle_over(),
            "winner": self.state.winner(),
            "requiresHumanAction": self.mode == "human-vs-ai" and not self.state.battle_over(),
            "currentState": current_state,
            "frames": frames,
        }
