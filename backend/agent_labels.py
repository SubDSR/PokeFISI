from __future__ import annotations


AGENT_DISPLAY_NAMES = {
    "human": "Jugador",
    "random": "IA Random",
    "heuristic": "IA Heuristic",
}


def build_agent_labels(agent1_name: str, agent2_name: str) -> tuple[str, str]:
    labels = [AGENT_DISPLAY_NAMES[agent1_name], AGENT_DISPLAY_NAMES[agent2_name]]
    if labels[0] == labels[1]:
        return (f"{labels[0]} 1", f"{labels[1]} 2")
    return tuple(labels)
