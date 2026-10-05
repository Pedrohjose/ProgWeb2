class NaoEncontrado(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class Conflito(Exception):
    def __init__(self, detail: str):
        self.detail = detail
