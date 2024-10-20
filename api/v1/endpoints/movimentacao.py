
import api.v1.endpoints
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy import extract, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from api.v1.endpoints.fatura import create_fatura_ano
from core.utils import handle_db_exceptions
from models.cartao_credito_model import CartaoCreditoModel
from models.divide_model import DivideModel
from models.movimentacao_model import MovimentacaoModel
from models.parente_model import ParenteModel
from schemas.fatura_schema import FaturaSchema, FaturaSchemaId
from schemas.movimentacao_schema import (IdMovimentacaoSchema, MovimentacaoRequestFilterSchema,
    MovimentacaoSchema, MovimentacaoSchemaId, MovimentacaoSchemaList, MovimentacaoSchemaReceitaDespesa,
    MovimentacaoSchemaTransferencia, MovimentacaoSchemaUpdate, ParenteResponse)
from core.deps import get_session, get_current_user
from models.usuario_model import UsuarioModel
from models.conta_model import ContaModel
from models.categoria_model import CategoriaModel
from models.fatura_model import FaturaModel
from typing import List, Optional
from models.repeticao_model import RepeticaoModel
from models.enums import CondicaoPagamento, FormaPagamento, TipoMovimentacao, TipoRecorrencia
from datetime import date, timedelta
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


router = APIRouter()


async def find_fatura(id_cartao_credito: int, data_pagamento: date,   db: AsyncSession):
    
    query = select(FaturaModel).filter(
        FaturaModel.id_cartao_credito == id_cartao_credito,
        extract('month', FaturaModel.data_fechamento) == data_pagamento.month,
        extract('year', FaturaModel.data_fechamento) == data_pagamento.year
    )
    
    result = await db.execute(query)
    fatura = result.scalars().first()
    return fatura

async def get_or_create_fatura(session, usuario_logado, id_financeiro, data_pagamento):
    fatura = await find_fatura(id_financeiro, data_pagamento, session)
    cartao_credito = None 

    if not fatura:
        cartao_credito = await create_fatura_ano(session, usuario_logado, id_financeiro, data_pagamento.year, None, None)
        fatura = await find_fatura(id_financeiro, data_pagamento, session)
        
        if not fatura:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao adicionar fatura")
    
    return fatura, cartao_credito



