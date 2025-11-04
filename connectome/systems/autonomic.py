class Autonomic:
    def __init__(self, state: dict):
        self.state = state

    def sympathetic_drive(self) -> float:
        return 0.8 + 0.4 * float(self.state.get("sympathetic", 1.0))

    def parasympathetic_brake(self) -> float:
        return max(0.6, 0.8 + 0.4 * float(self.state.get("parasympathetic", 1.0)))

    def update(self, values: dict):
        self.state.update(values or {})
