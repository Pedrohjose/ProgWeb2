from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from pedro_api.db import get_db
from pedro_api.respostas import PNGResponse
from pedro_api.schemas import Erro, ItemEntrada, ItemSaida
from pedro_api.services import itens, qrcodes

router = APIRouter(prefix="/itens", tags=["Itens"])

ERRO_404 = {404: {"model": Erro}, 503: {"model": Erro}}
ERRO_GRAVACAO = {404: {"model": Erro}, 409: {"model": Erro}, 503: {"model": Erro}}
RESPOSTA_PNG = {200: {"content": {"image/png": {}}}, 404: {"model": Erro}, 503: {"model": Erro}}


@router.get("/all", response_model=list[ItemSaida], responses={503: {"model": Erro}}, summary="Listar itens")
def listar_itens(db: Session = Depends(get_db)):
    return itens.listar(db)


@router.get("/{id}", response_model=ItemSaida, responses=ERRO_404, summary="Consultar item")
def obter_item(id: int, db: Session = Depends(get_db)):
    return itens.buscar(db, id)


@router.post("", response_model=ItemSaida, status_code=status.HTTP_201_CREATED,
             responses=ERRO_GRAVACAO, summary="Cadastrar item")
def criar_item(dados: ItemEntrada, db: Session = Depends(get_db)):
    return itens.criar(db, dados)


@router.put("/{id}", response_model=ItemSaida, responses=ERRO_GRAVACAO, summary="Atualizar item")
def atualizar_item(id: int, dados: ItemEntrada, db: Session = Depends(get_db)):
    return itens.atualizar(db, id, dados)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,
               responses=ERRO_404, summary="Excluir item")
def excluir_item(id: int, db: Session = Depends(get_db)):
    itens.excluir(db, id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}/qrcode", response_class=PNGResponse,
            responses=RESPOSTA_PNG, summary="Consultar QR Code do item")
def obter_qrcode_item(id: int, db: Session = Depends(get_db)):
    return PNGResponse(qrcodes.imagem_do_item(db, id))


@router.post("/{id}/qrcode", response_class=PNGResponse, responses=RESPOSTA_PNG,
             summary="Gerar QR Code do item",
             description="Gera um PNG a partir do código único. O banco atual não armazena a imagem.")
def gerar_qrcode_item(id: int, db: Session = Depends(get_db)):
    return PNGResponse(qrcodes.imagem_do_item(db, id))
