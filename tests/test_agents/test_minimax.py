"""Tests para el agente Minimax."""

import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.agents.minimax_agent import MinimaxAgent
from backend.battle import build_random_team
from backend.battle.damage import calculate_damage
from backend.battle.models import BattleAction, BattleMove, BattlePokemon, TeamState
from backend.battle.simulator import simulate_turn
from backend.battle.state import BattleState


def _setup_state(seed: int = 42, team_size: int = 3):
    rng = random.Random(seed)
    team1 = build_random_team("P0", team_size, rng)
    team2 = build_random_team("P1", team_size, rng)
    return BattleState(team1, team2)


def _move(
    name: str,
    base_power: int,
    move_type: str,
    accuracy: float = 1.0,
    pp: int = 10,
) -> BattleMove:
    return BattleMove(
        id=name.lower().replace(" ", "-"),
        name=name,
        base_power=base_power,
        accuracy=accuracy,
        move_type=move_type,
        description=name,
        max_pp=pp,
        pp=pp,
    )


def _pokemon(
    name: str,
    hp: int,
    attack: int,
    defense: int,
    speed: int,
    pokemon_type: str,
    moves: list[BattleMove],
) -> BattlePokemon:
    return BattlePokemon(
        species_id=name.lower(),
        name=name,
        level=50,
        max_hp=hp,
        hp=hp,
        attack=attack,
        defense=defense,
        speed=speed,
        pokemon_type=pokemon_type,
        moves=moves,
        sprite_front_url="",
        sprite_back_url="",
    )


