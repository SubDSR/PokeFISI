from __future__ import annotations

import argparse
import random
from pathlib import Path

from backend.agents import HeuristicAgent, RandomAgent
from backend.battle import BattleEngine, BattleState, build_random_team
from backend.experiments import run_experiment
from backend.server import run_server
from backend.ui import ConsoleBattleUI, ReplayBattleUI


def create_agent(agent_name: str, rng: random.Random):
    if agent_name == "random":
        return RandomAgent(rng=rng)
    if agent_name == "heuristic":
        return HeuristicAgent()
    raise ValueError(f"Agente no soportado: {agent_name}")


def build_ui(args):
    if args.ui == "replay":
        return ReplayBattleUI(output_path=Path(args.replay_output))
    return ConsoleBattleUI(
        verbose=not args.quiet,
        message_delay=args.message_delay,
        decision_delay=args.decision_delay,
    )


def run_single_battle(args) -> None:
    rng = random.Random(args.seed)
    team1 = build_random_team("Jugador", args.team_size, rng)
    team2 = build_random_team("IA", args.team_size, rng)
    state = BattleState(team1, team2)
    agents = [create_agent(args.agent1, rng), create_agent(args.agent2, rng)]
    ui = build_ui(args)
    engine = BattleEngine(state, agents, ui=ui, rng=rng)
    result = engine.run()

    export = getattr(ui, "export", None)
    if export:
        export()

    if args.quiet:
        print(f"Ganador: {result.winner} | Turnos: {result.turns}")
    if args.ui == "replay":
        print(f"Replay visual exportado en: {args.replay_output}")


def run_batch(args) -> None:
    summary = run_experiment(
        battles=args.battles,
        team_size=args.team_size,
        agent1_name=args.agent1,
        agent2_name=args.agent2,
        seed=args.seed,
        verbose=False,
    )
    print("Resumen del experimento")
    print(f"Batallas: {summary['battles']}")
    print(f"Tamano de equipo: {summary['team_size']}")
    print(f"Agentes: {summary['agent1']} vs {summary['agent2']}")
    print(f"Victorias: {summary['wins']}")
    print(f"Win rate: {summary['win_rate']}")
    print(f"Promedio de turnos: {summary['average_turns']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pokefisi - simulador academico de combate")
    parser.add_argument("--mode", choices=["battle", "experiment", "serve"], default="battle")
    parser.add_argument("--ui", choices=["console", "replay"], default="console")
    parser.add_argument("--team-size", type=int, choices=[3, 4], default=3)
    parser.add_argument("--agent1", choices=["random", "heuristic"], default="random")
    parser.add_argument("--agent2", choices=["random", "heuristic"], default="random")
    parser.add_argument("--battles", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--message-delay", type=float, default=0.35)
    parser.add_argument("--decision-delay", type=float, default=1.0)
    parser.add_argument("--replay-output", default="frontend/web/replay_data.js")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser



def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.mode == "serve":
        run_server(host=args.host, port=args.port)
        return
    if args.mode == "experiment":
        run_batch(args)
        return
    run_single_battle(args)


if __name__ == "__main__":
    main()
