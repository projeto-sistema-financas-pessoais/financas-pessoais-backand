from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from core.deps import get_session, get_current_user
from models.cartao_credito_model import CartaoCreditoModel
from schemas.cartao_de_credito_schema import CartaoCreditoCreateSchema, CartaoCreditoSchema, CartaoCreditoUpdateSchema
from models.usuario_model import UsuarioModel

router = APIRouter()

@router.post('/cadastro', response_model=CartaoCreditoSchema, status_code=status.HTTP_201_CREATED)
async def create_cartao_credito(
    cartao_credito: CartaoCreditoCreateSchema, 
    db: AsyncSession = Depends(get_session), 
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    novo_cartao: CartaoCreditoModel = CartaoCreditoModel(
        nome=cartao_credito.nome,
        limite=cartao_credito.limite,
        id_usuario=usuario_logado.id_usuario,
        nome_icone=cartao_credito.nome_icone,
        ativo=cartao_credito.ativo if cartao_credito.ativo is not None else True  # Definindo o valor padrão como True
    )

    async with db as session:
        try:
            session.add(novo_cartao)
            await session.commit()
            return novo_cartao
        except IntegrityError:
            await session.rollback()  
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Já existe um cartão de crédito com este nome para este usuário")

@router.put('/editar/{id_cartao_credito}', response_model=CartaoCreditoSchema, status_code=status.HTTP_202_ACCEPTED)
async def update_cartao_credito(
    id_cartao_credito: int, 
    cartao_credito_update: CartaoCreditoUpdateSchema, 
    db: AsyncSession = Depends(get_session), 
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        query = select(CartaoCreditoModel).where(
            CartaoCreditoModel.id_cartao_credito == id_cartao_credito,
            CartaoCreditoModel.id_usuario == usuario_logado.id_usuario
        )
        result = await session.execute(query)
        cartao_credito: CartaoCreditoModel = result.scalars().unique().one_or_none()

        if not cartao_credito:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartão de crédito não encontrado ou você não tem permissão para editá-lo")

        if cartao_credito_update.nome:
            cartao_credito.nome = cartao_credito_update.nome
        if cartao_credito_update.limite:
            cartao_credito.limite = cartao_credito_update.limite
        if cartao_credito_update.nome_icone:
            cartao_credito.nome_icone = cartao_credito_update.nome_icone
        if cartao_credito_update.ativo is not None:
            cartao_credito.ativo = cartao_credito_update.ativo

        try:
            await session.commit()
            return cartao_credito
        except IntegrityError:
            await session.rollback() 
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Já existe um cartão com este nome para este usuário")
        

@router.get('/Listar', response_model=list[CartaoCreditoSchema], status_code=status.HTTP_200_OK)
async def listar_cartoes_credito(db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(CartaoCreditoModel).where(CartaoCreditoModel.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        cartoes_credito = result.scalars().all()

        return cartoes_credito
    
@router.get('/visualizar/{id_cartao_credito}', response_model=CartaoCreditoSchema, status_code=status.HTTP_200_OK)
async def listar_cartao_credito(
    id_cartao_credito: int, 
    db: AsyncSession = Depends(get_session), 
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        query = select(CartaoCreditoModel).where(
            CartaoCreditoModel.id_cartao_credito == id_cartao_credito,
            CartaoCreditoModel.id_usuario == usuario_logado.id_usuario
        )
        result = await session.execute(query)
        cartao_credito = result.scalars().one_or_none()

        if not cartao_credito:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartão de crédito não encontrado ou você não tem permissão para visualizá-lo")

        return cartao_credito
    
@router.delete('/deletar/{id_cartao_credito}', status_code=status.HTTP_204_NO_CONTENT)
async def deletar_cartao_credito(
    id_cartao_credito: int, 
    db: AsyncSession = Depends(get_session), 
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        query = select(CartaoCreditoModel).where(
            CartaoCreditoModel.id_cartao_credito == id_cartao_credito,
            CartaoCreditoModel.id_usuario == usuario_logado.id_usuario
        )
        result = await session.execute(query)
        cartao_credito = result.scalars().one_or_none()

        if not cartao_credito:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartão de crédito não encontrado ou você não tem permissão para deletá-lo")

        await session.delete(cartao_credito)
        await session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)
