class Ethics:
    def __init__(self, state: dict):
        self.state = state

    def guard_threshold(self) -> float:
        return float(self.state.get("override_guard", 1.5))

    def halt_threshold(self) -> float:
        return float(self.state.get("halt_threshold", 1.5))

    def update(self, values: dict):
        self.state.update(values or {})
