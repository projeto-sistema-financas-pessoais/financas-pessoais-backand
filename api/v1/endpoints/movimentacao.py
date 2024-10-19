
from decimal import Decimal
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import extract, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from api.v1.endpoints.fatura import create_fatura_ano
from models.cartao_credito_model import CartaoCreditoModel
from models.movimentacao_model import MovimentacaoModel
from schemas.fatura_schema import FaturaSchemaId
from schemas.movimentacao_schema import IdMovimentacaoSchema, MovimentacaoSchema, MovimentacaoSchemaDespesa, MovimentacaoSchemaUpdate, MovimentacaoSchemaId
from core.deps import get_session, get_current_user
from models.usuario_model import UsuarioModel
from models.conta_model import ContaModel
from models.categoria_model import CategoriaModel
from models.fatura_model import FaturaModel
from typing import List
from models.repeticao_model import RepeticaoModel
from models.enums import CondicaoPagamento, FormaPagamento, TipoMovimentacao, TipoRecorrencia
from datetime import date, timedelta
from models.associations_model import  divide_table
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
    # Tenta encontrar a fatura
    fatura = await find_fatura(id_financeiro, data_pagamento, session)
    cartao_credito = None  # Inicializa como None

    if not fatura:
        # Se não encontrar, cria uma nova fatura para o ano correspondente
        cartao_credito = await create_fatura_ano(session, usuario_logado, id_financeiro, data_pagamento.year, None, None)
        # Tenta buscar a fatura novamente
        fatura = await find_fatura(id_financeiro, data_pagamento, session)
        
        if not fatura:
            # Se ainda assim não encontrar, levanta uma exceção
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao adicionar fatura")
    
    return fatura, cartao_credito



@router.post('/cadastro/despesa', status_code=status.HTTP_201_CREATED)
async def create_movimentacao(
    movimentacao: MovimentacaoSchemaDespesa,
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
            
            # Ajuste de quantidade de parcelas se necessário
            if movimentacao.condicao_pagamento != CondicaoPagamento.PARCELADO:
                movimentacao.quantidade_parcelas = 1
            
            

            # Ajuste da conta ou criação de fatura
            if movimentacao.forma_pagamento in [FormaPagamento.DEBITO, FormaPagamento.DINHEIRO]:
                movimentacao.id_conta = movimentacao.id_financeiro
            else:
                movimentacao.consolidado = False
                fatura, cartao_credito = await get_or_create_fatura(session, usuario_logado, movimentacao.id_financeiro, movimentacao.data_pagamento)
                print(f"Fatura {fatura}")
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
                
                
                
                db.add(nova_movimentacao)
                await db.flush()
                await db.refresh(nova_movimentacao)
                
                if movimentacao.consolidado and parcela_atual == 1:
                    conta.saldo = conta.saldo - Decimal(valor_por_parcela_ajustado + valor_restante)
        
                        
                if movimentacao.forma_pagamento == FormaPagamento.CREDITO:
                    print(f"Fatura inicio ",valor_por_parcela_ajustado, valor_restante, fatura.fatura_gastos )

                    if parcela_atual == 1:
                        cartao_credito.limite_disponivel = cartao_credito.limite_disponivel - valor_por_parcela_ajustado + valor_restante
                        fatura.fatura_gastos +=valor_por_parcela_ajustado + valor_restante
                    elif movimentacao.condicao_pagamento == CondicaoPagamento.PARCELADO:
                        cartao_credito.limite_disponivel = cartao_credito.limite_disponivel - valor_por_parcela_ajustado
                        fatura.fatura_gastos +=valor_por_parcela_ajustado
                    print(f"Fatura final ",valor_por_parcela_ajustado, valor_restante, fatura.fatura_gastos )


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
                        

                    novo_divide_parente = insert(divide_table).values(
                        id_parente=divide.id_parente,
                        id_movimentacao=nova_movimentacao.id_movimentacao,
                        valor= valor,
                    )
                    await db.execute(novo_divide_parente)

                # await db.commit()

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
                    
                if movimentacao.forma_pagamento == FormaPagamento.CREDITO:       
                    fatura, cartao = await get_or_create_fatura(session, usuario_logado, movimentacao.id_financeiro, data_pagamento)
            await db.commit()
            return {"message": "Despesa cadastrada com sucesso."}
        
        except IntegrityError as e:
            await session.rollback()
            print(f"Erro de integridade: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro de integridade no banco de dados: {e.orig}"
            )

        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Erro de banco de dados: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro no banco de dados, tente novamente mais tarde."
            )

        except Exception as e:
            await session.rollback()
            print(f"Erro geral: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ocorreu um erro: {e}"
            )

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
    async with db:  # Adicione o gerenciador de contexto aqui
        query = (
            select(MovimentacaoModel)
            .options(joinedload(MovimentacaoModel.conta), 
                      joinedload(MovimentacaoModel.repeticao)) 
            .join(MovimentacaoModel.conta)  # Adicione a junção aqui
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
