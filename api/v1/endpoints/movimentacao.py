from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from api.v1.endpoints.fatura import create_fatura_ano
from models.movimentacao_model import MovimentacaoModel
from schemas.fatura_schema import FaturaSchemaId
from schemas.movimentacao_schema import IdMovimentacaoSchema, MovimentacaoSchema, MovimentacaoSchemaDespesa, MovimentacaoSchemaUpdate, MovimentacaoSchemaId
from core.deps import get_session, get_current_user
from models.usuario_model import UsuarioModel
from models.conta_model import ContaModel
from models.categoria_model import CategoriaModel
from models.fatura_model import FaturaModel
from typing import List

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


@router.post('/cadastro/despesa', response_model=IdMovimentacaoSchema, status_code=status.HTTP_201_CREATED)
async def create_movimentacao(
    movimentacao: MovimentacaoSchemaDespesa,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        
        movimentacao_cadastro: MovimentacaoSchema

        movimentacao_cadastro.valor = movimentacao.valor
        movimentacao_cadastro.descricao = movimentacao.descricao
        movimentacao_cadastro.tipoMovimentacao = "Despesa"
        movimentacao_cadastro.forma_pagamento = movimentacao.forma_pagamento
        movimentacao_cadastro.condicao_pagamento = movimentacao.condicao_pagamento
        movimentacao_cadastro.datatime = movimentacao.datatime
        movimentacao_cadastro.data_pagamento = movimentacao.data_pagamento

        
        if movimentacao.forma_pagamento == "Débito" or movimentacao.forma_pagamento == "Dinheiro":
            movimentacao_cadastro.id_conta = movimentacao.id_financeiro
            movimentacao_cadastro.consolidado = movimentacao.consolidado

            # if(movimentacao.consolidado):
            #         #desconta da conta
        else:
            movimentacao_cadastro.consolidado = False

            fatura = find_fatura(movimentacao)            
            if fatura:
                movimentacao_cadastro.id_fatura = fatura.id_fatura
            else:
                create_fatura_ano(session, usuario_logado, movimentacao.id_financeiro, movimentacao.data_pagamento.year, None, None )
                fatura = find_fatura(movimentacao)        

                if fatura:
                    movimentacao_cadastro.id_fatura = fatura.id_fatura    
                else:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao adicionar fatura")


        if(movimentacao.condicao_pagamento == "Parcelado"):
            movimentacao_cadastro.quantidade_parcelas = movimentacao.quantidade_parcelas

            ## 3 quantidade = 3
            # id_movimentacao 1  ===> setembro  1/3  não coloca (credito ou debito)
            # id_movimentacao 2  ===> outubro 2/3
            # id_movimentacao 2  ===> novembro 3/3

        


        #if(movimentacao.condicao_pagamento == "Recorrente"):




        


        

        query_conta = select(ContaModel).where(ContaModel.id_conta == movimentacao.id_conta, ContaModel.id_usuario == usuario_logado.id_usuario)
        result_conta = await session.execute(query_conta)
        conta = result_conta.scalars().first()

        if not conta:
             print(f"Conta {movimentacao.id_conta} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada ou não pertence ao usuário.")

        query_categoria = select(CategoriaModel).where(CategoriaModel.id_categoria == movimentacao.id_categoria, CategoriaModel.id_usuario == usuario_logado.id_usuario)
        result_categoria = await session.execute(query_categoria)
        categoria = result_categoria.scalars().first()

        if not categoria:
             print(f"Categoria {movimentacao.id_categoria} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada ou não pertence ao usuário.")
        

    

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
    
@router.get('/listar', response_model=List[MovimentacaoSchemaId])
async def listar_movimentacoes(
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        # Listar todas as movimentações do usuário logado
        query = select(MovimentacaoModel).join(MovimentacaoModel.conta).filter(MovimentacaoModel.conta.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        movimentacoes = result.scalars().all()

        if not movimentacoes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma movimentação encontrada")

        return movimentacoes
        
        
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
        query = select(MovimentacaoModel).join(MovimentacaoModel.conta).filter(MovimentacaoModel.id_movimentacao == id_movimentacao, MovimentacaoModel.conta.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        movimentacao = result.scalars().one_or_none()

        if not movimentacao:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimentação não encontrada ou não pertence ao usuário")

        await session.delete(movimentacao)
        await session.commit()

        return
