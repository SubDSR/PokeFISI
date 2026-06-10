"""Evaluador de fitness para el algoritmo genético.

Evalúa un vector de pesos W = [W1..W5] ejecutando batallas entre:
  - MinimaxAgent con los pesos candidatos (individuo a evaluar)
  - HeuristicAgent (oponente de referencia)

Fitness = win_rate × 0.7 + margin_score × 0.3
  Rango aproximado: [0, 100+]
"""

from __future__ import annotations

import random

from backend.agents.heuristic_agent import HeuristicAgent
from backend.agents.minimax_agent import MinimaxAgent
from backend.battle import BattleEngine, BattleState, build_balanced_teams
from backend.config import MINIMAX_DEPTH, MINIMAX_TOP_K_ACTIONS


def evaluate_weights(
    weights: list[float],
    n_battles: int = 30,
    team_size: int = 3,
    depth: int = MINIMAX_DEPTH,
    top_k_actions: int = MINIMAX_TOP_K_ACTIONS,
    seed: int = 42,
    verbose: bool = False,
) -> dict:
    """Evalúa un vector de pesos ejecutando batallas contra HeuristicAgent.

    Args:
        weights: Vector [W1, W2, W3, W4, W5] a evaluar.
        n_battles: Número de batallas para reducir varianza.
        team_size: Tamaño de equipo.
        depth: Profundidad Minimax.
        top_k_actions: Número máximo de acciones priorizadas por búsqueda.
        seed: Semilla maestra reproducible.
        verbose: Si True imprime información por batalla.

    Returns:
        Dict con fitness, win_rate, margin_score, wins, losses, draws.
    """
    rng = random.Random(seed)
    minimax_agent = MinimaxAgent(
        name="Candidato",
        depth=depth,
        weights=weights,
        enable_transposition_table=True,
        top_k_actions=top_k_actions,
    )
    heuristic_agent = HeuristicAgent(name="Rival")

    wins = losses = draws = 0
    margins: list[float] = []

    for battle_num in range(n_battles):
        battle_rng = random.Random(rng.randint(0, 1_000_000))
        team1, team2 = build_balanced_teams("Candidato", "Rival", team_size, battle_rng)
        state = BattleState(team1, team2)

        minimax_agent._sim_rng = random.Random(battle_rng.randint(0, 1_000_000))
        agents = [minimax_agent, heuristic_agent]
        engine = BattleEngine(state, agents, rng=battle_rng)

        result = engine.run()
        winner = result.winner

        alive_mine = sum(1 for p in state.teams[0].pokemons if not p.is_fainted())
        alive_opp = sum(1 for p in state.teams[1].pokemons if not p.is_fainted())

        if winner == "Candidato":
            wins += 1
            margins.append(alive_mine - alive_opp)
        elif winner == "Empate":
            draws += 1
            margins.append(0.0)
        else:
            losses += 1
            margins.append(-alive_opp)

        if verbose:
            print(f"  Batalla {battle_num + 1}/{n_battles}: {winner}")

    win_rate = (wins / n_battles) * 100.0
    avg_margin = sum(margins) / len(margins) if margins else 0.0
    margin_score = (avg_margin / max(1, team_size)) * 100.0

    fitness = win_rate * 0.7 + margin_score * 0.3

    return {
        "fitness": round(fitness, 4),
        "win_rate": round(win_rate, 2),
        "margin_score": round(margin_score, 2),
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "n_battles": n_battles,
    }
