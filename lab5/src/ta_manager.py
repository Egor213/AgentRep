class TAManager:
    def __init__(self):
        self.visible = {}
        self.team = ""
        self.side = ""
        self.player_number = 0
        self.time_cycle = 0

    def update(
        self,
        visible_objects: dict,
        team: str = "",
        side: str = "",
        player_number: int = 0,
        time_cycle: int = 0,
    ):
        self.visible = visible_objects
        self.team = team
        self.side = side
        self.player_number = player_number
        self.time_cycle = time_cycle

    def getVisible(self, obj_key: str) -> bool:
        return obj_key in self.visible

    def getDistance(self, obj_key: str) -> float:
        if obj_key in self.visible:
            return self.visible[obj_key].get("dist", 9999)
        return 9999

    def getAngle(self, obj_key: str) -> float:
        if obj_key in self.visible:
            return self.visible[obj_key].get("dir", 0)
        return 0

    def getTeammates(self) -> list:
        teammates = []
        for key, obj in self.visible.items():
            name = obj.get("name", [])
            if not isinstance(name, list) or len(name) < 2:
                continue
            if name[0] == "p" and str(name[1]).strip('"') == self.team:
                if len(name) >= 3:
                    try:
                        num = int(name[2])
                        if num == self.player_number:
                            continue
                    except (ValueError, IndexError):
                        pass
                teammates.append((key, obj))
        return teammates

    def getTeammateCount(self) -> int:
        return len(self.getTeammates())

    def getClosestTeammate(self):
        teammates = self.getTeammates()
        if not teammates:
            return None
        return min(teammates, key=lambda t: t[1].get("dist", 9999))

    def getEnemies(self) -> list:
        enemies = []
        for key, obj in self.visible.items():
            name = obj.get("name", [])
            if not isinstance(name, list) or len(name) < 2:
                continue
            if name[0] == "p" and str(name[1]).strip('"') != self.team:
                enemies.append((key, obj))
        return enemies

    def getClosestEnemy(self):
        enemies = self.getEnemies()
        if not enemies:
            return None
        return min(enemies, key=lambda t: t[1].get("dist", 9999))

    def is_runner(self) -> bool:
        return self.player_number % 2 == 1

    def is_passer(self) -> bool:
        return self.player_number % 2 == 0

    def is_upper_defender(self) -> bool:
        return self.player_number % 2 == 1

    def is_lower_defender(self) -> bool:
        return self.player_number % 2 == 0

    def own_goal_key(self) -> str:
        return "gl" if self.side == "l" else "gr"

    def enemy_goal_key(self) -> str:
        return "gr" if self.side == "l" else "gl"

    def own_penalty_center_flag(self) -> str:
        return "fplc" if self.side == "l" else "fprc"

    def own_goal_top_flag(self) -> str:
        """Верхняя штанга своих ворот"""
        return "fglt" if self.side == "l" else "fgrt"

    def own_goal_bottom_flag(self) -> str:
        """Нижняя штанга своих ворот"""
        return "fglb" if self.side == "l" else "fgrb"

    def teammate_is_closer_to_ball(self) -> bool:
        """Партнёр ближе к мячу чем я?"""
        if not self.getVisible("b"):
            return False
        my_dist = self.getDistance("b")
        closest = self.getClosestTeammate()
        if not closest:
            return False

        teammate_dist = closest[1].get("dist", 9999)
        teammate_dir = closest[1].get("dir", 0)
        ball_dir = self.getAngle("b")

        def norm(a):
            while a > 180: a -= 360
            while a < -180: a += 360
            return a

        angle_diff = abs(norm(teammate_dir - ball_dir))

        if angle_diff < 30 and teammate_dist < my_dist:
            return True
        if teammate_dist + 3 < my_dist:
            return True

        return False
