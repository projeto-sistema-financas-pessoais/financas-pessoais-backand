
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

router = APIRouter()

# @router.post('/cadastro', response_model=MovimentacaoSchema, status_code=status.HTTP_201_CREATED)
# async def create_movimentacao(
#     movimentacao: MovimentacaoSchema,
#     db: AsyncSession = Depends(get_session),
#     usuario_logado: UsuarioModel = Depends(get_current_user)
# ):
#     async with db as session:
#         # Verificar se a conta pertence ao usuário logado
#         print(f"Verificando se a conta {movimentacao.id_conta} pertence ao usuário {usuario_logado.id_usuario}")
#         query_conta = select(ContaModel).where(ContaModel.id_conta == movimentacao.id_conta, ContaModel.id_usuario == usuario_logado.id_usuario)
#         result_conta = await session.execute(query_conta)
#         conta = result_conta.scalars().first()

#         if not conta:
#             print(f"Conta {movimentacao.id_conta} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada ou não pertence ao usuário.")

#         # Verificar se a categoria pertence ao usuário logado
#         print(f"Verificando se a categoria {movimentacao.id_categoria} pertence ao usuário {usuario_logado.id_usuario}")
#         query_categoria = select(CategoriaModel).where(CategoriaModel.id_categoria == movimentacao.id_categoria, CategoriaModel.id_usuario == usuario_logado.id_usuario)
#         result_categoria = await session.execute(query_categoria)
#         categoria = result_categoria.scalars().first()

#         if not categoria:
#             print(f"Categoria {movimentacao.id_categoria} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada ou não pertence ao usuário.")

#         # Criar nova movimentação
#         nova_movimentacao = MovimentacaoModel(
#             valor=movimentacao.valor,
#             descricao=movimentacao.descricao,
#             tipoMovimentacao=movimentacao.tipoMovimentacao,
#             forma_pagamento=movimentacao.forma_pagamento,
#             condicao_pagamento=movimentacao.condicao_pagamento,
#             datatime=movimentacao.datatime,
#             quantidade_parcelas=movimentacao.quantidade_parcelas,
#             consolidado=movimentacao.consolidado,
#             tipo_recorrencia=movimentacao.tipo_recorrencia,
#             recorrencia=movimentacao.recorrencia,
#             data_pagamento=movimentacao.data_pagamento,
#             id_conta=movimentacao.id_conta,
#             id_categoria=movimentacao.id_categoria,
#         )
#         print("============== Nova Movimentação Criada ==============")
#         print(f"Movimentação: {nova_movimentacao}")
#         print(f"Conta associada: {conta}")
#         print(f"Categoria associada: {categoria}")

#         try:
#             session.add(nova_movimentacao)
#             await session.commit()
#             print(f"Movimentação {nova_movimentacao.id_movimentacao} criada com sucesso.")
#             return nova_movimentacao
#         except IntegrityError as e:
#             print(f"Erro de integridade ao criar movimentação: {e}")
#             await session.rollback()
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao criar movimentação.")

def find_fatura(movimentacao: MovimentacaoSchemaDespesa):
    fatura = FaturaSchemaId.query.filter(
            FaturaSchemaId.id_cartao_credito == movimentacao.id_financeiro,
            extract('month', FaturaSchemaId.data_fechamento) == movimentacao.data_pagamento.month,
            extract('year', FaturaSchemaId.data_fechamento) == movimentacao.data_pagamento.year
            ).first()
    return fatura



# @router.post('/cadastro/despesa', status_code=status.HTTP_201_CREATED)
# async def create_movimentacao(
#     movimentacao: MovimentacaoSchemaDespesa,
#     db: AsyncSession = Depends(get_session),
#     usuario_logado: UsuarioModel = Depends(get_current_user)
# ):
#     async with db as session:
#         try:
#             query_categoria = select(CategoriaModel).where(
#                 CategoriaModel.id_categoria == movimentacao.id_categoria, 
#                 CategoriaModel.id_usuario == usuario_logado.id_usuario
#             )
#             result_categoria = await session.execute(query_categoria)
#             categoria = result_categoria.scalars().first()

#             if not categoria:
#                 print(f"Categoria {movimentacao.id_categoria} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
#                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada ou não pertence ao usuário.")

#             # Validação da soma dos valores de parentes
#             soma = sum(divide.valor_parente for divide in movimentacao.divide_parente)
#             if soma != movimentacao.valor:
#                 raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Valor total de parentes não pode ser diferente do valor.")
            
#             # Ajuste de quantidade de parcelas se necessário
#             if movimentacao.quantidade_parcelas is None:
#                 movimentacao.quantidade_parcelas = 1

