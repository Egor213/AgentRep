# ===== FILE: src/hierarchical_controller.py =====

class HierarchicalController:
    """
    Базовый класс для уровня иерархического контроллера.
    Каждый уровень имеет:
    - memory (dict) — индивидуальное хранилище
    - execute(input_data, upper_controllers) — основной метод
    """

    def __init__(self):
        self.memory = {}

    def execute(self, input_data, upper_controllers):
        """
        input_data — данные от нижнего уровня (или от среды для самого нижнего).
        upper_controllers — список контроллеров верхних уровней.
        Возвращает команду (cmd, params) или None.
        """
        result = self.process(input_data)

        if upper_controllers:
            next_ctrl = upper_controllers[0]
            rest = upper_controllers[1:]
            upper_result = next_ctrl.execute(result, rest)
            return self.merge(result, upper_result)

        return self.finalize(result)

    def process(self, input_data):
        """Обработка данных на текущем уровне. Переопределяется в подклассах."""
        return input_data

    def merge(self, own_result, upper_result):
        """Слияние результатов своего уровня и верхнего. Переопределяется."""
        if upper_result:
            return upper_result
        return own_result

    def finalize(self, result):
        """Финализация, если нет верхних уровней."""
        return result