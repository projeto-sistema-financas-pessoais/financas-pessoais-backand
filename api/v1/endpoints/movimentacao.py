from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from models.movimentacao_model import MovimentacaoModel
from schemas.movimentacao_schema import MovimentacaoSchema, MovimentacaoSchemaUpdate, MovimentacaoSchemaId
from core.deps import get_session, get_current_user
from models.usuario_model import UsuarioModel
from models.conta_model import ContaModel
from models.categoria_model import CategoriaModel
from models.fatura_model import FaturaModel
from typing import List

router = APIRouter()

@router.post('/cadastro', response_model=MovimentacaoSchema, status_code=status.HTTP_201_CREATED)
async def create_movimentacao(
    movimentacao: MovimentacaoSchema,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        # Verificar se a conta pertence ao usuário logado
        print(f"Verificando se a conta {movimentacao.id_conta} pertence ao usuário {usuario_logado.id_usuario}")
        query_conta = select(ContaModel).where(ContaModel.id_conta == movimentacao.id_conta, ContaModel.id_usuario == usuario_logado.id_usuario)
        result_conta = await session.execute(query_conta)
        conta = result_conta.scalars().first()

        if not conta:
            print(f"Conta {movimentacao.id_conta} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada ou não pertence ao usuário.")

        # Verificar se a categoria pertence ao usuário logado
        print(f"Verificando se a categoria {movimentacao.id_categoria} pertence ao usuário {usuario_logado.id_usuario}")
        query_categoria = select(CategoriaModel).where(CategoriaModel.id_categoria == movimentacao.id_categoria, CategoriaModel.id_usuario == usuario_logado.id_usuario)
        result_categoria = await session.execute(query_categoria)
        categoria = result_categoria.scalars().first()

        if not categoria:
            print(f"Categoria {movimentacao.id_categoria} não encontrada ou não pertence ao usuário {usuario_logado.id_usuario}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada ou não pertence ao usuário.")

        # Criar nova movimentação
        nova_movimentacao = MovimentacaoModel(
            valor=movimentacao.valor,
            descricao=movimentacao.descricao,
            tipoMovimentacao=movimentacao.tipoMovimentacao,
            forma_pagamento=movimentacao.forma_pagamento,
            condicao_pagamento=movimentacao.condicao_pagamento,
            datatime=movimentacao.datatime,
            quantidade_parcelas=movimentacao.quantidade_parcelas,
            consolidado=movimentacao.consolidado,
            tipo_recorrencia=movimentacao.tipo_recorrencia,
            recorrencia=movimentacao.recorrencia,
            data_pagamento=movimentacao.data_pagamento,
            id_conta=movimentacao.id_conta,
            id_categoria=movimentacao.id_categoria,
        )
        print("============== Nova Movimentação Criada ==============")
        print(f"Movimentação: {nova_movimentacao}")
        print(f"Conta associada: {conta}")
        print(f"Categoria associada: {categoria}")

        try:
            session.add(nova_movimentacao)
            await session.commit()
            print(f"Movimentação {nova_movimentacao.id_movimentacao} criada com sucesso.")
            return nova_movimentacao
        except IntegrityError as e:
            print(f"Erro de integridade ao criar movimentação: {e}")
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao criar movimentação.")

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
