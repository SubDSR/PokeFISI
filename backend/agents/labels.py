"""Nombres de visualización y etiquetas para agentes.

Módulo canónico para metadatos de display de agentes.
"""

from __future__ import annotations

AGENT_DISPLAY_NAMES: dict[str, str] = {
    "human": "Jugador",
    "random": "IA Random",
    "heuristic": "IA Heuristic",
    "minimax": "IA Minimax",
    "minimax-optimized": "IA Sobrevilla",
}


def build_agent_labels(agent1_name: str, agent2_name: str) -> tuple[str, str]:
    """Devuelve los nombres de visualización para los dos agentes.

    Si ambos agentes tienen el mismo nombre, agrega sufijos "1" y "2".
    """
    label1 = AGENT_DISPLAY_NAMES.get(agent1_name, agent1_name)
    label2 = AGENT_DISPLAY_NAMES.get(agent2_name, agent2_name)
    if label1 == label2:
        return (f"{label1} 1", f"{label2} 2")
    return (label1, label2)