def _brick_break_case_state(active_index: int = 1) -> BattleState:
    machop = _pokemon(
        "Machop",
        70,
        80,
        50,
        35,
        "fighting",
        [
            _move("Karate Chop", 50, "fighting", pp=25),
            _move("Submission", 80, "fighting", pp=25),
            _move("Brick Break", 75, "fighting", pp=15),
            _move("Rock Slide", 75, "rock", pp=10),
        ],
    )
    meowth = _pokemon(
        "Meowth",
        40,
        45,
        35,
        90,
        "normal",
        [
            _move("Scratch", 40, "normal", pp=35),
            _move("Slam", 80, "normal", pp=20),
            _move("Quick Attack", 40, "normal", pp=30),
            _move("Headbutt", 70, "normal", pp=15),
        ],
    )
    sandshrew = _pokemon(
        "Sandshrew",
        50,
        75,
        85,
        40,
        "ground",
        [
            _move("Bulldoze", 60, "ground", pp=20),
            _move("Rock Throw", 50, "rock", pp=15),
            _move("Rock Slide", 75, "rock", pp=10),
            _move("Scratch", 40, "normal", pp=35),
        ],
    )
    sandshrew.hp = 17
    nidoran = _pokemon(
        "Nidoran M",
        46,
        57,
        40,
        50,
        "poison",
        [
            _move("Sludge Bomb", 90, "poison", pp=10),
            _move("Dig", 80, "ground", pp=10),
            _move("Earthquake", 100, "ground", pp=10),
            _move("Slam", 80, "normal", pp=20),
        ],
    )
    nidoran.hp = 11 if active_index != 2 else 46

    return BattleState(
        TeamState("Jugador", [machop]),
        TeamState("IA Minimax", [meowth, sandshrew, nidoran], active_index=active_index),
    )


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

    def test_quick_score_uses_damage_expected_once(self):
        move = _move("Flame", 40, "fire", accuracy=0.8)
        attacker = _pokemon("Firemon", 50, 50, 40, 30, "fire", [move])
        defender = _pokemon("Grassmon", 60, 40, 40, 20, "grass", [_move("Tackle", 20, "normal")])
        state = BattleState(
            TeamState("P0", [attacker]),
            TeamState("P1", [defender]),
        )
        action = BattleAction("move", 0, "Usar Flame")
        agent = MinimaxAgent(depth=1)

        expected = calculate_damage(attacker, defender, move) * move.accuracy / defender.max_hp

        assert agent._quick_score(state, 0, action) == expected

    def test_critical_knockout_action_is_kept_when_top_k_is_zero(self):
        weak = _move("Tap", 1, "normal")
        ko = _move("Finisher", 120, "fire")
        attacker = _pokemon("Firemon", 50, 100, 40, 30, "fire", [weak, ko])
        defender = _pokemon("Grassmon", 10, 40, 20, 20, "grass", [_move("Tackle", 20, "normal")])
        state = BattleState(
            TeamState("P0", [attacker]),
            TeamState("P1", [defender]),
        )
        actions = [
            BattleAction("move", 0, "Usar Tap"),
            BattleAction("move", 1, "Usar Finisher"),
        ]
        agent = MinimaxAgent(depth=1, top_k_actions=0)

        selected = agent._select_search_actions(state, actions, 0, maximize=True)

        assert actions[1] in selected

    def test_deterministic_simulation_ignores_rng_sampling(self):
        move = _move("Risky", 50, "normal", accuracy=0.5)
        attacker = _pokemon("Attacker", 50, 50, 30, 40, "normal", [move])
        defender = _pokemon("Defender", 50, 30, 30, 20, "normal", [_move("Tackle", 10, "normal")])
        state = BattleState(
            TeamState("P0", [attacker]),
            TeamState("P1", [defender]),
        )
        action = BattleAction("move", 0, "Usar Risky")
        opp_action = BattleAction("move", 0, "Usar Tackle")

        s1 = simulate_turn(state, action, opp_action, random.Random(1), deterministic=True)
        s2 = simulate_turn(state, action, opp_action, random.Random(999), deterministic=True)

        assert s1.team_of(1).active_pokemon.hp == s2.team_of(1).active_pokemon.hp

    def test_forced_switch_prefers_best_evaluated_replacement(self):
        fainted = _pokemon("Fainted", 30, 10, 10, 10, "normal", [_move("Tackle", 10, "normal")])
        fainted.hp = 0
        weak = _pokemon("Weak", 30, 10, 10, 10, "normal", [_move("Tackle", 10, "normal")])
        weak.hp = 1
        strong = _pokemon("Strong", 80, 50, 50, 50, "water", [_move("Water", 40, "water")])
        opponent = _pokemon("Opponent", 40, 20, 20, 20, "fire", [_move("Ember", 20, "fire")])
        state = BattleState(
            TeamState("P0", [fainted, weak, strong]),
            TeamState("P1", [opponent]),
        )
        agent = MinimaxAgent(depth=1)
        agent._player_index = 0

        assert agent._select_forced_switch(state, 0) == 2

    def test_does_not_switch_sandshrew_into_meowth_against_brick_break(self):
        state = _brick_break_case_state(active_index=1)
        legal = state.get_legal_actions(1)
        agent = MinimaxAgent(depth=2)

        action = agent.choose_action(state, 1, legal)

        assert action != BattleAction("switch", 0, "Cambiar a Meowth")

    def test_attacks_when_all_switches_are_bad_against_brick_break(self):
        state = _brick_break_case_state(active_index=1)
        legal = state.get_legal_actions(1)
        agent = MinimaxAgent(depth=2)

        action = agent.choose_action(state, 1, legal)

        assert action.action_type == "move"

    def test_nidoran_uses_earthquake_against_machop_when_no_safe_switch_exists(self):
        state = _brick_break_case_state(active_index=2)
        state.team_of(1).pokemons[0].hp = 0
        state.team_of(1).pokemons[1].hp = 17
        legal = state.get_legal_actions(1)
        agent = MinimaxAgent(depth=2)

        action = agent.choose_action(state, 1, legal)

        assert action.action_type == "move"
        assert state.team_of(1).active_pokemon.moves[action.index].name == "Earthquake"


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
