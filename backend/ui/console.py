"""Console visualization with structured, colorized battle logs."""

from __future__ import annotations

import os
import re
import sys
import time

from backend.battle.models import BattleAction
from backend.battle.state import BattleState


class ConsoleBattleUI:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"
    LINE_WIDTH = 78
    ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
    HP_MESSAGE_PATTERN = re.compile(r"^(?P<name>.+) queda con (?P<hp>\d+)/(?P<max_hp>\d+) HP\.$")

    def __init__(
        self,
        verbose: bool = True,
        message_delay: float = 0.35,
        decision_delay: float = 1.0,
        agent_names: list[str] | None = None,
    ):
        self.verbose = verbose
        self.message_delay = max(0.0, message_delay)
        self.decision_delay = max(0.0, decision_delay)
        self.agent_names = agent_names or []
        self.use_color = self._supports_color()
        self._decision_section_open = False
        self._resolution_section_open = False

    def show_battle_intro(self, state: BattleState) -> None:
        team1 = state.team_of(0)
        team2 = state.team_of(1)
        headers = ["Lado", "Entrenador", "Activo", "Equipo"]
        rows = [
            self._team_summary_row(team1, side_label="LADO 1"),
            self._team_summary_row(team2, side_label="LADO 2"),
        ]
        table_width = self._table_width(headers, rows)
        self._emit_blank_line()
        self._emit(self._separator("=", width=table_width), pause=0.0)
        self._emit(self._format_tag("BATTLE", f"{team1.trainer_name} vs {team2.trainer_name}"), pause=0.0)
        self._emit_table(headers, rows)
        self._emit(self._separator("=", width=table_width))
        self._log_random_agent_note()

    def show_turn(self, state: BattleState) -> None:
        team1 = state.team_of(0)
        team2 = state.team_of(1)
        headers = ["Lado", "Entrenador", "Activo", "HP", "ATK", "DEF", "SPD", "Disponibles"]
        rows = [
            self._active_summary_row(team1, side_label="LADO 1"),
            self._active_summary_row(team2, side_label="LADO 2"),
        ]
        alignments = ["left", "left", "left", "left", "right", "right", "right", "right"]
        table_width = self._table_width(headers, rows, alignments=alignments)
        self._decision_section_open = False
        self._resolution_section_open = False
        self._emit_blank_line()
        self._emit(self._separator("-", width=table_width), pause=0.0)
        self.log(f"TURNO {state.turn_number}", kind="TURN", pause=0.0)
        self._emit_table(headers, rows, alignments=alignments)
        self._emit(self._separator("-", width=table_width))

    def show_winner(self, winner: str, state: BattleState) -> None:
        self._emit_blank_line()
        self._emit(self._separator("="), pause=0.0)
        if winner == "Empate":
            self.log(f"Combate finalizado en {state.turn_number - 1} turnos. Resultado: Empate.", kind="DRAW", pause=0.0)
        else:
            self.log(f"Combate finalizado en {state.turn_number - 1} turnos. Ganador: {winner}", kind="WIN", pause=0.0)
        self._emit(self._separator("="))

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
        self._open_decision_section(forced)
        if not self._is_human_agent(player_index):
            context = "cambio forzado" if forced else "seleccion de accion"
            options_label = "opcion" if len(legal_actions) == 1 else "opciones"
            self.log(f"{trainer_name} analiza {len(legal_actions)} {options_label} para {context}.", kind="INFO", pause=0.0)
            self._emit_table(
                ["#", "Tipo", "Accion"],
                [
                    [str(action_index), self._action_kind(action), action.label]
                    for action_index, action in enumerate(legal_actions)
                ],
                alignments=["right", "left", "left"],
            )

            self._pause(self.decision_delay)
            self._describe_agent_choice(trainer_name, legal_actions, proposed_action, decision_details)
        if proposed_action != final_action:
            self.log(
                f"{trainer_name} propuso una accion invalida; se reemplaza por {final_action.label}.",
                kind="ERROR",
                pause=0.0,
            )
        self._pause(self.decision_delay)
        self.log(f"{trainer_name} confirma {final_action.label}.", kind="CHOICE")

    def log(self, message: str, kind: str | None = None, pause: float | None = None) -> None:
        if not self.verbose:
            return
        if kind is None:
            self._open_resolution_section()
        resolved_kind = kind or self._classify_message(message)
        formatted_message = self._format_raw_message(resolved_kind, message)
        self._emit(self._format_tag(resolved_kind, formatted_message), pause=pause)

    def _describe_agent_choice(
        self,
        trainer_name: str,
        legal_actions: list[BattleAction],
        proposed_action: BattleAction,
        decision_details: dict | None,
    ) -> None:
        strategy = decision_details.get("strategy") if decision_details else None
        if strategy == "random":
            self._describe_random_choice(trainer_name, legal_actions, proposed_action, decision_details)
            return
        if strategy == "heuristic":
            self._describe_heuristic_choice(trainer_name, proposed_action, decision_details)
            return
        if proposed_action in legal_actions:
            self.log(f"{trainer_name} selecciona {proposed_action.label}.", kind="INFO", pause=0.0)
            return
        self.log(f"{trainer_name} no devolvio una accion valida.", kind="ERROR", pause=0.0)

    def _describe_random_choice(
        self,
        trainer_name: str,
        legal_actions: list[BattleAction],
        proposed_action: BattleAction,
        decision_details: dict | None,
    ) -> None:
        selected_index = decision_details.get("choice_index") if decision_details else None
        if selected_index is None:
            self.log(f"{trainer_name} no devolvio una accion valida.", kind="ERROR", pause=0.0)
            return

        max_index = len(legal_actions) - 1
        self.log(
            f"{trainer_name} realiza un sorteo uniforme entre 0 y {max_index}; sale [{selected_index}] -> {proposed_action.label}.",
            kind="INFO",
            pause=0.0,
        )

    def _describe_heuristic_choice(
        self,
        trainer_name: str,
        proposed_action: BattleAction,
        decision_details: dict | None,
    ) -> None:
        score = decision_details.get("score") if decision_details else None
        if score is None:
            self.log(f"{trainer_name} prioriza {proposed_action.label} usando heuristicas.", kind="INFO", pause=0.0)
            return
        self.log(
            f"{trainer_name} prioriza {proposed_action.label} usando heuristicas (score: {score}).",
            kind="INFO",
            pause=0.0,
        )

    def _pause(self, seconds: float) -> None:
        if self.verbose and seconds > 0:
            time.sleep(seconds)

    def _emit(self, message: str, pause: float | None = None) -> None:
        if not self.verbose:
            return
        print(message)
        self._pause(self.message_delay if pause is None else pause)

    def _emit_blank_line(self) -> None:
        if self.verbose:
            print()

    def _open_decision_section(self, forced: bool) -> None:
        if self._decision_section_open and not (forced and self._resolution_section_open):
            return
        title = "FASE DE CAMBIOS FORZADOS" if forced else "FASE DE DECISIONES"
        self._emit_blank_line()
        self.log(title, kind="PHASE", pause=0.0)
        self._decision_section_open = True

    def _open_resolution_section(self) -> None:
        if self._resolution_section_open:
            return
        self._emit_blank_line()
        self.log("RESOLUCION DEL TURNO", kind="RESOLVE", pause=0.0)
        self._decision_section_open = False
        self._resolution_section_open = True

    def _log_random_agent_note(self) -> None:
        random_agents = sum(agent_name == "random" for agent_name in self.agent_names)
        if random_agents == 0:
            return
        if random_agents == 1:
            self.log("La IA Random no calcula la mejor jugada: sortea una accion valida por indice.", kind="INFO")
            return
        self.log("Las IAs Random no calculan la mejor jugada: sortean una accion valida por indice.", kind="INFO")

    def _team_summary_row(self, team, side_label: str) -> list[str]:
        return [
            side_label,
            team.trainer_name,
            team.active_pokemon.name,
            ", ".join(pokemon.name for pokemon in team.pokemons),
        ]

    def _active_summary_row(self, team, side_label: str) -> list[str]:
        active = team.active_pokemon
        survivors = sum(not pokemon.is_fainted() for pokemon in team.pokemons)
        return [
            side_label,
            team.trainer_name,
            active.name,
            f"{self._hp_bar(active.hp, active.max_hp)} {active.hp}/{active.max_hp}",
            str(active.attack),
            str(active.defense),
            str(active.speed),
            f"{survivors}/{len(team.pokemons)}",
        ]

    def _action_kind(self, action: BattleAction) -> str:
        if action.action_type == "switch":
            return "SWITCH"
        return "MOVE"

    def _is_human_agent(self, player_index: int) -> bool:
        return player_index < len(self.agent_names) and self.agent_names[player_index] == "human"

    def _hp_bar(self, current_hp: int, max_hp: int, width: int = 16) -> str:
        if max_hp <= 0:
            return "[----------------]"
        ratio = max(0.0, min(1.0, current_hp / max_hp))
        filled = round(ratio * width)
        bar = f"[{'#' * filled}{'-' * (width - filled)}]"
        return self._colorize_hp_bar(bar, ratio)

    def _colorize_hp_bar(self, bar: str, hp_ratio: float) -> str:
        if not self.use_color:
            return bar
        if hp_ratio > 0.5:
            color = self.GREEN
        elif hp_ratio > 0.2:
            color = self.YELLOW
        else:
            color = self.RED
        return f"{color}{bar}{self.RESET}"

    def _classify_message(self, message: str) -> str:
        if "pero falla!" in message:
            return "MISS"
        if "pierde a" in message:
            return "KO"
        if "cambia de" in message or "envia a" in message:
            return "SWITCH"
        if "queda con" in message or "recibe" in message:
            return "HP"
        if "usa" in message and "causa" in message:
            return "MOVE"
        return "INFO"

    def _format_raw_message(self, kind: str, message: str) -> str:
        if kind != "HP":
            return message
        match = self.HP_MESSAGE_PATTERN.match(message)
        if not match:
            return message
        hp = int(match.group("hp"))
        max_hp = int(match.group("max_hp"))
        hp_bar = self._hp_bar(hp, max_hp, width=12)
        return f"{match.group('name')} queda con HP {hp_bar} {hp}/{max_hp}."

    def _format_tag(self, kind: str, message: str) -> str:
        prefix = f"[{kind}]"
        color = self._color_for_kind(kind)
        if color:
            prefix = f"{color}{self.BOLD}{prefix}{self.RESET}"
        return f"{prefix} {message}"

    def _color_for_kind(self, kind: str) -> str:
        if not self.use_color:
            return ""
        return {
            "BATTLE": self.CYAN,
            "TURN": self.MAGENTA,
            "PHASE": self.CYAN,
            "RESOLVE": self.MAGENTA,
            "INFO": self.CYAN,
            "CHOICE": self.YELLOW,
            "MOVE": self.BLUE,
            "MISS": self.RED,
            "SWITCH": self.YELLOW,
            "HP": self.GRAY,
            "KO": self.RED,
            "ERROR": self.RED,
            "WIN": self.GREEN,
            "DRAW": self.YELLOW,
        }.get(kind, self.CYAN)

    def _separator(self, fill: str, width: int | None = None) -> str:
        return self._stylize(fill * (width or self.LINE_WIDTH), self.GRAY)

    def _emit_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        alignments: list[str] | None = None,
    ) -> None:
        for line in self._render_table(headers, rows, alignments=alignments):
            self._emit(line, pause=0.0)

    def _render_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        alignments: list[str] | None = None,
    ) -> list[str]:
        normalized_headers = [str(header) for header in headers]
        normalized_rows = [[str(cell) for cell in row] for row in rows]
        widths = [self._visible_len(header) for header in normalized_headers]

        for row in normalized_rows:
            for index, cell in enumerate(row):
                widths[index] = max(widths[index], self._visible_len(cell))

        border = self._table_border(widths)
        header_row = self._table_row(normalized_headers, widths, alignments)
        lines = [border, self._stylize(header_row, self.BOLD), border]
        lines.extend(self._table_row(row, widths, alignments) for row in normalized_rows)
        lines.append(border)
        return lines

    def _table_width(
        self,
        headers: list[str],
        rows: list[list[str]],
        alignments: list[str] | None = None,
    ) -> int:
        return self._visible_len(self._render_table(headers, rows, alignments=alignments)[0])

    def _table_border(self, widths: list[int]) -> str:
        border = "+-" + "-+-".join("-" * width for width in widths) + "-+"
        return self._stylize(border, self.GRAY)

    def _table_row(self, cells: list[str], widths: list[int], alignments: list[str] | None = None) -> str:
        padded_cells = []
        for index, cell in enumerate(cells):
            align = alignments[index] if alignments and index < len(alignments) else "left"
            padded_cells.append(self._pad_cell(cell, widths[index], align=align))
        return "| " + " | ".join(padded_cells) + " |"

    def _pad_cell(self, value: str, width: int, align: str = "left") -> str:
        padding = max(0, width - self._visible_len(value))
        if align == "right":
            return " " * padding + value
        return value + " " * padding

    def _visible_len(self, value: str) -> int:
        return len(self.ANSI_PATTERN.sub("", value))

    def _stylize(self, text: str, color: str) -> str:
        if not self.use_color:
            return text
        return f"{color}{text}{self.RESET}"

    def _supports_color(self) -> bool:
        if os.environ.get("NO_COLOR"):
            return False
        return bool(getattr(sys.stdout, "isatty", lambda: False)())
