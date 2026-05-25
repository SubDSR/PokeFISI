"""Battle state container and legal action generation."""

from backend.battle.models import BattleAction, TeamState


class BattleState:
    def __init__(self, team1: TeamState, team2: TeamState):
        self.teams = [team1, team2]
        self.turn_number = 1
        self.log: list[str] = []

    def team_of(self, player_index: int) -> TeamState:
        return self.teams[player_index]

    def opponent_of(self, player_index: int) -> TeamState:
        return self.teams[1 - player_index]

    def clone(self) -> "BattleState":
        """Copia profunda independiente del estado actual.

        Los objetos clonados no comparten referencias con el original.
        Usado exclusivamente por el árbol de búsqueda Minimax.
        """
        cloned = BattleState(self.teams[0].clone(), self.teams[1].clone())
        cloned.turn_number = self.turn_number
        cloned.log = list(self.log)
        return cloned

    def battle_over(self) -> bool:
        return any(team.all_fainted() for team in self.teams)

    def winner(self) -> str | None:
        team1_fainted = self.teams[0].all_fainted()
        team2_fainted = self.teams[1].all_fainted()
        if team1_fainted and team2_fainted:
            return "Empate"
        if team2_fainted:
            return self.teams[0].trainer_name
        if team1_fainted:
            return self.teams[1].trainer_name
        return None

    def get_legal_actions(self, player_index: int) -> list[BattleAction]:
        team = self.team_of(player_index)
        if team.all_fainted():
            return []

        actions: list[BattleAction] = []
        if team.active_pokemon.is_fainted():
            for switch_index, pokemon in team.available_switches():
                actions.append(BattleAction("switch", switch_index, f"Cambiar a {pokemon.name}"))
            return actions

        has_moves = False
        for move_index, move in enumerate(team.active_pokemon.moves):
            if move.has_pp():
                actions.append(BattleAction("move", move_index, f"Usar {move.name} (PP: {move.pp}/{move.max_pp})"))
                has_moves = True

        if not has_moves:
            actions.append(BattleAction("struggle", 0, "Struggle"))

        for switch_index, pokemon in team.available_switches():
            actions.append(BattleAction("switch", switch_index, f"Cambiar a {pokemon.name}"))
        return actions
