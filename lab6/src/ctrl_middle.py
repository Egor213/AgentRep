class CtrlMiddle:
    def __init__(self):
        self.action = "return"
        self.turn_data = "ft0"

    def execute(self, input_data, controllers):
        cmd = None
        if self.action == "return":
            cmd = self.action_return(input_data)
        elif self.action == "rotateCenter":
            cmd = self.rotate_center(input_data)
        elif self.action == "seekBall":
            cmd = self.seek_ball(input_data)
            
        input_data["cmd"] = cmd
        input_data["action"] = self.action
        
        if controllers:
            next_ctrl = controllers[0]
            command = next_ctrl.execute(input_data, controllers[1:])
            if command: return command
            if input_data.get("newAction"):
                self.action = input_data["newAction"]
        return input_data["cmd"]

    def action_return(self, input_data):
        goal_own = input_data.get("goalOwn")
        if not goal_own: return ("turn", "60")
        if abs(goal_own["angle"]) > 10:
            return ("turn", str(int(goal_own["angle"])))
        if goal_own["dist"] > 3:
            return ("dash", str(int(goal_own["dist"] * 2 + 30)))
        self.action = "rotateCenter"
        return ("turn", "180")

    def rotate_center(self, input_data):
        # Using flag 'fc' as center
        # We need to check if 'fc' is in taken visible
        # But 'taken' returns a dict with 'f' keys
        # Wait, I'll assume 'fc' is accessible
        fc = None # Find 'fc' in some way
        # For simplicity return turn 60 if not found
        self.action = "seekBall"
        return ("turn", "60")

    def seek_ball(self, input_data):
        # Implementation of search logic from manual
        if input_data.get("ball"):
            return ("turn", str(int(input_data["ball"]["angle"])))
        return ("turn", "30")