#             # Ajuste da conta ou criação de fatura
#             if movimentacao.forma_pagamento in [FormaPagamento.DEBITO, FormaPagamento.DINHEIRO]:
#                 movimentacao.id_conta = movimentacao.id_financeiro
#             else:
#                 movimentacao.consolidado = False
#                 fatura = find_fatura(movimentacao)
#                 if not fatura:
#                     cartao_credito = create_fatura_ano(session, usuario_logado, movimentacao.id_financeiro, movimentacao.data_pagamento.year, None, None)
#                     fatura = find_fatura(movimentacao)
#                     if not fatura:
#                         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao adicionar fatura")
#                 else:
#                     query_cartao_credito = select(CartaoCreditoModel).where(
#                         CartaoCreditoModel.id_cartao_credito == movimentacao.id_conta,
#                         CartaoCreditoModel.id_usuario == usuario_logado.id_usuario
#                     )
#                     result_cartao_credito = await session.execute(query_cartao_credito)
#                     cartao_credito = result_cartao_credito.scalars().one_or_none()

#                     if not cartao_credito:
#                         raise HTTPException(
#                             status_code=status.HTTP_403_FORBIDDEN, 
#                             detail="Você não tem permissão para acessar esse cartão"
#                         )

#             if movimentacao.id_conta is not None:
#                 query_conta = select(ContaModel).where(
#                     ContaModel.id_conta == movimentacao.id_conta, 
#                     ContaModel.id_usuario == usuario_logado.id_usuario
#                 )
#                 result_conta = await session.execute(query_conta)
#                 conta = result_conta.scalars().first()
                
#                 if not conta:
#                     print(f"Conta {movimentacao.id_conta} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
#                     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada ou não pertence ao usuário.")

#             # Preparação para criar movimentações parceladas
#             valor_por_parcela = movimentacao.valor / movimentacao.quantidade_parcelas
#             data_pagamento = movimentacao.data_pagamento

#             if movimentacao.condicao_pagamento in [CondicaoPagamento.PARCELADO, CondicaoPagamento.RECORRENTE]:
#                 quantidade_parcelas = (
#                     24 if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE else movimentacao.quantidade_parcelas
#                 )
#                 nova_repeticao = RepeticaoModel(
#                     quantidade_parcelas=quantidade_parcelas,
#                     tipo_recorrencia=movimentacao.tipo_recorrencia,
#                     valor_total=movimentacao.valor,
#                     data_inicio=movimentacao.data_pagamento,
#                     id_usuario=usuario_logado.id_usuario,
#                 )
#                 session.add(nova_repeticao)
#                 await session.commit()
#                 await session.refresh(nova_repeticao)

#             # Criação das movimentações parceladas
#             for parcela_atual in range(1, movimentacao.quantidade_parcelas + 1):
#                 nova_movimentacao = MovimentacaoModel(
#                     valor=valor_por_parcela,
#                     descricao=movimentacao.descricao,
#                     tipoMovimentacao=TipoMovimentacao.DESPESA,
#                     forma_pagamento=movimentacao.forma_pagamento,
#                     condicao_pagamento=movimentacao.condicao_pagamento,
#                     datatime=movimentacao.datatime,
#                     consolidado=movimentacao.consolidado,
#                     parcela_atual=str(parcela_atual),
#                     data_pagamento=data_pagamento,
#                     id_conta=movimentacao.id_conta,
#                     id_categoria=movimentacao.id_categoria,
#                     id_fatura=fatura.id_fatura if movimentacao.forma_pagamento == FormaPagamento.CREDITO else None,
#                     id_repeticao=nova_repeticao.id_repeticao if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE else None
#                 )

#                 session.add(nova_movimentacao)
#                 await session.refresh(nova_movimentacao)
                
#                 if movimentacao.consolidado and parcela_atual == 1:
#                     conta.saldo -= Decimal(valor_por_parcela)
                
#                 if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE:
#                     if parcela_atual == 1:
#                         cartao_credito.limite_disponivel -= valor_por_parcela
#                 elif movimentacao.forma_pagamento == FormaPagamento.CREDITO:
#                     cartao_credito.limite_disponivel -= valor_por_parcela

#                 # Criação dos relacionamentos com parentes
#                 for divide in movimentacao.divide_parente:
#                     novo_divide_parente = insert(divide_table).values(
#                         id_parente=divide.id_parente,
#                         id_movimentacao=nova_movimentacao.id_movimentacao,
#                         valor=divide.valor_parente,
#                     )
#                     await session.execute(novo_divide_parente)

