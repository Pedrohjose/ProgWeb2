from io import BytesIO
from urllib.parse import quote

import qrcode
from sqlalchemy.orm import Session

from models.pedro_erros import NaoEncontrado
from models import pedro_repo_itens as repo
from models.pedro_schemas import QRCodeSaida
from models import pedro_servico_itens as itens


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
