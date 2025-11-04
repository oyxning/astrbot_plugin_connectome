class Circadian:
    def __init__(self, state: dict):
        self.state = state

    def peak_factor(self) -> float:
        phase = float(self.state.get("circadian_phase", 0.5))
        return 1.0 + 0.2 * (1.0 - abs(0.5 - phase) * 2.0)

    def sleep_penalty(self) -> float:
        return max(0.6, 1.0 - 0.3 * float(self.state.get("sleep_pressure", 0.5)))

    def replay_limit_scale(self) -> float:
        return 1.0 + 0.3 * float(self.state.get("sleep_pressure", 0.5))

    def update(self, values: dict):
        self.state.update(values or {})