#             # Ajuste da data de pagamento para movimentações recorrentes
#             if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE:
#                 if movimentacao.tipo_recorrencia == TipoRecorrencia.ANUAL:
#                     data_pagamento = data_pagamento.replace(year=data_pagamento.year + 1)
#                 elif movimentacao.tipo_recorrencia == TipoRecorrencia.QUINZENAL:
#                     data_pagamento += timedelta(days=15)
#                 elif movimentacao.tipo_recorrencia == TipoRecorrencia.SEMANAL:
#                     data_pagamento += timedelta(weeks=1)
#                 elif movimentacao.tipo_recorrencia == TipoRecorrencia.MENSAL:
#                     if data_pagamento.month == 12:
#                         data_pagamento = data_pagamento.replace(year=data_pagamento.year + 1, month=1)
#                     else:
#                         data_pagamento = data_pagamento.replace(month=data_pagamento.month + 1)
#             else:
#                 if data_pagamento.month == 12:
#                     data_pagamento = data_pagamento.replace(year=data_pagamento.year + 1, month=1)
#                 else:
#                     data_pagamento = data_pagamento.replace(month=data_pagamento.month + 1)

#             # Commit final para salvar todas as alterações
#             await session.commit()
            
#             return {"detail": "Despesa cadastrada com sucesso!"}

#         except HTTPException as e:
#             print(f"Ocorreu um erro HTTPExceptions: {str(e)}")  # Imprimir o erro
#             raise e
#         except Exception as e:
#             # Tratar exceções gerais, se necessário
#             print(f"Ocorreu um erro: {str(e)}")  # Imprimir o erro
#             await session.rollback()
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao cadastrar despesa.")


@router.post('/cadastro/despesa', status_code=status.HTTP_201_CREATED)
async def create_movimentacao(
    movimentacao: MovimentacaoSchemaDespesa,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        
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
        if movimentacao.quantidade_parcelas is None:
            movimentacao.quantidade_parcelas = 1

        # Ajuste da conta ou criação de fatura
        if movimentacao.forma_pagamento in [FormaPagamento.DEBITO, FormaPagamento.DINHEIRO]:
            movimentacao.id_conta = movimentacao.id_financeiro
        else:
            movimentacao.consolidado = False
            fatura = find_fatura(movimentacao)
            if not fatura:
                cartao_credito =  create_fatura_ano(session, usuario_logado, movimentacao.id_financeiro, movimentacao.data_pagamento.year, None, None)
                fatura = find_fatura(movimentacao)
                if not fatura:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao adicionar fatura")
            else:
                query_cartao_credito = select(CartaoCreditoModel).where(
                    CartaoCreditoModel.id_cartao_credito == movimentacao.id_conta,
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
        data_pagamento = movimentacao.data_pagamento

        if movimentacao.condicao_pagamento in [CondicaoPagamento.PARCELADO, CondicaoPagamento.RECORRENTE]:
            quantidade_parcelas = (
                24 if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE else movimentacao.quantidade_parcelas
            )
            nova_repeticao = RepeticaoModel(
                quantidade_parcelas=quantidade_parcelas,
                tipo_recorrencia=movimentacao.tipo_recorrencia,
                valor_total=movimentacao.valor,
                data_inicio=movimentacao.data_pagamento,
                id_usuario=usuario_logado.id_usuario,
            )
            db.add(nova_repeticao)
            await db.commit()
            await db.refresh(nova_repeticao)

        # Criação das movimentações parceladas
        for parcela_atual in range(1, movimentacao.quantidade_parcelas + 1):
            nova_movimentacao = MovimentacaoModel(
                valor=valor_por_parcela,
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
                id_repeticao=nova_repeticao.id_repeticao if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE else None
            )
            
            
            
            db.add(nova_movimentacao)
            await db.commit()
            await db.refresh(nova_movimentacao)
            
            if movimentacao.consolidado and parcela_atual == 1:
                conta.saldo = conta.saldo - Decimal(valor_por_parcela)
                
            if movimentacao.condicao_pagamento == CondicaoPagamento.RECORRENTE and movimentacao.forma_pagamento == FormaPagamento.CREDITO :
                if parcela_atual == 1:
                    cartao_credito.limite_disponivel = cartao_credito.limite_disponivel - valor_por_parcela
            elif movimentacao.forma_pagamento == FormaPagamento.CREDITO:
                cartao_credito.limite_disponivel = cartao_credito.limite_disponivel - valor_por_parcela

            # Criação dos relacionamentos com parentes
            for divide in movimentacao.divide_parente:
                novo_divide_parente = insert(divide_table).values(
                    id_parente=divide.id_parente,
                    id_movimentacao=nova_movimentacao.id_movimentacao,
                    valor=divide.valor_parente,
                )
                await db.execute(novo_divide_parente)

            await db.commit()

        # Ajuste da data de pagamento para movimentações recorrentes
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
                      joinedload(MovimentacaoModel.repeticao))  # Use options() para joinedload
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
