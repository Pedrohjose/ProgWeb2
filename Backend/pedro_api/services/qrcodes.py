from io import BytesIO
from urllib.parse import quote

import qrcode
from sqlalchemy.orm import Session

from pedro_api.erros import NaoEncontrado
from pedro_api.repositories import itens as repo
from pedro_api.schemas import QRCodeSaida
from pedro_api.services import itens


def imagem_do_item(db: Session, item_id: int) -> bytes:
    return _imagem(itens.buscar(db, item_id).codigoUnico)


def imagem_por_codigo(db: Session, codigo: str) -> bytes:
    item = repo.buscar_por_codigo(db, codigo)
    if item is None:
        raise NaoEncontrado("Código não encontrado")
    return _imagem(item.codigoUnico)


def listar(db: Session) -> list[QRCodeSaida]:
    return [
        QRCodeSaida(
            codigo=item.codigoUnico,
            itemId=item.id,
            url=f"/qrcode/{quote(item.codigoUnico, safe='')}",
        )
        for item in repo.listar(db)
    ]


def _imagem(codigo: str) -> bytes:
    buffer = BytesIO()
    qrcode.make(codigo).save(buffer, format="PNG")
    return buffer.getvalue()
