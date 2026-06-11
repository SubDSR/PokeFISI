"""Algoritmo Genético para optimizar los pesos del MinimaxAgent.

Optimiza el vector W = [W1, W2, W3, W4, W5] de la función heurística.

Operadores:
  - Inicialización: uniforme [0, 1] + individuo semilla manual
  - Selección: torneo
  - Cruce: un punto o uniforme
  - Mutación: gaussiana con clamp [0, 1]
  - Elitismo: top elite_percentage pasa intacto

Exporta automáticamente:
  - results/evolution_history.csv
  - results/best_weights.json
  - results/evolution_summary.txt
"""

from __future__ import annotations

import csv
import random
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path

from backend.config import MANUAL_WEIGHTS, MINIMAX_DEPTH, MINIMAX_TOP_K_ACTIONS, save_optimized_weights
from backend.experiments.fitness import evaluate_weights

_RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results"
N_WEIGHTS = 5


@dataclass
class Individual:
    weights: list[float]
    fitness: float = 0.0
    win_rate: float = 0.0

    def __lt__(self, other: "Individual") -> bool:
        return self.fitness < other.fitness


@dataclass
class GenerationStats:
    generation: int
    best_fitness: float
    avg_fitness: float
    best_weights: list[float]
    diversity: float  # desviación estándar del fitness
    time_elapsed: float


@dataclass
class EvolutionConfig:
    population_size: int = 30
    generations: int = 50
    mutation_rate: float = 0.2
    crossover_rate: float = 0.8
    elite_percentage: float = 0.15
    tournament_size: int = 4
    n_battles_fitness: int = 30
    minimax_depth: int = MINIMAX_DEPTH
    top_k_actions: int = MINIMAX_TOP_K_ACTIONS
    team_size: int = 3
    seed: int | None = 42


def _random_individual(rng: random.Random) -> Individual:
    weights = [rng.uniform(0.0, 1.0) for _ in range(N_WEIGHTS)]
    return Individual(weights=weights)


def _tournament_select(population: list[Individual], size: int, rng: random.Random) -> Individual:
    contestants = rng.sample(population, min(size, len(population)))
    return max(contestants, key=lambda ind: ind.fitness)


def _crossover_one_point(
    parent1: Individual, parent2: Individual, rng: random.Random
) -> tuple[Individual, Individual]:
    point = rng.randint(1, N_WEIGHTS - 1)
    w1 = parent1.weights[:point] + parent2.weights[point:]
    w2 = parent2.weights[:point] + parent1.weights[point:]
    return Individual(weights=w1), Individual(weights=w2)


def _crossover_uniform(
    parent1: Individual, parent2: Individual, rng: random.Random
) -> tuple[Individual, Individual]:
    w1, w2 = [], []
    for a, b in zip(parent1.weights, parent2.weights):
        if rng.random() < 0.5:
            w1.append(a)
            w2.append(b)
        else:
            w1.append(b)
            w2.append(a)
    return Individual(weights=w1), Individual(weights=w2)


def _mutate(individual: Individual, mutation_rate: float, rng: random.Random) -> Individual:
    new_weights = []
    for w in individual.weights:
        if rng.random() < mutation_rate:
            w = w + rng.gauss(0.0, 0.1)
            w = max(0.0, min(1.0, w))
        new_weights.append(w)
    return Individual(weights=new_weights)


def _evaluate_individual(
    individual: Individual,
    config: EvolutionConfig,
    battle_seed: int,
) -> None:
    """Evalúa el fitness de un individuo in-place."""
    try:
        result = evaluate_weights(
            weights=individual.weights,
            n_battles=config.n_battles_fitness,
            team_size=config.team_size,
            depth=config.minimax_depth,
            top_k_actions=config.top_k_actions,
            seed=battle_seed,
        )
        individual.fitness = result["fitness"]
        individual.win_rate = result["win_rate"]
    except Exception as exc:
        # Un individuo defectuoso no detiene la evolución
        print(f"  [WARN] Error evaluando individuo: {exc}")
        individual.fitness = 0.0
        individual.win_rate = 0.0