@router.post('/cadastro/despesa', status_code=status.HTTP_201_CREATED)
async def create_movimentacao(
    movimentacao: MovimentacaoSchemaReceitaDespesa,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        try:
            query_categoria = select(CategoriaModel).where(CategoriaModel.id_categoria == movimentacao.id_categoria, CategoriaModel.id_usuario == usuario_logado.id_usuario)
            result_categoria = await session.execute(query_categoria)
            categoria = result_categoria.scalars().first()

            if not categoria:
                print(f"Categoria {movimentacao.id_categoria} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada ou não pertence ao usuário.")
            # Validação da soma dos valores de parentes
            soma = sum(divide.valor_parente for divide in movimentacao.divide_parente)
            if soma != movimentacao.valor:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Valor total de parentes não pode ser diferente do valor.")
            
            if movimentacao.condicao_pagamento != CondicaoPagamento.PARCELADO:
                movimentacao.quantidade_parcelas = 1


            # Ajuste da conta ou criação de fatura
            if movimentacao.forma_pagamento in [FormaPagamento.DEBITO, FormaPagamento.DINHEIRO]:
                movimentacao.id_conta = movimentacao.id_financeiro
            else:
                movimentacao.consolidado = False
                fatura, cartao_credito = await get_or_create_fatura(session, usuario_logado, movimentacao.id_financeiro, movimentacao.data_pagamento)
                if cartao_credito:
                    print(f"Cartão de Crédito {cartao_credito}")
                else:
                    query_cartao_credito = select(CartaoCreditoModel).where(
                        CartaoCreditoModel.id_cartao_credito == movimentacao.id_financeiro,
                        CartaoCreditoModel.id_usuario == usuario_logado.id_usuario
                    )
                    result_cartao_credito = await db.execute(query_cartao_credito)
                    cartao_credito = result_cartao_credito.scalars().one_or_none()

                    if not cartao_credito:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Você não tem permissão para acessar esse cartão"
                        )

            if movimentacao.id_conta is not None:
                query_conta = select(ContaModel).where(ContaModel.id_conta == movimentacao.id_conta, ContaModel.id_usuario == usuario_logado.id_usuario)
                result_conta = await session.execute(query_conta)
                conta = result_conta.scalars().first()
 
                if not conta:
                    print(f"Conta {movimentacao.id_conta} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada ou não pertence ao usuário.")

            # Preparação para criar movimentações parceladas
            valor_por_parcela = movimentacao.valor / movimentacao.quantidade_parcelas
            valor_por_parcela_ajustado = round(valor_por_parcela, 2)
            valor_restante = round(movimentacao.valor - (valor_por_parcela_ajustado * movimentacao.quantidade_parcelas), 2)
            print(valor_por_parcela, valor_restante, valor_por_parcela_ajustado )

            data_pagamento = movimentacao.data_pagamento

            if movimentacao.condicao_pagamento in [CondicaoPagamento.PARCELADO, CondicaoPagamento.RECORRENTE]:
                
                if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE: 
                    if movimentacao.tipo_recorrencia == TipoRecorrencia.ANUAL:
                        movimentacao.quantidade_parcelas = 2
                    else: 
                        movimentacao.quantidade_parcelas = 8

                nova_repeticao = RepeticaoModel(
                    quantidade_parcelas=movimentacao.quantidade_parcelas,
                    tipo_recorrencia=movimentacao.tipo_recorrencia,
                    valor_total=movimentacao.valor,
                    data_inicio=movimentacao.data_pagamento,
                )
                db.add(nova_repeticao)
                await db.flush()
                await db.refresh(nova_repeticao)
                id_repeticao = nova_repeticao.id_repeticao

            # Criação das movimentações parceladas
            for parcela_atual in range(1, movimentacao.quantidade_parcelas + 1):
                nova_movimentacao = MovimentacaoModel(
                    valor= valor_por_parcela_ajustado + valor_restante if  parcela_atual == 1 else valor_por_parcela_ajustado,
                    descricao=movimentacao.descricao,
                    tipoMovimentacao=TipoMovimentacao.DESPESA,
                    forma_pagamento=movimentacao.forma_pagamento,
                    condicao_pagamento=movimentacao.condicao_pagamento,
                    datatime=movimentacao.datatime,
                    consolidado=movimentacao.consolidado,
                    parcela_atual= str(parcela_atual),
                    data_pagamento=data_pagamento,
                    id_conta=movimentacao.id_conta,
                    id_categoria=movimentacao.id_categoria,
                    id_fatura= fatura.id_fatura if movimentacao.forma_pagamento == FormaPagamento.CREDITO else None,
                    id_repeticao= id_repeticao if movimentacao.condicao_pagamento != CondicaoPagamento.A_VISTA  else None,
                    id_usuario=usuario_logado.id_usuario
                )
                
                
                nova_movimentacao.divisoes = []

                db.add(nova_movimentacao)
                
                if movimentacao.consolidado and parcela_atual == 1:
                    conta.saldo = conta.saldo - Decimal(valor_por_parcela_ajustado + valor_restante)
        
                        
                if movimentacao.forma_pagamento == FormaPagamento.CREDITO:

                    if parcela_atual == 1:
                        cartao_credito.limite_disponivel = cartao_credito.limite_disponivel - valor_por_parcela_ajustado + valor_restante
                        fatura.fatura_gastos +=valor_por_parcela_ajustado + valor_restante
                    elif movimentacao.condicao_pagamento == CondicaoPagamento.PARCELADO:
                        cartao_credito.limite_disponivel = cartao_credito.limite_disponivel - valor_por_parcela_ajustado
                        fatura.fatura_gastos +=valor_por_parcela_ajustado


                # Criação dos relacionamentos com parentes
                for divide in movimentacao.divide_parente:
                    if movimentacao.condicao_pagamento == CondicaoPagamento.PARCELADO:
                        valor_parente = divide.valor_parente / movimentacao.quantidade_parcelas
                        valor_parente_ajustado = round(valor_parente, 2)
                        valor_parente_restante = round(divide.valor_parente - (valor_parente_ajustado * movimentacao.quantidade_parcelas), 2)
                        
                        valor = valor_parente_ajustado + valor_parente_restante if parcela_atual == 1 else valor_parente_ajustado
                        # print(valor_parente, valor_parente_ajustado, valor_parente_restante )

                    else:
                        valor = divide.valor_parente
                        

                    novo_divide_parente = DivideModel(
                        id_parente= divide.id_parente,
                        valor= valor
                    )
                    nova_movimentacao.divisoes.append(novo_divide_parente)


                movimentacao.consolidado = False
                
                if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE:
                    if movimentacao.tipo_recorrencia == TipoRecorrencia.ANUAL:
                        data_pagamento = data_pagamento.replace(year=data_pagamento.year + 1)
                    elif movimentacao.tipo_recorrencia == TipoRecorrencia.QUINZENAL:
                        data_pagamento += timedelta(days=15)
                    elif movimentacao.tipo_recorrencia == TipoRecorrencia.SEMANAL:
                        data_pagamento += timedelta(weeks=1)
                    elif movimentacao.tipo_recorrencia == TipoRecorrencia.MENSAL:
                        if data_pagamento.month == 12:
                            data_pagamento = data_pagamento.replace(year=data_pagamento.year + 1, month=1)
                        else:
                            data_pagamento = data_pagamento.replace(month=data_pagamento.month + 1)
                else:
                    if data_pagamento.month == 12:
                        data_pagamento = data_pagamento.replace(year=data_pagamento.year + 1, month=1)
                    else:
                        data_pagamento = data_pagamento.replace(month=data_pagamento.month + 1)
                    
                if movimentacao.forma_pagamento == FormaPagamento.CREDITO:       
                    fatura, cartao = await get_or_create_fatura(session, usuario_logado, movimentacao.id_financeiro, data_pagamento)
            await db.commit()
            return {"message": "Despesa cadastrada com sucesso."}
        
        except Exception as e:
            await handle_db_exceptions(session, e)
        finally:
            await session.close()
            
            
