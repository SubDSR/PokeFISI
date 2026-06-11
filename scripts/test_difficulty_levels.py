"""Valida los 4 niveles de dificultad de IA simulando batallas.

Compara:
  RandomAgent vs HeuristicAgent vs MinimaxAgent (manual) vs MinimaxAgent (optimized)

Uso:
    python scripts/test_difficulty_levels.py
    python scripts/test_difficulty_levels.py --battles 20 --team-size 3
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.agents import HeuristicAgent, MinimaxAgent, RandomAgent
from backend.battle import BattleEngine, BattleState, build_balanced_teams
from backend.config import MANUAL_WEIGHTS, MINIMAX_DEPTH, MINIMAX_TOP_K_ACTIONS, load_agent_weights


def battle_pair(
    agent1_name: str,
    agent1,
    agent2_name: str,
    agent2,
    battles: int,
    team_size: int,
    seed: int,
) -> dict:
    rng = random.Random(seed)
    wins1 = wins2 = draws = 0

    for _ in range(battles):
        battle_rng = random.Random(rng.randint(0, 1_000_000))
        team1, team2 = build_balanced_teams(agent1_name, agent2_name, team_size, battle_rng)
        state = BattleState(team1, team2)
        if hasattr(agent1, "_sim_rng"):
            agent1._sim_rng = random.Random(battle_rng.randint(0, 1_000_000))
        if hasattr(agent2, "_sim_rng"):
            agent2._sim_rng = random.Random(battle_rng.randint(0, 1_000_000))
        engine = BattleEngine(state, [agent1, agent2], rng=battle_rng)
        result = engine.run()
        if result.winner == agent1_name:
            wins1 += 1
        elif result.winner == agent2_name:
            wins2 += 1
        else:
            draws += 1

    return {
        "agent1": agent1_name,
        "agent2": agent2_name,
        "battles": battles,
        "wins1": wins1,
        "wins2": wins2,
        "draws": draws,
        "winrate1": round(wins1 / battles * 100, 1),
        "winrate2": round(wins2 / battles * 100, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Test de los 4 niveles de dificultad")
    parser.add_argument("--battles", type=int, default=20)
    parser.add_argument("--team-size", type=int, default=3)
    parser.add_argument("--seed", type=int, default=99)
    args = parser.parse_args()

    rng_seed = args.seed

    rng = random.Random(rng_seed)
    lvl1 = RandomAgent(name="Nivel1_Random", rng=rng)
    lvl2 = HeuristicAgent(name="Nivel2_Heuristic")
    lvl3 = MinimaxAgent(
        name="Nivel3_Minimax",
        depth=MINIMAX_DEPTH,
        top_k_actions=MINIMAX_TOP_K_ACTIONS,
        weights=list(MANUAL_WEIGHTS),
    )
    lvl4_weights = load_agent_weights(use_optimized=True)
    lvl4 = MinimaxAgent(
        name="Nivel4_Sobrevilla",
        depth=MINIMAX_DEPTH,
        top_k_actions=MINIMAX_TOP_K_ACTIONS,
        weights=lvl4_weights,
    )

    matchups = [
        ("Nivel1_Random", lvl1, "Nivel2_Heuristic", lvl2),
        ("Nivel2_Heuristic", lvl2, "Nivel3_Minimax", lvl3),
        ("Nivel3_Minimax", lvl3, "Nivel4_Sobrevilla", lvl4),
    ]

    print(f"\n{'='*62}")
    print(f"  VALIDACIÓN DE NIVELES — {args.battles} batallas por par")
    print(f"{'='*62}")
    print(f"  {'Agente 1':<22} vs {'Agente 2':<22}  win%1  win%2")
    print(f"  {'-'*58}")

    for a1name, a1, a2name, a2 in matchups:
        r = battle_pair(a1name, a1, a2name, a2, args.battles, args.team_size, rng_seed)
        print(
            f"  {a1name:<22} vs {a2name:<22}  {r['winrate1']:5.1f}  {r['winrate2']:5.1f}"
        )

    print(f"\n  Esperado: Nivel 1 < Nivel 2 < Nivel 3 <= Nivel 4")
    print(f"  (win% del nivel superior debe ser mayor que el inferior)\n")


if __name__ == "__main__":
    main()
