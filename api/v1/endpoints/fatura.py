from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models.fatura_model import FaturaModel
from models.usuario_model import UsuarioModel
from models.cartao_credito_model import CartaoCreditoModel
from schemas.fatura_schema import FaturaSchema, FaturaSchemaUpdate, FaturaSchemaId
from core.deps import get_session, get_current_user
from sqlalchemy.future import select
from typing import List, Optional


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


async def create_fatura_ano(
    db: AsyncSession,
    usuario_logado: UsuarioModel,
    id_cartao_credito: int,
    ano: int,
    data_vencimento_usuario: Optional[date],
    data_fechamento_usuario: Optional[date]
):
    query_cartao_credito = select(CartaoCreditoModel).where(
        CartaoCreditoModel.id_cartao_credito == id_cartao_credito,
        CartaoCreditoModel.id_usuario == usuario_logado.id_usuario
    )
    result_cartao_credito = await db.execute(query_cartao_credito)
    cartao_credito = result_cartao_credito.scalars().one_or_none()

    if not cartao_credito:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Você não tem permissão para criar essa fatura"
        )
    
    # Verificando se já existe uma fatura
    if data_vencimento_usuario is None or data_fechamento_usuario is None:
        print(f"Entrou if create")

        fatura_anterior = await db.execute(
            select(FaturaModel).where(FaturaModel.id_cartao_credito == id_cartao_credito)
        )
        fatura_anterior = fatura_anterior.scalars().one_or_none()

        existe_uma_fatura = True

        if fatura_anterior:
            dia_vencimento = fatura_anterior.data_vencimento.day
            dia_fechamento = fatura_anterior.data_pagamento.day

            # Criar faturas para todos os meses do ano
            for mes in range(1, 13):  # Meses de 1 a 12
                data_vencimento = date(ano, mes, dia_vencimento)
                data_fechamento = date(ano, mes, dia_fechamento)

                nova_fatura = FaturaModel(
                    data_vencimento=data_vencimento,
                    data_fechamento=data_fechamento,
                    id_conta=fatura_anterior.id_conta if existe_uma_fatura else None,
                    id_cartao_credito=id_cartao_credito,
                    fatura_gastos = 0
                )
                db.add(nova_fatura)

    else: 
        print(f"Entrou else create")

        dia_fechamento = data_fechamento_usuario.day
        dia_vencimento = data_vencimento_usuario.day
        existe_uma_fatura = False

        # Criar a partir do mês atual até o final do ano
        mes_atual = date.today().month

        for mes in range(mes_atual, 13):  # Meses a partir do mês atual até 12
            data_vencimento = date(ano, mes, dia_vencimento)
            data_fechamento = date(ano, mes, dia_fechamento)

            nova_fatura = FaturaModel(
                data_vencimento=data_vencimento,
                data_fechamento=data_fechamento,
                id_conta=None, 
                id_cartao_credito=id_cartao_credito,
                fatura_gastos = 0

            )
            db.add(nova_fatura)

    # Salvar todas as faturas criadas na sessão
    try:
        
        await db.commit()
        return cartao_credito
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Erro ao criar as faturas. Verifique os dados fornecidos.')


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

        if fatura_update.data_vencimento:
            fatura.data_vencimento = fatura_update.data_vencimento
        if fatura_update.data_fechamento:
            fatura.data_fechamento = fatura_update.data_fechamento
        if fatura_update.data_pagamento:
            fatura.data_pagamento = fatura_update.data_pagamento
        if fatura_update.id_conta:
            fatura.id_conta = fatura_update.id_conta
        if fatura_update.id_cartao_credito:
            fatura.id_cartao_credito = fatura_update.id_cartao_credito

        try:
            await session.commit()
            return fatura
        except IntegrityError:
            await session.rollback()  # Garantir rollback em caso de erro
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Erro ao atualizar a fatura. Verifique os dados fornecidos.')
        
@router.get('/visualizar/{id_fatura}', response_model=FaturaSchema, status_code=status.HTTP_200_OK)
async def get_fatura(id_fatura: int, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(FaturaModel).join(CartaoCreditoModel).where(
            FaturaModel.id_fatura == id_fatura,
            CartaoCreditoModel.id_usuario == usuario_logado.id_usuario
        )
        result = await session.execute(query)
        fatura = result.scalars().unique().one_or_none()

        if not fatura:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fatura não encontrada ou não pertence ao usuário logado")

        return fatura

   
@router.get('/cartaoCredito/{id_cartao_credito}/fatura', response_model=List[FaturaSchema], status_code=status.HTTP_200_OK)
async def get_faturas_by_cartao(id_cartao_credito: int, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query_cartao_credito = select(CartaoCreditoModel).where(CartaoCreditoModel.id_cartao_credito == id_cartao_credito, CartaoCreditoModel.id_usuario == usuario_logado.id_usuario)
        result_cartao_credito = await session.execute(query_cartao_credito)
        cartao_credito = result_cartao_credito.scalars().one_or_none()

        if not cartao_credito:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartão de crédito não encontrada ou não pertence ao usuário logado")
        
        query_faturas = select(FaturaModel).where(FaturaModel.id_cartao_credito == id_cartao_credito)
        result_faturas = await session.execute(query_faturas)
        faturas = result_faturas.scalars().all()

        return faturas
    
@router.delete('/deletar/{id_fatura}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_fatura(id_fatura: int, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(FaturaModel).join(CartaoCreditoModel).where(
            FaturaModel.id_fatura == id_fatura,
            CartaoCreditoModel.id_usuario == usuario_logado.id_usuario
        )
        result = await session.execute(query)
        fatura = result.scalars().unique().one_or_none()

        if not fatura:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fatura não encontrada ou não pertence ao usuário logado")
        
        await session.delete(fatura)
        await session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)