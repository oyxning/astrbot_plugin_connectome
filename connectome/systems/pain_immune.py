class PainImmune:
    def __init__(self, state: dict):
        self.state = state

    def load(self) -> float:
        return min(2.0, float(self.state.get("nociception", 0.0)) + 0.5 * float(self.state.get("inflammation", 0.0)))

    def sensorimotor_penalty(self) -> float:
        return 1.0 - 0.3 * self.load()

    def update(self, values: dict):
        self.state.update(values or {})