@router.post('/cadastro/receita', status_code=status.HTTP_201_CREATED)
async def create_movimentacao(
    movimentacao: MovimentacaoSchemaReceitaDespesa,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        try:
            query_categoria = select(CategoriaModel).where(CategoriaModel.id_categoria == movimentacao.id_categoria, CategoriaModel.id_usuario == usuario_logado.id_usuario)
            result_categoria = await session.execute(query_categoria)
            categoria = result_categoria.scalars().first()

            if not categoria:
                print(f"Categoria {movimentacao.id_categoria} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada ou não pertence ao usuário.")
            
            
            if movimentacao.condicao_pagamento != CondicaoPagamento.PARCELADO:
                movimentacao.quantidade_parcelas = 1
            else:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Não existe receita parcelada")

            
            if movimentacao.forma_pagamento in [FormaPagamento.DEBITO, FormaPagamento.DINHEIRO]:
                movimentacao.id_conta = movimentacao.id_financeiro
            else:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Só é aceito dinheiro ou débito para receita")

            if len(movimentacao.divide_parente) > 1:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Só é um parente (o usuário) para receitas")
            else: 
                parente_query = await session.execute(
                    select(ParenteModel).where(ParenteModel.id_parente == movimentacao.divide_parente[0].id_parente)
                )
                parente = parente_query.scalars().first()
                if parente.nome != usuario_logado.nome_completo:
                    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Só é aceito o próprio usuário para dividir uma receita")


            if movimentacao.id_conta is not None:
                query_conta = select(ContaModel).where(ContaModel.id_conta == movimentacao.id_conta, ContaModel.id_usuario == usuario_logado.id_usuario)
                result_conta = await session.execute(query_conta)
                conta = result_conta.scalars().first()
 
                if not conta:
                    print(f"Conta {movimentacao.id_conta} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada ou não pertence ao usuário.")

           
            data_pagamento = movimentacao.data_pagamento

            if movimentacao.condicao_pagamento in [CondicaoPagamento.PARCELADO, CondicaoPagamento.RECORRENTE]:
                
                if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE: 
                    if movimentacao.tipo_recorrencia == TipoRecorrencia.ANUAL:
                        movimentacao.quantidade_parcelas = 2
                    else: 
                        movimentacao.quantidade_parcelas = 8

                nova_repeticao = RepeticaoModel(
                    quantidade_parcelas=movimentacao.quantidade_parcelas,
                    tipo_recorrencia=movimentacao.tipo_recorrencia,
                    valor_total=movimentacao.valor,
                    data_inicio=movimentacao.data_pagamento,
                )
                db.add(nova_repeticao)
                await db.flush()
                await db.refresh(nova_repeticao)
                id_repeticao = nova_repeticao.id_repeticao

            # Criação das movimentações parceladas
            for parcela_atual in range(1, movimentacao.quantidade_parcelas + 1):
                nova_movimentacao = MovimentacaoModel(
                    valor= movimentacao.valor,
                    descricao=movimentacao.descricao,
                    tipoMovimentacao=TipoMovimentacao.RECEITA,
                    forma_pagamento=movimentacao.forma_pagamento,
                    condicao_pagamento=movimentacao.condicao_pagamento,
                    datatime=movimentacao.datatime,
                    consolidado=movimentacao.consolidado,
                    parcela_atual= str(parcela_atual),
                    data_pagamento=data_pagamento,
                    id_conta=movimentacao.id_conta,
                    id_categoria=movimentacao.id_categoria,
                    id_fatura= None,
                    id_repeticao= id_repeticao if movimentacao.condicao_pagamento != CondicaoPagamento.A_VISTA  else None,
                    id_usuario=usuario_logado.id_usuario
                )
                
                nova_movimentacao.divisoes = []

                db.add(nova_movimentacao)

                if movimentacao.consolidado and parcela_atual == 1:
                    conta.saldo = conta.saldo + Decimal(movimentacao.valor)
        

                # Criação dos relacionamentos com parentes
                for divide in movimentacao.divide_parente:
                    
                    valor = divide.valor_parente
                        
                    novo_divide_parente = DivideModel(
                        id_parente= divide.id_parente,
                        valor= valor
                    )
                    nova_movimentacao.divisoes.append(novo_divide_parente)


                movimentacao.consolidado = False
                
                if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE:
                    # Lógica para ajustar data_pagamento com base em recorrência
                    if movimentacao.tipo_recorrencia == TipoRecorrencia.ANUAL:
                        data_pagamento = data_pagamento.replace(year=data_pagamento.year + 1)
                    elif movimentacao.tipo_recorrencia == TipoRecorrencia.QUINZENAL:
                        data_pagamento += timedelta(days=15)
                    elif movimentacao.tipo_recorrencia == TipoRecorrencia.SEMANAL:
                        data_pagamento += timedelta(weeks=1)
                    elif movimentacao.tipo_recorrencia == TipoRecorrencia.MENSAL:
                        if data_pagamento.month == 12:
                            data_pagamento = data_pagamento.replace(year=data_pagamento.year + 1, month=1)
                        else:
                            data_pagamento = data_pagamento.replace(month=data_pagamento.month + 1)
                else:
                    if data_pagamento.month == 12:
                        data_pagamento = data_pagamento.replace(year=data_pagamento.year + 1, month=1)
                    else:
                        data_pagamento = data_pagamento.replace(month=data_pagamento.month + 1)
                
            await db.commit()
            return {"message": "Receita cadastrada com sucesso."}
        
        
        except Exception as e:
            await handle_db_exceptions(session, e)

        finally:
            await session.close()

@router.post('/cadastro/transferencia', status_code=status.HTTP_201_CREATED)
async def create_movimentacao(
    movimentacao: MovimentacaoSchemaTransferencia
,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        try:
            
            if movimentacao.id_conta_transferencia == movimentacao.id_conta_atual:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="As contas devem ter ids diferentes")

            
            contas_a_verificar = []

            contas_a_verificar.append(movimentacao.id_conta_atual)
            contas_a_verificar.append(movimentacao.id_conta_transferencia)
            
            query = select(ContaModel).where(
                ContaModel.id_usuario == usuario_logado.id_usuario,
                ContaModel.id_conta.in_(contas_a_verificar)  # Verifica se id_conta está na lista
            )
            result = await session.execute(query)
            contas_encontradas = result.scalars().all()
            
            if len(contas_encontradas) < 2:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contas não encontradas ou não pertencem ao usuário.")

            for conta in contas_encontradas:
                if(conta.id_conta == movimentacao.id_conta_atual):
                    conta.saldo = conta.saldo - Decimal(movimentacao.valor)
                elif (conta.id_conta == movimentacao.id_conta_transferencia):
                    conta.saldo = conta.saldo + Decimal(movimentacao.valor)
            await db.commit()
            return {"message": "Transferencia realizada com sucesso."}
        except Exception as e:
            await handle_db_exceptions(session, e)
            
        finally:
            await session.close()


@router.post('/editar/{id_movimentacao}', response_model=MovimentacaoSchemaId, status_code=status.HTTP_202_ACCEPTED)
async def update_movimentacao(
    id_movimentacao: int,
    movimentacao_update: MovimentacaoSchemaUpdate,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        # Verificar se a movimentação existe
        query_movimentacao = select(MovimentacaoModel).filter(MovimentacaoModel.id_movimentacao == id_movimentacao)
        result = await session.execute(query_movimentacao)
        movimentacao: MovimentacaoModel = result.scalars().unique().one_or_none()

        if not movimentacao:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimentação não encontrada")

        # Verificar se a conta pertence ao usuário logado (se fornecida)
        if movimentacao_update.id_conta:
            query_conta = select(ContaModel).where(ContaModel.id_conta == movimentacao_update.id_conta, ContaModel.id_usuario == usuario_logado.id_usuario)
            result_conta = await session.execute(query_conta)
            conta = result_conta.scalars().first()

            if not conta:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada ou não pertence ao usuário.")

        # Verificar se a categoria pertence ao usuário logado (se fornecida)
        if movimentacao_update.id_categoria:
            query_categoria = select(CategoriaModel).where(CategoriaModel.id_categoria == movimentacao_update.id_categoria, CategoriaModel.id_usuario == usuario_logado.id_usuario)
            result_categoria = await session.execute(query_categoria)
            categoria = result_categoria.scalars().first()

            if not categoria:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada ou não pertence ao usuário.")

        # Verificar se a fatura pertence ao usuário logado (se fornecida)
        if movimentacao_update.id_fatura:
            query_fatura = select(FaturaModel).where(FaturaModel.id_fatura == movimentacao_update.id_fatura)
            result_fatura = await session.execute(query_fatura)
            fatura = result_fatura.scalars().first()

            if not fatura:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fatura não encontrada.")

        # Atualizar campos fornecidos
        if movimentacao_update.valor is not None:
            movimentacao.valor = movimentacao_update.valor
        if movimentacao_update.descricao:
            movimentacao.descricao = movimentacao_update.descricao
        if movimentacao_update.tipoMovimentacao:
            movimentacao.tipoMovimentacao = movimentacao_update.tipoMovimentacao
        if movimentacao_update.forma_pagamento:
            movimentacao.forma_pagamento = movimentacao_update.forma_pagamento
        if movimentacao_update.condicao_pagamento:
            movimentacao.condicao_pagamento = movimentacao_update.condicao_pagamento
        if movimentacao_update.datatime:
            movimentacao.datatime = movimentacao_update.datatime
        if movimentacao_update.quantidade_parcelas is not None:
            movimentacao.quantidade_parcelas = movimentacao_update.quantidade_parcelas
        if movimentacao_update.consolidado:
            movimentacao.consolidado = movimentacao_update.consolidado
        if movimentacao_update.tipo_recorrencia:
            movimentacao.tipo_recorrencia = movimentacao_update.tipo_recorrencia
        if movimentacao_update.recorrencia:
            movimentacao.recorrencia = movimentacao_update.recorrencia
        if movimentacao_update.data_pagamento:
            movimentacao.data_pagamento = movimentacao_update.data_pagamento
        if movimentacao_update.id_conta:
            movimentacao.id_conta = movimentacao_update.id_conta
        if movimentacao_update.id_categoria:
            movimentacao.id_categoria = movimentacao_update.id_categoria
        if movimentacao_update.id_fatura:
            movimentacao.id_fatura = movimentacao_update.id_fatura

        try:
            await session.commit()
            return movimentacao
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao atualizar movimentação")
    

from sqlalchemy.orm import joinedload  # Certifique-se de importar joinedload

@router.get('/listar', response_model=List[MovimentacaoSchemaId])
async def listar_movimentacoes(
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db:  
        query = (
            select(MovimentacaoModel)
            .options(joinedload(MovimentacaoModel.conta), 
                      joinedload(MovimentacaoModel.repeticao)) 
            .join(MovimentacaoModel.conta)
            .filter(ContaModel.id_usuario == usuario_logado.id_usuario)
        )
        result = await db.execute(query)
        movimentacoes = result.scalars().all()
        

        if not movimentacoes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma movimentação encontrada")

        # Mapeando as movimentações para o schema
        response = [
            MovimentacaoSchemaId(
                id_movimentacao=mov.id_movimentacao,
                valor=mov.valor,
                descricao=mov.descricao,
                tipoMovimentacao=mov.tipoMovimentacao,
                forma_pagamento=mov.forma_pagamento,
                condicao_pagamento=mov.condicao_pagamento,
                datatime=mov.datatime,
                quantidade_parcelas=mov.repeticao.quantidade_parcelas if mov.repeticao else None,
                consolidado=mov.consolidado,
                tipo_recorrencia=mov.repeticao.tipo_recorrencia if mov.repeticao else None,
                parcela_atual=mov.parcela_atual,
                data_pagamento=mov.data_pagamento,
                id_conta=mov.id_conta,
                id_categoria=mov.id_categoria,
                id_fatura=mov.id_fatura,
                id_repeticao=mov.id_repeticao
            )
            for mov in movimentacoes
        ]

        return response

@router.post('/listar/filtro', response_model=List[MovimentacaoSchemaList])
async def listar_movimentacoes(
    requestFilter: MovimentacaoRequestFilterSchema,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db: 
        
        
        condicoes = [
            MovimentacaoModel.id_usuario == usuario_logado.id_usuario,
            extract('month', MovimentacaoModel.data_pagamento) == requestFilter.mes,
            extract('year', MovimentacaoModel.data_pagamento) == requestFilter.ano
        ] 
  
        if requestFilter.forma_pagamento is not None: 
            condicoes.append(MovimentacaoModel.forma_pagamento == requestFilter.forma_pagamento)
                
        if requestFilter.tipo_movimentacao is not None: 
            condicoes.append(MovimentacaoModel.tipoMovimentacao == requestFilter.tipo_movimentacao)        

        if requestFilter.consolidado is not None: 
            condicoes.append(MovimentacaoModel.consolidado == requestFilter.consolidado)
            
        if requestFilter.id_categoria is not None: 
            condicoes.append(MovimentacaoModel.id_categoria == requestFilter.id_categoria)
            
        if requestFilter.id_conta is not None: 
            condicoes.append(MovimentacaoModel.id_conta == requestFilter.id_conta)
            
        if requestFilter.id_fatura is not None: 
            condicoes.append(MovimentacaoModel.id_fatura == requestFilter.id_fatura)
            
        query = (
            select(MovimentacaoModel)
            .options(
                selectinload(MovimentacaoModel.categoria),
                selectinload(MovimentacaoModel.conta),
                selectinload(MovimentacaoModel.repeticao),
                selectinload(MovimentacaoModel.divisoes),
                selectinload(MovimentacaoModel.divisoes, DivideModel.parentes),
                selectinload(MovimentacaoModel.fatura),
                selectinload(MovimentacaoModel.fatura, FaturaModel.cartao_credito)
            )
            .where(*condicoes)  # Suas outras condições
        )

        if requestFilter.id_parente is not None:
            query = query.join(DivideModel, MovimentacaoModel.divisoes).where(DivideModel.id_parente == requestFilter.id_parente)

        
        result = await db.execute(query)
        movimentacoes = result.scalars().all()

        if not movimentacoes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma movimentação encontrada")

        response = [
            MovimentacaoSchemaList(
                id_movimentacao=mov.id_movimentacao,
                valor=mov.valor,
                descricao=mov.descricao,
                tipoMovimentacao=mov.tipoMovimentacao,
                forma_pagamento=mov.forma_pagamento,
                condicao_pagamento=mov.condicao_pagamento,
                datatime=mov.datatime,
                quantidade_parcelas= mov.repeticao.quantidade_parcelas if mov.repeticao else None , 
                consolidado=mov.consolidado,
                tipo_recorrencia= mov.repeticao.tipo_recorrencia if mov.repeticao else None , 
                parcela_atual=mov.parcela_atual,
                data_pagamento=mov.data_pagamento,
                id_conta=mov.id_conta,
                id_categoria=mov.id_categoria,
                nome_icone_categoria=mov.categoria.nome_icone if mov.categoria else None,
                nome_conta = mov.conta.nome if mov.conta else None,
                nome_cartao_credito = mov.fatura.cartao_credito.nome if mov.fatura else None,
                id_fatura=mov.id_fatura,
                id_repeticao=mov.id_repeticao,
                divide_parente=[
                    ParenteResponse(
                        id_parente=divide.id_parente,
                        valor_parente=divide.valor, 
                        nome_parente= divide.parentes.nome
                    )
                    for divide in mov.divisoes 
                ],
                fatura_info = 
                    FaturaSchema(
                        data_vencimento= mov.fatura.data_vencimento,
                        data_fechamento = mov.fatura.data_fechamento,
                        data_pagamento = mov.fatura.data_pagamento,
                        id_cartao_credito = mov.fatura.id_cartao_credito,
                        id_conta = mov.fatura.id_conta
                    ) if requestFilter.id_fatura is not None else None
            )
            for mov in movimentacoes
        ]

        return response





        
@router.get('/visualizar/{id_movimentacao}', response_model=MovimentacaoSchemaId)
async def visualizar_movimentacao(
    id_movimentacao: int,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        query = select(MovimentacaoModel).join(MovimentacaoModel.conta).filter(MovimentacaoModel.id_movimentacao == id_movimentacao, MovimentacaoModel.conta.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        movimentacao = result.scalars().one_or_none()

        if not movimentacao:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimentação não encontrada ou não pertence ao usuário")

        return movimentacao

@router.delete('/deletar/{id_movimentacao}', status_code=status.HTTP_204_NO_CONTENT)
async def deletar_movimentacao(
    id_movimentacao: int,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        query = select(MovimentacaoModel).join(MovimentacaoModel.conta).filter(MovimentacaoModel.id_movimentacao == id_movimentacao, ContaModel.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        movimentacao = result.scalars().one_or_none()

        if not movimentacao:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimentação não encontrada ou não pertence ao usuário")

        await session.delete(movimentacao)
        await session.commit()

        return
