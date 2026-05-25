"""Experimento: MinimaxAgent (Nivel 3) vs HeuristicAgent (Nivel 2).

Uso:
    python scripts/run_minimax_experiment.py
    python scripts/run_minimax_experiment.py --battles 50 --depth 2 --team-size 4
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.agents import HeuristicAgent, MinimaxAgent
from backend.battle import BattleEngine, BattleState, build_random_team
from backend.config import MANUAL_WEIGHTS

_RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def run(battles: int, depth: int, team_size: int, seed: int) -> None:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    minimax = MinimaxAgent(
        name="Minimax",
        depth=depth,
        weights=list(MANUAL_WEIGHTS),
    )
    heuristic = HeuristicAgent(name="Heuristic")

    wins_minimax = wins_heuristic = draws = 0
    rows: list[dict] = []

    print(f"\nExperimento: Minimax(depth={depth}) vs Heuristic  |  {battles} batallas\n")

    for i in range(battles):
        battle_rng = random.Random(rng.randint(0, 1_000_000))
        minimax._sim_rng = random.Random(battle_rng.randint(0, 1_000_000))

        team1 = build_random_team("Minimax", team_size, battle_rng)
        team2 = build_random_team("Heuristic", team_size, battle_rng)
        state = BattleState(team1, team2)
        engine = BattleEngine(state, [minimax, heuristic], rng=battle_rng)
        result = engine.run()

        d = minimax.last_choice_details or {}
        row = {
            "battle_id": i + 1,
            "winner": result.winner,
            "turns": result.turns,
            "nodes_evaluated": d.get("nodes_evaluated", 0),
            "nodes_pruned": d.get("nodes_pruned", 0),
            "transposition_hits": d.get("transposition_hits", 0),
            "time_taken": d.get("time_taken", 0),
        }
        rows.append(row)

        if result.winner == "Minimax":
            wins_minimax += 1
        elif result.winner == "Heuristic":
            wins_heuristic += 1
        else:
            draws += 1

        print(
            f"  [{i+1:3d}] {result.winner:<12} | turnos={result.turns:3d} "
            f"| nodos={row['nodes_evaluated']:5d} | podados={row['nodes_pruned']:4d}"
        )

    total = battles
    print(f"\n{'='*55}")
    print(f"  Minimax:   {wins_minimax:3d} victorias ({wins_minimax/total*100:.1f}%)")
    print(f"  Heuristic: {wins_heuristic:3d} victorias ({wins_heuristic/total*100:.1f}%)")
    print(f"  Empates:   {draws:3d}")

    csv_path = _RESULTS_DIR / f"minimax_metrics_depth{depth}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n✓ Métricas exportadas: {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimento Minimax vs Heuristic")
    parser.add_argument("--battles", type=int, default=30)
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--team-size", type=int, default=3)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    run(battles=args.battles, depth=args.depth, team_size=args.team_size, seed=args.seed)


if __name__ == "__main__":
    main()
