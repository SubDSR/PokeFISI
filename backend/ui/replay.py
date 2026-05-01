"""Replay exporter that feeds the Gen 3 inspired web battle layout."""

from __future__ import annotations

import json
from pathlib import Path

from backend.battle.state import BattleState
from backend.ui.view_state import build_view_state


class ReplayBattleUI:
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.frames: list[dict] = []

    def show_battle_intro(self, state: BattleState) -> None:
        player_team = state.team_of(0)
        enemy_team = state.team_of(1)
        self._append_frame(
            state,
            frame_type="intro",
            message=f"{player_team.trainer_name} reta a {enemy_team.trainer_name}.",
        )

    def show_turn(self, state: BattleState) -> None:
        self._append_frame(
            state,
            frame_type="turn",
            message=f"Turno {state.turn_number}",
            player_actions=state.get_legal_actions(0),
        )

    def show_winner(self, winner: str, state: BattleState) -> None:
        self._append_frame(
            state,
            frame_type="result",
            message=f"Combate finalizado. Ganador: {winner}",
            animation={"type": "victory", "side": "player" if winner == state.team_of(0).trainer_name else "enemy"},
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
        self._append_frame(
            state,
            frame_type="switch",
            message=message,
            animation={"type": "switch", "side": "player" if player_index == 0 else "enemy"},
            player_actions=state.get_legal_actions(0),
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
        self._append_frame(
            state,
            frame_type="attack",
            message=f"{attacker_name} uso {move_name}. {defender_name} recibe {damage} de dano.",
            animation={
                "type": "attack",
                "side": "player" if player_index == 0 else "enemy",
                "target": "enemy" if player_index == 0 else "player",
            },
            player_actions=state.get_legal_actions(0),
        )

    def on_faint(self, state: BattleState, fainted_player_index: int, pokemon_name: str) -> None:
        self._append_frame(
            state,
            frame_type="faint",
            message=f"{pokemon_name} ha caido.",
            animation={"type": "faint", "side": "player" if fainted_player_index == 0 else "enemy"},
            player_actions=state.get_legal_actions(0),
        )

    def log(self, message: str) -> None:
        return

    def export(self) -> None:
        payload = {
            "metadata": {
                "style": "pokemon-gen3",
            },
            "frames": self.frames,
        }
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        js_payload = json.dumps(payload, ensure_ascii=True, indent=2)
        self.output_path.write_text(f"window.BATTLE_REPLAY = {js_payload};\n", encoding="utf-8")

    def _append_frame(
        self,
        state: BattleState,
        frame_type: str,
        message: str,
        animation: dict | None = None,
        player_actions=None,
    ) -> None:
        frame = {
            "type": frame_type,
            "animation": animation or {"type": "idle"},
            "state": build_view_state(
                state,
                message=message,
                player_actions=player_actions,
            ),
        }
        self.frames.append(frame)
