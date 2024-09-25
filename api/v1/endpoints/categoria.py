from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List
from core.deps import get_current_user, get_session
from models.categoria_model import CategoriaModel
from models.usuario_model import UsuarioModel
from schemas.categoria_schema import CategoriaSchema, CategoriaCreateSchema, CategoriaUpdateSchema, CategoriaSchemaId
from sqlalchemy.future import select

router = APIRouter()

@router.post('/criar', status_code=status.HTTP_201_CREATED)
async def post_categoria(
    categoria: CategoriaCreateSchema, 
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    nova_categoria: CategoriaModel = CategoriaModel(
        nome=categoria.nome,
        descricao=categoria.descricao,
        tipo_categoria=categoria.tipo_categoria,
        modelo_categoria=categoria.modelo_categoria,
        id_usuario=usuario_logado.id_usuario,
        valor_categoria=categoria.valor_categoria
    )
    
    async with db as session:
        try:
            session.add(nova_categoria)
            await session.commit()
            return nova_categoria
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Categoria já cadastrada para este usuário")

@router.get('/visualizar/{id_categoria}', response_model=CategoriaSchema, status_code=status.HTTP_200_OK)
async def get_categoria(
    id_categoria: int, 
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(CategoriaModel).where(CategoriaModel.id_categoria == id_categoria, CategoriaModel.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        categoria = CategoriaSchemaId = result.scalars().unique().one_or_none()
        if not categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
        return categoria

@router.get('/listar/', response_model=List[CategoriaSchemaId])
async def get_categorias ( db: AsyncSession = Depends(get_session),
                      usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(CategoriaModel).where(CategoriaModel.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        categorias: List[CategoriaSchemaId] = result.scalars().unique().all()
      
        return categorias


@router.put('/editar/{categoria_id}', response_model=CategoriaSchemaId, status_code=status.HTTP_202_ACCEPTED)
async def put_categoria(
    categoria_id: int, 
    categoria: CategoriaUpdateSchema, 
    db: AsyncSession = Depends(get_session), 
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        query = select(CategoriaModel).filter(CategoriaModel.id_categoria == categoria_id)
        result = await session.execute(query)
        categoria_up: CategoriaModel = result.scalars().unique().one_or_none()

        if not categoria_up:
            raise HTTPException(
                detail="Categoria não encontrada.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if categoria_up.id_usuario != usuario_logado.id_usuario:
            raise HTTPException(
                detail="Você não tem permissão para editar esta categoria.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        if categoria.nome:
            categoria_up.nome = categoria.nome
        if categoria.descricao:
            categoria_up.descricao = categoria.descricao
        if categoria.tipo_categoria:
            categoria_up.tipo_categoria = categoria.tipo_categoria
        if categoria.modelo_categoria:
            categoria_up.modelo_categoria = categoria.modelo_categoria
        if categoria.valor_categoria is not None:
            categoria_up.valor_categoria = categoria.valor_categoria

        try:
            await session.commit()
            return categoria_up
        except IntegrityError:
            await session.rollback()  
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, 
                detail='Já existe uma categoria com este nome para o usuário.'
            )

@router.delete('/deletar/{id_categoria}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_categoria(id_categoria: int, db: AsyncSession = Depends(get_session)):
    async with db as session:
        categoria = await session.get(CategoriaModel, id_categoria)
        if not categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
        
        await session.delete(categoria)
        await session.commit()
        return {"detail": "Categoria excluída com sucesso"}
