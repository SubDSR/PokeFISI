"""Ejecuta el algoritmo genético para optimizar los pesos del MinimaxAgent.

Uso:
    python scripts/run_evolution.py
    python scripts/run_evolution.py --generations 100 --pop 50 --battles 30 --depth 4 --top-k 6
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import MINIMAX_DEPTH, MINIMAX_TOP_K_ACTIONS
from backend.experiments.evolution import EvolutionConfig, run_evolution


def _parse_seed(value: str) -> int | None:
    if value.lower() in {"none", "null", "random"}:
        return None
    return int(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Algoritmo Genético — PokeFISI")
    parser.add_argument("--generations", type=int, default=50, help="Número de generaciones")
    parser.add_argument("--pop", type=int, default=30, help="Tamaño de población")
    parser.add_argument("--battles", type=int, default=30, help="Batallas por individuo")
    parser.add_argument("--depth", type=int, default=MINIMAX_DEPTH, help="Profundidad Minimax")
    parser.add_argument("--top-k", type=int, default=MINIMAX_TOP_K_ACTIONS, help="Acciones priorizadas por nodo")
    parser.add_argument("--mutation", type=float, default=0.2, help="Tasa de mutación")
    parser.add_argument("--team-size", type=int, default=3)
    parser.add_argument("--seed", type=_parse_seed, default=42)
    args = parser.parse_args()

    config = EvolutionConfig(
        population_size=args.pop,
        generations=args.generations,
        mutation_rate=args.mutation,
        crossover_rate=0.8,
        elite_percentage=0.15,
        tournament_size=4,
        n_battles_fitness=args.battles,
        minimax_depth=args.depth,
        top_k_actions=args.top_k,
        team_size=args.team_size,
        seed=args.seed,
    )

    print(f"Iniciando evolución con {config.generations} generaciones...")
    print(
        f"Nota: con depth={config.minimax_depth}, top_k={config.top_k_actions} "
        f"y {config.n_battles_fitness} batallas/individuo"
    )
    print(f"      Tiempo estimado: {config.population_size * config.n_battles_fitness * 0.05:.0f}–"
          f"{config.population_size * config.n_battles_fitness * 0.3:.0f}s por generación\n")

    run_evolution(config)


if __name__ == "__main__":
    main()
