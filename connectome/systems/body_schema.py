class BodySchema:
    def __init__(self, state: dict):
        self.state = state

    def motor_cost(self) -> float:
        return float(self.state.get("motor_cost", 1.0))

    def proprio_noise(self) -> float:
        return float(self.state.get("proprioception_noise", 0.5))

    def agency(self) -> float:
        return float(self.state.get("agency", 1.0))

    def update(self, values: dict):
        self.state.update(values or {})
