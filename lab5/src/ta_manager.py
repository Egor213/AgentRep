class TAManager:
    def __init__(self, ta_dict):
        self.ta = ta_dict
        self.last_time = 0

    def update(self, taken_data):
        self.inc_timers(taken_data["time"])
        
        # beforeAction
        if "beforeAction" in self.ta["actions"]:
            self.ta["actions"]["beforeAction"](taken_data, self.ta["state"])
            
        return self.execute(taken_data)

    def inc_timers(self, current_time):
        if current_time > self.last_time:
            diff = current_time - self.last_time
            self.last_time = current_time
            for key in self.ta["state"]["timers"]:
                self.ta["state"]["timers"][key] += diff

    def execute(self, taken):
        state = self.ta["state"]
        
        if state.get("synch"):
            # If action was not completed (e.g. multi-step turn)
            # This logic depends on implementation
            cond = state["synch"].rstrip("!")
            return self.ta["actions"][cond](taken, state)

        if state.get("next"):
            if self.ta["current"] in self.ta["nodes"]:
                return self.next_state(taken)
            if self.ta["current"] in self.ta["edges"]:
                return self.next_edge(taken)

        if self.ta["current"] in self.ta["nodes"]:
            return self.execute_state(taken)
        if self.ta["current"] in self.ta["edges"]:
            return self.execute_edge(taken)

        raise ValueError(f"Unexpected state: {self.ta['current']}")

    def next_state(self, taken):
        node_name = self.ta["current"]
        node = self.ta["nodes"][node_name]
        
        for target_node in node["e"]:
            edge_name = f"{node_name}_{target_node}"
            edges = self.ta["edges"].get(edge_name, [])
            if not isinstance(edges, list):
                edges = [edges]
                
            for edge in edges:
                # Check guards
                if "guard" in edge:
                    if not self.check_guards(taken, edge["guard"]):
                        continue
                
                # Check synchronization (condition ?)
                if "synch" in edge and edge["synch"].endswith("?"):
                    cond = edge["synch"].rstrip("?")
                    if not self.ta["actions"][cond](taken, self.ta["state"]):
                        continue
                
                # Found valid edge
                self.ta["current"] = edge_name
                self.ta["state"]["next"] = False
                return self.execute(taken)
        
        # If no edge valid, just stay in state and try to execute its action
        return self.execute_state(taken)

    def next_edge(self, taken):
        # Edge finished, move to target node
        parts = self.ta["current"].split("_")
        self.ta["current"] = parts[1]
        self.ta["state"]["next"] = False
        return self.execute(taken)

    def execute_state(self, taken):
        node_name = self.ta["current"]
        action_func = self.ta["actions"].get(node_name)
        if action_func:
            res = action_func(taken, self.ta["state"])
            if not res and self.ta["state"].get("next"):
                return self.execute(taken)
            return res
        else:
            self.ta["state"]["next"] = True
            return self.execute(taken)

    def execute_edge(self, taken):
        edge_name = self.ta["current"]
        edges = self.ta["edges"][edge_name]
        if not isinstance(edges, list):
            edges = [edges]
            
        # We assume we already picked the right one in next_state
        # But for robustness we can re-check or just pick the first matching
        edge = edges[0] 
        
        # Assignments
        if "assign" in edge:
            for ass in edge["assign"]:
                name = ass["n"]
                val = ass["v"]
                if ass["type"] == "timer":
                    self.ta["state"]["timers"][name] = val
                else:
                    self.ta["state"]["variables"][name] = val
                    
        # Synchronization (!)
        if "synch" in edge and edge["synch"].endswith("!"):
            cond = edge["synch"].rstrip("!")
            res = self.ta["actions"][cond](taken, self.ta["state"])
            if res:
                return res
            
        self.ta["state"]["next"] = True
        return self.execute(taken)

    def check_guards(self, taken, guards):
        for g in guards:
            if not self.evaluate_guard(g):
                return False
        return True

    def evaluate_guard(self, g):
        # g: { s: "lt", l: {v: "dist"}, r: 2 }
        l_val = self.get_ta_val(g["l"])
        r_val = self.get_ta_val(g["r"])
        op = g["s"]
        
        if op == "lt": return l_val < r_val
        if op == "lte": return l_val <= r_val
        if op == "gt": return l_val > r_val
        if op == "gte": return l_val >= r_val
        if op == "eq": return l_val == r_val
        
        return True

    def get_ta_val(self, obj):
        if not isinstance(obj, dict):
            return obj
        if "v" in obj:
            return self.ta["state"]["variables"].get(obj["v"])
        if "t" in obj:
            return self.ta["state"]["timers"].get(obj["t"])
        return obj