def run_evolution(config: EvolutionConfig | None = None) -> list[GenerationStats]:
    """Ejecuta el algoritmo genético completo.

    Returns:
        Lista de GenerationStats, una por generación.
    """
    cfg = config or EvolutionConfig()
    rng = random.Random(cfg.seed)
    history: list[GenerationStats] = []

    print(f"\n{'='*60}")
    print(f"  ALGORITMO GENÉTICO — PokeFISI MinimaxAgent")
    print(f"  Población: {cfg.population_size}  |  Generaciones: {cfg.generations}")
    print(
        f"  Batallas/individuo: {cfg.n_battles_fitness}  |  "
        f"Profundidad: {cfg.minimax_depth}  |  Top-K: {cfg.top_k_actions}"
    )
    print(f"{'='*60}\n")

    # ── Inicializar población ──────────────────
    population: list[Individual] = [
        Individual(weights=list(MANUAL_WEIGHTS))  # semilla manual
    ]
    # Variaciones cercanas al individuo semilla
    for _ in range(3):
        seed_variant = [max(0.0, min(1.0, w + rng.gauss(0, 0.05))) for w in MANUAL_WEIGHTS]
        population.append(Individual(weights=seed_variant))

    while len(population) < cfg.population_size:
        population.append(_random_individual(rng))

    # ── Evaluación inicial ─────────────────────
    print("Evaluando generación 0 (inicial)...")
    t_gen_start = time.perf_counter()
    for i, ind in enumerate(population):
        battle_seed = rng.randint(0, 1_000_000)
        _evaluate_individual(ind, cfg, battle_seed)
        print(f"  [{i+1}/{cfg.population_size}] fitness={ind.fitness:.2f}  win={ind.win_rate:.1f}%")

    population.sort(reverse=True)
    best_ever = population[0]

    # ── Ciclo evolutivo ────────────────────────
    elite_count = max(1, int(cfg.population_size * cfg.elite_percentage))

    for gen in range(cfg.generations):
        gen_start = time.perf_counter()

        # Elitismo: los mejores pasan intactos
        new_population: list[Individual] = [
            Individual(weights=list(ind.weights), fitness=ind.fitness, win_rate=ind.win_rate)
            for ind in population[:elite_count]
        ]

        # Reproducción
        while len(new_population) < cfg.population_size:
            parent1 = _tournament_select(population, cfg.tournament_size, rng)
            parent2 = _tournament_select(population, cfg.tournament_size, rng)

            if rng.random() < cfg.crossover_rate:
                if rng.random() < 0.5:
                    child1, child2 = _crossover_one_point(parent1, parent2, rng)
                else:
                    child1, child2 = _crossover_uniform(parent1, parent2, rng)
            else:
                child1 = Individual(weights=list(parent1.weights))
                child2 = Individual(weights=list(parent2.weights))

            child1 = _mutate(child1, cfg.mutation_rate, rng)
            child2 = _mutate(child2, cfg.mutation_rate, rng)

            new_population.append(child1)
            if len(new_population) < cfg.population_size:
                new_population.append(child2)

        # Evaluar nuevos individuos (los élites ya tienen fitness)
        for i, ind in enumerate(new_population):
            if ind.fitness > 0:
                continue  # ya evaluado (élite)
            battle_seed = rng.randint(0, 1_000_000)
            _evaluate_individual(ind, cfg, battle_seed)

        new_population.sort(reverse=True)
        population = new_population

        # Actualizar mejor global
        if population[0].fitness > best_ever.fitness:
            best_ever = Individual(
                weights=list(population[0].weights),
                fitness=population[0].fitness,
                win_rate=population[0].win_rate,
            )

        # Estadísticas de la generación
        fitnesses = [ind.fitness for ind in population]
        avg = statistics.mean(fitnesses)
        diversity = statistics.stdev(fitnesses) if len(fitnesses) > 1 else 0.0
        elapsed = time.perf_counter() - gen_start

        stats = GenerationStats(
            generation=gen + 1,
            best_fitness=population[0].fitness,
            avg_fitness=round(avg, 4),
            best_weights=list(population[0].weights),
            diversity=round(diversity, 4),
            time_elapsed=round(elapsed, 2),
        )
        history.append(stats)

        print(
            f"Generación {gen+1:3d}/{cfg.generations} | "
            f"Mejor: {stats.best_fitness:.2f} | "
            f"Promedio: {stats.avg_fitness:.2f} | "
            f"Tiempo: {stats.time_elapsed:.1f}s"
        )

    print(f"\n{'='*60}")
    print(f"  EVOLUCIÓN COMPLETADA")
    print(f"  Mejor fitness: {best_ever.fitness:.4f}")
    print(f"  Win rate:      {best_ever.win_rate:.1f}%")
    print(f"  Pesos:         {[round(w, 4) for w in best_ever.weights]}")
    print(f"{'='*60}\n")

    # ── Exportar resultados ────────────────────
    _export_history(history, cfg)
    save_optimized_weights(
        weights=best_ever.weights,
        fitness=best_ever.fitness,
        generation=cfg.generations,
        win_rate=best_ever.win_rate,
        training_config={
            "population_size": cfg.population_size,
            "generations": cfg.generations,
            "n_battles_fitness": cfg.n_battles_fitness,
            "minimax_depth": cfg.minimax_depth,
            "top_k_actions": cfg.top_k_actions,
            "seed": cfg.seed,
        },
    )
    _export_summary(history, best_ever, cfg)

    return history


def _export_history(history: list[GenerationStats], cfg: EvolutionConfig) -> None:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = _RESULTS_DIR / "evolution_history.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["generation", "best_fitness", "avg_fitness", "best_weights", "diversity", "time_seconds"]
        )
        for s in history:
            writer.writerow([
                s.generation,
                s.best_fitness,
                s.avg_fitness,
                str([round(w, 4) for w in s.best_weights]),
                s.diversity,
                s.time_elapsed,
            ])
    print(f"✓ Historial exportado: {csv_path}")


def _export_summary(
    history: list[GenerationStats], best: Individual, cfg: EvolutionConfig
) -> None:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = _RESULTS_DIR / "evolution_summary.txt"
    lines = [
        "RESUMEN DE EVOLUCIÓN — PokeFISI MinimaxAgent",
        "=" * 50,
        f"Generaciones:    {cfg.generations}",
        f"Población:       {cfg.population_size}",
        f"Batallas/ind:    {cfg.n_battles_fitness}",
        f"Profundidad MM:  {cfg.minimax_depth}",
        f"Top-K acciones:  {cfg.top_k_actions}",
        f"Seed:            {cfg.seed}",
        "",
        f"Mejor fitness:   {best.fitness:.4f}",
        f"Win rate final:  {best.win_rate:.1f}%",
        f"Pesos óptimos:   {[round(w, 4) for w in best.weights]}",
        "",
        "Progresión (cada 10 generaciones):",
    ]
    for s in history:
        if s.generation % 10 == 0 or s.generation == 1:
            lines.append(
                f"  Gen {s.generation:3d} | Mejor {s.best_fitness:.2f} | Prom {s.avg_fitness:.2f}"
            )
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ Resumen exportado: {summary_path}")
