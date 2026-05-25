"""Exporta métricas de múltiples profundidades para análisis comparativo.

Genera:
  - results/minimax_metrics_depth{d}.csv  para d in [1, 2, 3]
  - results/depth_comparison.csv          con resumen de todas las profundidades

Uso:
    python scripts/export_metrics.py
    python scripts/export_metrics.py --depths 1 2 --battles 20
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


def run_depth_experiment(
    depth: int, battles: int, team_size: int, seed: int
) -> tuple[list[dict], dict]:
    rng = random.Random(seed)
    minimax = MinimaxAgent(name="Minimax", depth=depth, weights=list(MANUAL_WEIGHTS))
    heuristic = HeuristicAgent(name="Heuristic")

    rows: list[dict] = []
    wins = losses = draws = 0
    total_nodes = total_pruned = total_time = 0.0

    for i in range(battles):
        battle_rng = random.Random(rng.randint(0, 1_000_000))
        minimax._sim_rng = random.Random(battle_rng.randint(0, 1_000_000))

        team1 = build_random_team("Minimax", team_size, battle_rng)
        team2 = build_random_team("Heuristic", team_size, battle_rng)
        state = BattleState(team1, team2)
        engine = BattleEngine(state, [minimax, heuristic], rng=battle_rng)
        result = engine.run()

        d = minimax.last_choice_details or {}
        nodes = d.get("nodes_evaluated", 0)
        pruned = d.get("nodes_pruned", 0)
        t = d.get("time_taken", 0.0)

        rows.append({
            "battle_id": i + 1,
            "depth": depth,
            "winner": result.winner,
            "turns": result.turns,
            "nodes_evaluated": nodes,
            "nodes_pruned": pruned,
            "pruning_pct": round(pruned / max(1, nodes + pruned) * 100, 1),
            "time_taken": t,
        })
        total_nodes += nodes
        total_pruned += pruned
        total_time += t

        if result.winner == "Minimax":
            wins += 1
        elif result.winner == "Heuristic":
            losses += 1
        else:
            draws += 1

    n = len(rows)
    summary = {
        "depth": depth,
        "battles": n,
        "win_rate": round(wins / n * 100, 1),
        "avg_nodes": round(total_nodes / n),
        "avg_pruned": round(total_pruned / n),
        "avg_pruning_pct": round(total_pruned / max(1, total_nodes + total_pruned) * 100, 1),
        "avg_time_ms": round(total_time / n * 1000, 2),
    }
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--depths", type=int, nargs="+", default=[1, 2])
    parser.add_argument("--battles", type=int, default=20)
    parser.add_argument("--team-size", type=int, default=3)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summaries: list[dict] = []

    for depth in args.depths:
        print(f"\nEjecutando profundidad {depth}...")
        rows, summary = run_depth_experiment(depth, args.battles, args.team_size, args.seed)

        csv_path = _RESULTS_DIR / f"minimax_metrics_depth{depth}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"  ✓ {csv_path}  |  win_rate={summary['win_rate']}%  avg_nodes={summary['avg_nodes']}")
        summaries.append(summary)

    cmp_path = _RESULTS_DIR / "depth_comparison.csv"
    with open(cmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)
    print(f"\n✓ Comparación exportada: {cmp_path}")

    print("\n  depth | win%  | avg_nodos | poda%  | ms/turno")
    print("  " + "-" * 50)
    for s in summaries:
        print(
            f"    {s['depth']}   | {s['win_rate']:5.1f} | {s['avg_nodes']:9d} "
            f"| {s['avg_pruning_pct']:6.1f} | {s['avg_time_ms']:7.2f}"
        )


if __name__ == "__main__":
    main()
