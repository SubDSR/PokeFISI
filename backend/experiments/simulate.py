"""Batch simulations for quick preliminary results."""

from __future__ import annotations

import random

from backend.agents import HeuristicAgent, RandomAgent
from backend.battle import BattleEngine, BattleState, build_random_team
from backend.ui import ConsoleBattleUI


def create_agent(agent_name: str, rng: random.Random):
    if agent_name == "random":
        return RandomAgent(rng=rng)
    if agent_name == "heuristic":
        return HeuristicAgent()
    raise ValueError(f"Agente no soportado: {agent_name}")


def run_experiment(
    battles: int = 30,
    team_size: int = 3,
    agent1_name: str = "random",
    agent2_name: str = "random",
    seed: int = 7,
    verbose: bool = False,
) -> dict:
    rng = random.Random(seed)
    wins = {"Jugador 1": 0, "Jugador 2": 0, "Empate": 0}
    turn_counts: list[int] = []

    for _ in range(battles):
        team1 = build_random_team("Jugador 1", team_size, rng)
        team2 = build_random_team("Jugador 2", team_size, rng)
        state = BattleState(team1, team2)
        agents = [create_agent(agent1_name, rng), create_agent(agent2_name, rng)]
        engine = BattleEngine(state, agents, ui=ConsoleBattleUI(verbose=verbose), rng=rng)
        result = engine.run()
        wins[result.winner] = wins.get(result.winner, 0) + 1
        turn_counts.append(result.turns)

    average_turns = sum(turn_counts) / len(turn_counts) if turn_counts else 0.0
    win_rate = {
        player: round(count / battles * 100, 1) if battles else 0.0
        for player, count in wins.items()
    }
    return {
        "battles": battles,
        "team_size": team_size,
        "agent1": agent1_name,
        "agent2": agent2_name,
        "wins": wins,
        "win_rate": win_rate,
        "average_turns": round(average_turns, 2),
    }
