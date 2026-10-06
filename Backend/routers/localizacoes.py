import segno
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from banco import get_db
from models import Item, Localizacao
from schemas import ItemSaida, LocalizacaoEntrada, LocalizacaoSaida, QrCodeItem, respostas


router = APIRouter(prefix="/localizacoes", tags=["Localizações"])


def buscar_localizacao(db: Session, id: int) -> Localizacao:
    localizacao = db.get(Localizacao, id)
    if localizacao is None:
        raise HTTPException(404, "Localização não encontrada.")
    return localizacao


def preencher(localizacao: Localizacao, dados: LocalizacaoEntrada) -> None:
    valores = dados.model_dump()
    valores["estado"] = dados.estado.upper()
    valores["tipo_endereco"] = dados.tipo_endereco.value
    for campo, valor in valores.items():
        setattr(localizacao, campo, valor)


def itens_da_localizacao(db: Session, id: int):
    buscar_localizacao(db, id)
    return db.scalars(select(Item).where(Item.id_localizacao == id).order_by(Item.id)).all()


# Rotas com segmento fixo (/all) são registradas antes de /{id}.
@router.get("/all", response_model=list[LocalizacaoSaida], responses=respostas(), summary="Listar localizações",
            description="Item 14 da lista, originalmente escrito /localizacoes/{all}. A palavra all é fixa nesta implementação. Retorna as localizações por ID crescente; [] se não houver nenhuma.")
def listar_localizacoes(db: Session = Depends(get_db)):
    return db.scalars(select(Localizacao).order_by(Localizacao.id)).all()


@router.get("/{id}/itens/all", response_model=list[ItemSaida], responses=respostas(404),
            summary="Listar itens de uma localização",
            description="Item 19 da lista, originalmente escrito /localizacoes/{id}/itens/{all}. Retorna os itens do patrimônio armazenados na localização; [] se não houver nenhum. Localização inexistente retorna 404.")
def listar_itens(id: int, db: Session = Depends(get_db)):
    return itens_da_localizacao(db, id)


@router.get("/{id}/qrcode/all", response_model=list[QrCodeItem], responses=respostas(404),
            summary="Gerar QR Codes dos itens de uma localização",
            description="Item 20 da lista, originalmente escrito /localizacoes/{id}/qrcode/{all}. Para cada item da localização, retorna o QR Code do `codigoUnico` como imagem SVG em data URI. [] se não houver itens. Localização inexistente retorna 404.")
def listar_qrcodes(id: int, db: Session = Depends(get_db)):
    return [
        {"item_id": i.id, "codigoUnico": i.codigoUnico, "nome": i.nome,
         "qrcode": segno.make(i.codigoUnico, error="m").svg_data_uri(scale=4)}
        for i in itens_da_localizacao(db, id)
    ]


@router.get("/{id}", response_model=LocalizacaoSaida, responses=respostas(404), summary="Consultar localização por ID",
            description="Item 15 da lista. ID inexistente retorna 404; ID não inteiro retorna 422.")
def consultar_localizacao(id: int, db: Session = Depends(get_db)):
    return buscar_localizacao(db, id)


@router.post("", status_code=201, response_model=LocalizacaoSaida, responses=respostas(), summary="Cadastrar localização",
             description="Item 16 da lista. Retorna 201 com a localização criada. CEP com 8 dígitos e estado com 2 letras (gravado em maiúsculas); tipo de endereço padrão: Entrega.")
def criar_localizacao(dados: LocalizacaoEntrada, db: Session = Depends(get_db)):
    localizacao = Localizacao()
    preencher(localizacao, dados)
    db.add(localizacao)
    db.commit()
    db.refresh(localizacao)
    return localizacao


@router.put("/{id}", response_model=LocalizacaoSaida, responses=respostas(404), summary="Atualizar localização",
            description="Item 17 da lista. Substitui todos os campos da localização; envie o cadastro completo. ID inexistente retorna 404.")
def atualizar_localizacao(id: int, dados: LocalizacaoEntrada, db: Session = Depends(get_db)):
    localizacao = buscar_localizacao(db, id)
    preencher(localizacao, dados)
    db.commit()
    db.refresh(localizacao)
    return localizacao


@router.delete("/{id}", status_code=204, response_class=Response, responses=respostas(404, 409),
               summary="Excluir localização",
               description="Item 18 da lista. Exclui definitivamente a localização e retorna 204 sem conteúdo. ID inexistente retorna 404. Localização com itens vinculados retorna 409, pois a cascata do modelo apagaria os itens do patrimônio.")
def excluir_localizacao(id: int, db: Session = Depends(get_db)):
    localizacao = buscar_localizacao(db, id)
    if db.scalar(select(Item.id).where(Item.id_localizacao == id).limit(1)) is not None:
        raise HTTPException(409, "Localização possui itens vinculados e não pode ser excluída.")
    db.delete(localizacao)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Localização possui vínculos que impedem a exclusão.")
    return Response(status_code=204)
