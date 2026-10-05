from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.pedro_db import get_db
from models.pedro_respostas import PNGResponse
from models.pedro_schemas import Erro, QRCodeSaida
from models import pedro_servico_qrcodes as qrcodes

router = APIRouter(prefix="/qrcode", tags=["QR Code"])


@router.get("/all", response_model=list[QRCodeSaida], responses={503: {"model": Erro}},
            summary="Listar códigos QR dos itens")
def listar_qrcodes(db: Session = Depends(get_db)):
    return qrcodes.listar(db)


@router.get("/{codigo}", response_class=PNGResponse,
            responses={200: {"content": {"image/png": {}}},
                                     404: {"model": Erro}, 503: {"model": Erro}},
            summary="Consultar QR Code pelo código")
def obter_qrcode(codigo: str, db: Session = Depends(get_db)):
    return PNGResponse(qrcodes.imagem_por_codigo(db, codigo))
