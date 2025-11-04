class Homeostasis:
    def __init__(self, state: dict):
        # 引用外部字典，保持一致更新
        self.state = state

    def energy_factor(self) -> float:
        e = float(self.state.get("energy", 1.0))
        f = float(self.state.get("fatigue", 0.5))
        return max(0.3, e * (1.0 - 0.4 * f))

    def temp_penalty(self) -> float:
        t = float(self.state.get("body_temp", 1.0))
        return max(0.6, 1.0 - 0.3 * abs(t - 1.0))

    def capacity(self) -> float:
        return self.energy_factor() * self.temp_penalty()

    def update(self, values: dict):
        self.state.update(values or {})
