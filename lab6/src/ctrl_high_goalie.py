# ===== FILE: src/ctrl_high_goalie.py =====

from hierarchical_controller import HierarchicalController


class CtrlHighGoalie(HierarchicalController):
    """
    Вратарь:
    - Мяч очень близко (< 0.7) → поймать (catch) если можно, иначе отбить
    - Мяч в штрафной (< 20) → бросок к мячу
    - Мяч далеко → следить, стоять у ворот
    
    catch direction — ловит мяч в указанном направлении.
    После catch мяч зафиксирован, следующим действием — kick подальше.
    """

    def __init__(self, side):
        super().__init__()
        self.side = side
        self.last = None
        self.ball_caught = False  # Мяч пойман — нужно выбить

    def process(self, input_data):
        # После поимки — выбить мяч
        if self.ball_caught:
            self.ball_caught = False
            self.last = "kick_after_catch"
            return self._kick_away(input_data)

        # 1. Мяч рядом
        if input_data.get("can_kick"):
            ball = input_data.get("ball")
            if ball:
                ball_dist = ball.get("dist", 9999)
                ball_angle = ball.get("dir", 0)

                # Попробовать поймать (catch работает только в штрафной)
                # catch direction — ловит мяч в направлении angle
                if ball_dist < 2.0:
                    self.last = "catch"
                    self.ball_caught = True
                    return ("catch", str(int(ball_angle)))

            # Мяч совсем рядом но не поймали — отбить
            self.last = "kick"
            return self._kick_away(input_data)

        ball = input_data.get("ball")

        # 2. Мяч виден
        if ball:
            ball_dist = ball.get("dist", 9999)
            ball_angle = ball.get("dir", 0)
            teammate_near = input_data.get("teammate_near_ball", False)

            # Мяч близко — попытаться поймать (бежать к нему)
            if ball_dist < 2.0:
                # Достаточно близко для catch
                self.last = "catch"
                self.ball_caught = True
                return ("catch", str(int(ball_angle)))

            # Мяч в штрафной — бросок
            if ball_dist < 20 and not teammate_near:
                self.last = "defend"
                return {"new_action": "go_to_ball"}

            # Мяч далеко — следить
            if abs(ball_angle) > 5:
                return ("turn", str(int(ball_angle)))

            if self.last == "defend":
                self.last = None
                return {"new_action": "return_home"}

            return ("turn", "0")

        # 3. Мяч не виден
        if self.last == "defend":
            self.last = None
            return {"new_action": "return_home"}

        return ("turn", "40")

    def _kick_away(self, data):
        """Выбить мяч подальше от своих ворот."""
        best_target = data.get("best_pass_target")
        goal_opp = data.get("goal_opp")
        goal_own = data.get("goal_own")

        # Пас тиммейту
        if best_target:
            angle = best_target.get("dir", 0)
            if not self._is_toward_own_goal(angle, goal_own):
                dist = best_target.get("dist", 10)
                power = min(100, int(dist * 5 + 30))
                return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        # В чужие ворота
        if goal_opp:
            angle = goal_opp.get("dir", 0)
            return ("kick", f"100 {int(angle)}")

        # От своих ворот
        if goal_own:
            own_angle = goal_own.get("dir", 0)
            safe_angle = self._opposite_angle(own_angle)
            return ("kick", f"100 {int(safe_angle)}")

        return ("kick", "100 0")

    def _is_toward_own_goal(self, kick_angle, goal_own):
        if not goal_own:
            return False
        own_angle = goal_own.get("dir", 0)
        diff = abs(kick_angle - own_angle)
        if diff > 180:
            diff = 360 - diff
        return diff < 60

    def _opposite_angle(self, angle):
        opposite = angle + 180
        if opposite > 180:
            opposite -= 360
        if opposite < -180:
            opposite += 360
        return opposite