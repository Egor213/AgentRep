
class Controller:
    def __init__(self, actions: list[dict] = None):
        self.actions = actions or []
        self.current_idx = 0

    @property
    def current_action(self) -> dict | None:
        if not self.actions or self.current_idx >= len(self.actions):
            return None
        return self.actions[self.current_idx]

    def next_action(self):
        self.current_idx += 1
        if self.current_idx >= len(self.actions):
            self.current_idx = 0
        print(f"переход к действию {self.current_idx}: {self.current_action}")

    def reset(self):
        self.current_idx = 0
        print(f"Сброс контроллера. Текущее действие: {self.current_action}")

    def decide(self, visible_objects: dict, game_on: bool) -> tuple[str, str] | None:
        if not game_on:
            return None

        action = self.current_action
        if action is None:
            return None

        act_type = action["act"]

        if act_type == "flag":
            return self._decide_move_to_flag(action, visible_objects)
        elif act_type == "kick":
            return self._decide_kick(action, visible_objects)

        return None

    def _decide_move_to_flag(self, action: dict, visible: dict) -> tuple[str, str]:
        target = action["fl"]

        # Если флаг не видно -> поворачиваемся
        if target not in visible:
            return ("turn", "60")

        obj = visible[target]
        dist = obj["dist"]
        direction = obj["dir"]

        if dist < 3.0:
            self.next_action()
            # return self.decide(visible, True)
            return None

        # Если флаг далеко -> поворачиваемся и бежим
        if abs(direction) > 10:
            return ("turn", str(int(direction)))
        else:
            return ("dash", "100")

    def _decide_kick(self, action: dict, visible: dict) -> tuple[str, str]:
        ball_key = action["fl"]
        goal_key = action.get("goal", "gr")

        # Если мяч не видно -> повернуться
        if ball_key not in visible:
            return ("turn", "60")

        ball = visible[ball_key]
        ball_dist = ball["dist"]
        ball_dir = ball["dir"]

        if ball_dist > 0.7:
            # Если мяч далеко -> идем к нему
            if abs(ball_dir) > 10:
                return ("turn", str(int(ball_dir)))
            else:
                return ("dash", "100")

        if goal_key in visible:
            goal = visible[goal_key]
            goal_dir = goal["dir"]
            return ("kick", f"100 {int(goal_dir)}")
        else:
            # Если ворота не видны -> слабый удар вбок
            return ("kick", "10 45")