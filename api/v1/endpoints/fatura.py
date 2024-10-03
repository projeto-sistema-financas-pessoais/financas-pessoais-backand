from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models.fatura_model import FaturaModel
from models.usuario_model import UsuarioModel
from models.cartao_credito_model import CartaoCreditoModel
from schemas.fatura_schema import FaturaSchema, FaturaSchemaUpdate, FaturaSchemaId
from core.deps import get_session, get_current_user
from sqlalchemy.future import select
from typing import List
from sqlalchemy.orm import joinedload


router = APIRouter()

@router.post('/cadastro', status_code=status.HTTP_201_CREATED)
async def create_fatura(
    fatura: FaturaSchema,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    nova_fatura = FaturaModel(
        data_vencimento=fatura.data_vencimento,
        data_fechamento=fatura.data_fechamento,
        data_pagamento=fatura.data_pagamento,
        id_conta=fatura.id_conta,
        id_cartao_credito=fatura.id_cartao_credito
    )

    async with db as session:
        try:
            session.add(nova_fatura)
            await session.commit()
            return nova_fatura
        except IntegrityError:
            await session.rollback()  
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Erro ao criar a fatura. Verifique os dados fornecidos.')

@router.put('/editar/{id_fatura}', response_model=FaturaSchemaId,status_code=status.HTTP_200_OK)
async def put_fatura(
    id_fatura: int,
    fatura_update: FaturaSchemaUpdate,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        query = select(FaturaModel).where(FaturaModel.id_fatura == id_fatura)
        result = await session.execute(query)
        fatura: FaturaModel = result.scalars().unique().one_or_none()

        if not fatura:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fatura não encontrada")

        query_cartao_credito = select(CartaoCreditoModel).where(
            CartaoCreditoModel.id_cartao_credito == fatura.id_cartao_credito,
            CartaoCreditoModel.id_usuario == usuario_logado.id_usuario
        )
        result_cartao_credito = await session.execute(query_cartao_credito)
        cartao_credito = result_cartao_credito.scalars().one_or_none()

        if not cartao_credito:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Você não tem permissão para editar essa fatura"
            )

        if fatura_update.data_vencimento is not None:
            fatura.data_vencimento = fatura_update.data_vencimento
        if fatura_update.data_fechamento is not None:
            fatura.data_fechamento = fatura_update.data_fechamento
        if fatura_update.data_pagamento is not None:
            fatura.data_pagamento = fatura_update.data_pagamento
        if fatura_update.id_conta is not None:
            fatura.id_conta = fatura_update.id_conta
        if fatura_update.id_cartao_credito is not None:
            fatura.id_cartao_credito = fatura_update.id_cartao_credito

        try:
            await session.commit()
            return fatura
        except IntegrityError:
            await session.rollback()  # Garantir rollback em caso de erro
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Erro ao atualizar a fatura. Verifique os dados fornecidos.')
        
@router.get('/visualizar/{id_fatura}', status_code=status.HTTP_200_OK)
async def get_fatura(id_fatura: int, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        # Verifica se a fatura existe
        query = select(FaturaModel).where(FaturaModel.id_fatura == id_fatura)
        result = await session.execute(query)
        fatura = result.scalars().first()

        if not fatura:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fatura não encontrada")

        # Verifica se a fatura pertence ao usuário logado
        if fatura.id_cartao_credito not in [cartao.id_cartao_credito for cartao in usuario_logado.cartoes_credito]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para visualizar esta fatura")

        return fatura

@router.get('/listar', response_model=List[FaturaSchemaId], status_code=status.HTTP_200_OK)
async def list_faturas(db: AsyncSession = Depends(get_session), 
                       usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        # Verifica se o usuário possui cartões de crédito vinculados
        if not usuario_logado.cartoes_credito:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum cartão de crédito encontrado para o usuário.")

        # Consulta para selecionar todas as faturas vinculadas aos cartões de crédito do usuário logado
        query = (select(FaturaModel)
                 .options(joinedload(FaturaModel.cartao_credito))  # Carregar dados relacionados do cartão de crédito
                 .where(FaturaModel.id_cartao_credito.in_(
                    [cartao.id_cartao_credito for cartao in usuario_logado.cartoes_credito]
                 ))
        )
        
        result = await session.execute(query)
        faturas = result.scalars().unique().all()

        # Verifica se há faturas para retornar
        if not faturas:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma fatura encontrada para os cartões de crédito do usuário.")
        
        return faturas
@router.delete('/deletar/{id_fatura}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_fatura(id_fatura: int, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        # Verifica se a fatura existe
        query = select(FaturaModel).where(FaturaModel.id_fatura == id_fatura)
        result = await session.execute(query)
        fatura = result.scalars().first()

        if not fatura:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fatura não encontrada")

        # Verifica se a fatura pertence ao usuário logado
        if fatura.id_cartao_credito not in [cartao.id_cartao_credito for cartao in usuario_logado.cartoes_credito]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para deletar esta fatura")

        await session.delete(fatura)
        await session.commit()
        
        return {"detail": "Fatura deletada com sucesso."}