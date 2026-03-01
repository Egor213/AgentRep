class CtrlHigh:
    def __init__(self):
        self.last = "previous"

    def execute(self, input_data, controllers):
        immediate = self.immediate_reaction(input_data)
        if immediate: return immediate
        
        defend = self.defend_goal(input_data)
        if defend: return defend
        
        if self.last == "defend":
            input_data["newAction"] = "return"
        self.last = "previous"
        return None

    def immediate_reaction(self, input_data):
        if input_data.get("canKick"):
            self.last = "kick"
            goal = input_data.get("goal")
            if goal:
                return ("kick", f"110 {int(goal['angle'])}")
            return ("kick", "10 45")
        return None

    def defend_goal(self, input_data):
        ball = input_data.get("ball")
        if ball:
            # Simple defense logic
            self.last = "defend"
            if abs(ball["angle"]) > 5:
                return ("turn", str(int(ball["angle"])))
            return ("dash", "110")
        return None
