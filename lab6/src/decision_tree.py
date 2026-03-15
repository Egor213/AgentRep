class DecisionTree:
    """
    Дерево решений состоит из узлов 3 видов:
    - exec-узел: имеет функцию exec(mgr, state) и поле next
    - condition-узел: имеет condition(mgr, state), trueCond, falseCond
    - command-узел: имеет command(mgr, state), возвращает команду
    """

    def __init__(self, tree: dict):
        self.tree = tree

    @property
    def state(self):
        return self.tree["state"]

    def execute(self, mgr):
        return self._run(mgr, "root")

    def _run(self, mgr, node_name: str):
        node = self.tree[node_name]

        # Узел exec - устанавливает action для обработки и переходит к след узлу
        if "exec" in node:
            node["exec"](mgr, self.state)
            return self._run(mgr, node["next"])

        # Узел condition - проверяет условие, и выбирает правильный узел
        if "condition" in node:
            cond = node["condition"](mgr, self.state)
            if cond:
                return self._run(mgr, node["trueCond"])
            else:
                return self._run(mgr, node["falseCond"])

        # Узел command - возвращает команду для выполнения
        if "command" in node:
            return node["command"](mgr, self.state)

        raise ValueError(f"Узел {node_name} не содержит exec/condition/command")
