class Development:
    def __init__(self, state: dict):
        self.state = state

    def update(self, values: dict):
        self.state.update(values or {})
