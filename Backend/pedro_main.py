"""Execução independente da parte de Pedro: uvicorn pedro_main:app."""

from fastapi import FastAPI

from pedro_api import incluir_rotas


app = FastAPI(title="ESTOK API - Pedro", version="1.0.0")
incluir_rotas(app)
