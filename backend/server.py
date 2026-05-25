"""Small HTTP server for the Pokefisi frontend and battle API."""

from __future__ import annotations

import json
import mimetypes
import threading
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from backend.session import BattleSession


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_WEB_DIR = PROJECT_ROOT / "frontend" / "web"
FRONTEND_ASSET_DIR = PROJECT_ROOT / "frontend" / "assets"


class SessionStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: dict[str, BattleSession] = {}

    def create(
        self, mode: str, team_size: int, seed: int | None, difficulty: str = "medium"
    ) -> BattleSession:
        session = BattleSession(mode=mode, team_size=team_size, seed=seed, difficulty=difficulty)
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

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._write_json({"status": "ok"})
            return

        if parsed.path == "/":
            self._serve_file(FRONTEND_WEB_DIR / "index.html")
            return

        if parsed.path.startswith("/assets/"):
            relative = parsed.path.removeprefix("/assets/")
            self._serve_file(FRONTEND_ASSET_DIR / relative)
            return

        relative = parsed.path.lstrip("/")
        self._serve_file(FRONTEND_WEB_DIR / relative)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/battle/start":
            payload = self._read_json()
            mode = payload.get("mode", "human-vs-ai")
            team_size = int(payload.get("teamSize", 3))
            seed = payload.get("seed")
            difficulty = payload.get("difficulty", "medium")
            if mode not in {"human-vs-ai", "ai-vs-ai"}:
                self._write_json({"error": "Modo invalido."}, status=HTTPStatus.BAD_REQUEST)
                return
            from backend.config import VALID_DIFFICULTIES
            if difficulty not in VALID_DIFFICULTIES:
                self._write_json(
                    {"error": f"Dificultad invalida. Valores validos: {sorted(VALID_DIFFICULTIES)}"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            session = self.session_store.create(
                mode=mode, team_size=team_size, seed=seed, difficulty=difficulty
            )
            self._write_json(session.start())
            return

        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 4 and parts[:2] == ["api", "battle"]:
            session_id = parts[2]
            action_name = parts[3]
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

        self._write_json({"error": "Ruta no encontrada."}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:
        return

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length else b"{}"
        if not raw_body:
            return {}
        return json.loads(raw_body.decode("utf-8"))

    def _write_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, file_path: Path) -> None:
        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    session_store = SessionStore()
    handler = partial(PokefisiHandler, session_store=session_store)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"Pokefisi disponible en http://{host}:{port}")
    httpd.serve_forever()
