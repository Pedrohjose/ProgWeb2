from io import BytesIO
from urllib.parse import quote
import qrcode
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.pedro_comum import NaoEncontrado, Erro, PNGResponse, get_db
from models import pedro_itens as itens


class QRCodeSaida(BaseModel):
    codigo: str
    itemId: int
    url: str


def _svc_imagem_do_item(db: Session, item_id: int) -> bytes:
    return _svc__imagem(itens._svc_buscar(db, item_id).codigoUnico)


def _svc_imagem_por_codigo(db: Session, codigo: str) -> bytes:
    item = itens._repo_buscar_por_codigo(db, codigo)
    if item is None:
        raise NaoEncontrado("Código não encontrado")
    return _svc__imagem(item.codigoUnico)


def _svc_listar(db: Session) -> list[QRCodeSaida]:
    return [
        QRCodeSaida(
            codigo=item.codigoUnico,
            itemId=item.id,
            url=f"/qrcode/{quote(item.codigoUnico, safe='')}",
        )
        for item in itens._repo_listar(db)
    ]


def _svc__imagem(codigo: str) -> bytes:
    buffer = BytesIO()
    qrcode.make(codigo).save(buffer, format="PNG")
    return buffer.getvalue()


router = APIRouter(prefix="/qrcode", tags=["QR Code"])


@router.get("/all", response_model=list[QRCodeSaida], responses={503: {"model": Erro}},
            summary="Listar códigos QR dos itens")
def listar_qrcodes(db: Session = Depends(get_db)):
    return _svc_listar(db)


@router.get("/{codigo}", response_class=PNGResponse,
            responses={200: {"content": {"image/png": {}}},
                                     404: {"model": Erro}, 503: {"model": Erro}},
            summary="Consultar QR Code pelo código")
def obter_qrcode(codigo: str, db: Session = Depends(get_db)):
    return PNGResponse(_svc_imagem_por_codigo(db, codigo))
