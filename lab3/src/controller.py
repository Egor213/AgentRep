# ===== FILE: src/controller.py =====

from decision_tree import DecisionTree
from dt_manager import DTManager
from player_dt import create_player_tree
from goalie_dt import create_goalie_tree


class Controller:
    def __init__(self, actions: list[dict] = None, is_goalie: bool = False):
        self.is_goalie = is_goalie
        self.manager = DTManager()

        if is_goalie:
            tree_dict = create_goalie_tree()
        else:
            actions = actions or [
                {"act": "flag", "fl": "frb"},
                {"act": "kick", "fl": "b", "goal": "gr"},
            ]
            tree_dict = create_player_tree(actions)

        self.dt = DecisionTree(tree_dict)

    def reset(self):
        """Сброс после гола."""
        state = self.dt.state
        if "next" in state:
            state["next"] = 0
            if "sequence" in state:
                state["action"] = state["sequence"][0]
        state["command"] = None
        print("Контроллер сброшен")

    def decide(self, visible_objects: dict, game_on: bool,
               team: str = "", side: str = "", player_number: int = 0,
               x=None, y=None) -> tuple[str, str] | None:
        if not game_on:
            return None

        self.manager.update(visible_objects, team, side, player_number, x, y)
        result = self.dt.execute(self.manager)

        if result and isinstance(result, tuple) and len(result) == 2:
            return result
        return None