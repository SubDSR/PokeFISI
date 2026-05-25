"""Módulo legacy. Usar backend.agents.labels en código nuevo."""
from backend.agents.labels import AGENT_DISPLAY_NAMES, build_agent_labels  # noqa: F401

__all__ = ["AGENT_DISPLAY_NAMES", "build_agent_labels"]
