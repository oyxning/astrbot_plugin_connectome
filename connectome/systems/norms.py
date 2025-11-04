class Norms:
    def __init__(self, state: dict):
        self.state = state

    def legal_bias(self) -> float:
        # 与引擎中一致的小幅偏置实现
        return 0.95 + 0.1 * float(self.state.get("legal", 1.0))

    def social_bias(self) -> float:
        return 0.95 + 0.1 * float(self.state.get("social", 1.0))

    def update(self, values: dict):
        self.state.update(values or {})
