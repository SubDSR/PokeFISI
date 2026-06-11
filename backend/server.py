"""Servidor HTTP para la API de batalla de PokeFISI."""

from __future__ import annotations

import json
import threading
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from backend.session import BattleSession


class SessionStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: dict[str, BattleSession] = {}

    def create(
        self,
        mode: str,
        team_size: int,
        seed: int | None,
        difficulty: str = "medium",
        player_pokemon_ids: list[str] | None = None,
    ) -> BattleSession:
        session = BattleSession(
            mode=mode,
            team_size=team_size,
            seed=seed,
            difficulty=difficulty,
            player_pokemon_ids=player_pokemon_ids,
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> BattleSession | None:
        with self._lock:
            return self._sessions.get(session_id)


class PokefisiHandler(BaseHTTPRequestHandler):
    server_version = "PokefisiHTTP/1.0"

    def __init__(self, *args, session_store: SessionStore, **kwargs):
        self.session_store = session_store
        super().__init__(*args, **kwargs)

    # ── CORS preflight ────────────────────────────────────────────────────────

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._add_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ── GET ───────────────────────────────────────────────────────────────────

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self._write_json({"status": "ok"})
            return

        if parsed.path == "/api/pokemon":
            from backend.ui.serializers import serialize_pokedex
            self._write_json({"pokemon": serialize_pokedex()})
            return

        if parsed.path == "/api/config":
            from backend.ui.serializers import DIFFICULTIES_CONFIG
            self._write_json({"difficulties": DIFFICULTIES_CONFIG, "teamSizes": [3, 4]})
            return

        self._write_json({"error": "Ruta no encontrada."}, status=HTTPStatus.NOT_FOUND)

    # ── POST ──────────────────────────────────────────────────────────────────

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/battle/start":
            self._handle_battle_start()
            return

        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) == 4 and parts[:2] == ["api", "battle"]:
            self._handle_battle_action(parts[2], parts[3])
            return

        self._write_json({"error": "Ruta no encontrada."}, status=HTTPStatus.NOT_FOUND)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _handle_battle_start(self) -> None:
        payload = self._read_json()
        mode = payload.get("mode", "human-vs-ai")
        team_size = int(payload.get("teamSize", 3))
        seed = payload.get("seed")
        difficulty = payload.get("difficulty", "medium")
        player_pokemon_ids: list[str] | None = payload.get("playerPokemonIds")

        if mode not in {"human-vs-ai", "ai-vs-ai"}:
            self._write_json({"error": "Modo invalido."}, status=HTTPStatus.BAD_REQUEST)
            return

        if team_size not in (3, 4):
            self._write_json(
                {"error": "El tamano del equipo debe ser 3 o 4."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        from backend.config import VALID_DIFFICULTIES
        if difficulty not in VALID_DIFFICULTIES:
            self._write_json(
                {"error": f"Dificultad invalida. Valores validos: {sorted(VALID_DIFFICULTIES)}"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        if mode == "human-vs-ai":
            if not player_pokemon_ids or len(player_pokemon_ids) != team_size:
                self._write_json(
                    {"error": f"playerPokemonIds debe tener exactamente {team_size} IDs."},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            if len(set(player_pokemon_ids)) != len(player_pokemon_ids):
                self._write_json(
                    {"error": "playerPokemonIds no debe tener IDs repetidos."},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            from backend.data.pokemon import POKEDEX
            unknown = [pid for pid in player_pokemon_ids if pid not in POKEDEX]
            if unknown:
                self._write_json(
                    {"error": f"IDs desconocidos en POKEDEX: {unknown}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

        session = self.session_store.create(
            mode=mode,
            team_size=team_size,
            seed=seed,
            difficulty=difficulty,
            player_pokemon_ids=player_pokemon_ids if mode == "human-vs-ai" else None,
        )
        self._write_json(session.start())

    def _handle_battle_action(self, session_id: str, action_name: str) -> None:
        session = self.session_store.get(session_id)
        if session is None:
            self._write_json({"error": "Sesion no encontrada."}, status=HTTPStatus.NOT_FOUND)
            return

        try:
            if action_name == "step":
                self._write_json(session.step_ai_turn())
                return
            if action_name == "action":
                payload = self._read_json()
                self._write_json(
                    session.handle_human_action(
                        action_type=payload.get("actionType", ""),
                        index=int(payload.get("index", -1)),
                    )
                )
                return
        except ValueError as exc:
            self._write_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._write_json({"error": "Accion no reconocida."}, status=HTTPStatus.NOT_FOUND)

    # ── Utilidades ────────────────────────────────────────────────────────────

    def log_message(self, format: str, *args) -> None:
        return

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length else b"{}"
        if not raw_body:
            return {}
        return json.loads(raw_body.decode("utf-8"))

    def _add_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _write_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._add_cors_headers()
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    session_store = SessionStore()
    handler = partial(PokefisiHandler, session_store=session_store)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"PokeFISI API disponible en http://{host}:{port}")
    httpd.serve_forever()
