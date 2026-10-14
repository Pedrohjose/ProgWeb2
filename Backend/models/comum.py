from fastapi import Response
from pydantic import BaseModel
from banco import get_db


class NaoEncontrado(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class Conflito(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class PNGResponse(Response):
    media_type = "image/png"


class Erro(BaseModel):
    detail: str
