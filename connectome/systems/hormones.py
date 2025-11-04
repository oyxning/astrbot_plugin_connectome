class Hormones:
    def __init__(self, state: dict):
        self.state = state

    def adrenaline_gain(self) -> float:
        return 0.8 + 0.4 * float(self.state.get("adrenaline", 1.0))

    def cortisol_lr_modifier(self) -> float:
        return 1.0 / max(0.6, 0.8 + 0.4 * float(self.state.get("cortisol", 1.0)))

    def oxytocin_dmn_bias(self) -> float:
        return 0.9 + 0.2 * float(self.state.get("oxytocin", 1.0))

    def update(self, values: dict):
        self.state.update(values or {})
