class CtrlLow:
    def __init__(self):
        pass

    def execute(self, input_data, controllers):
        # input_data is from server (via Taken)
        # We need to compute canKick here
        if input_data.get("ball") and input_data["ball"]["dist"] < 0.5:
            input_data["canKick"] = True
        else:
            input_data["canKick"] = False
            
        if controllers:
            next_ctrl = controllers[0]
            return next_ctrl.execute(input_data, controllers[1:])
        return None
