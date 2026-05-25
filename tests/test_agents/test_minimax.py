"""Tests para el agente Minimax."""

import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.agents.minimax_agent import MinimaxAgent
from backend.battle import build_random_team
from backend.battle.state import BattleState


def _setup_state(seed: int = 42, team_size: int = 3):
    rng = random.Random(seed)
    team1 = build_random_team("P0", team_size, rng)
    team2 = build_random_team("P1", team_size, rng)
    return BattleState(team1, team2)


class TestMinimaxAgent:
    def test_returns_legal_action(self):
        state = _setup_state()
        legal = state.get_legal_actions(0)
        agent = MinimaxAgent(depth=1)
        action = agent.choose_action(state, 0, legal)
        assert action in legal

    def test_does_not_modify_state(self):
        state = _setup_state()
        hp_before = state.teams[0].pokemons[0].hp
        legal = state.get_legal_actions(0)
        agent = MinimaxAgent(depth=2)
        agent.choose_action(state, 0, legal)
        assert state.teams[0].pokemons[0].hp == hp_before, "Minimax no debe modificar el estado real"

    def test_telemetry_populated(self):
        state = _setup_state()
        legal = state.get_legal_actions(0)
        agent = MinimaxAgent(depth=1)
        agent.choose_action(state, 0, legal)
        d = agent.last_choice_details
        assert "nodes_evaluated" in d
        assert "nodes_pruned" in d
        assert "time_taken" in d
        assert d["nodes_evaluated"] >= 1

    def test_player_index_1(self):
        """El agente debe funcionar correctamente jugando como player 1."""
        state = _setup_state()
        legal = state.get_legal_actions(1)
        agent = MinimaxAgent(depth=1)
        action = agent.choose_action(state, 1, legal)
        assert action in legal

    def test_transposition_table_hits(self):
        state = _setup_state()
        legal = state.get_legal_actions(0)
        agent = MinimaxAgent(depth=2, enable_transposition_table=True)
        agent.choose_action(state, 0, legal)
        # No assertion on count, just verify it runs without error
        assert agent.last_choice_details["transposition_hits"] >= 0

    def test_depth_2_more_nodes_than_depth_1(self):
        state = _setup_state(seed=7)
        legal = state.get_legal_actions(0)

        agent1 = MinimaxAgent(depth=1, enable_transposition_table=False)
        agent1.choose_action(state, 0, legal)
        nodes_d1 = agent1.last_choice_details["nodes_evaluated"]

        agent2 = MinimaxAgent(depth=2, enable_transposition_table=False)
        agent2.choose_action(state, 0, legal)
        nodes_d2 = agent2.last_choice_details["nodes_evaluated"]

        assert nodes_d2 >= nodes_d1, "Mayor profundidad debe evaluar más nodos"


class TestAgentLabels:
    def test_build_agent_labels_different(self):
        from backend.agents.labels import build_agent_labels
        l1, l2 = build_agent_labels("random", "heuristic")
        assert l1 != l2

    def test_build_agent_labels_same(self):
        from backend.agents.labels import build_agent_labels
        l1, l2 = build_agent_labels("random", "random")
        assert "1" in l1
        assert "2" in l2

    def test_minimax_in_display_names(self):
        from backend.agents.labels import AGENT_DISPLAY_NAMES
        assert "minimax" in AGENT_DISPLAY_NAMES
        assert "minimax-optimized" in AGENT_DISPLAY_NAMES

    def test_legacy_import_still_works(self):
        """El shim de compatibilidad debe seguir funcionando."""
        from backend.agent_labels import build_agent_labels
        l1, l2 = build_agent_labels("random", "heuristic")
        assert l1 and l2
