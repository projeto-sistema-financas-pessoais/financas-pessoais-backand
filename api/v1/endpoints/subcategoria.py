from fastapi import APIRouter, status, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from core.deps import get_session, get_current_user
from models.subcategoria_model import SubcategoriaModel
from models.categoria_model import CategoriaModel
from schemas.subcategoria_schema import SubcategoriaSchema, SubcategoriaSchemaUpdate
from models.usuario_model import UsuarioModel

router = APIRouter()

@router.post('/cadastro', response_model=SubcategoriaSchema, status_code=status.HTTP_201_CREATED)
async def post_subcategoria(
    subcategoria: SubcategoriaSchema,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        query = select(CategoriaModel).where(
            CategoriaModel.id_categoria == subcategoria.id_categoria,
            CategoriaModel.id_usuario == usuario_logado.id_usuario
        )
        result = await session.execute(query)
        categoria = result.scalars().one_or_none()

        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Categoria não encontrada ou você não tem permissão para adicionar subcategoria"
            )

    nova_subcategoria = SubcategoriaModel(
        nome=subcategoria.nome,
        descricao=subcategoria.descricao,
        id_categoria=subcategoria.id_categoria
    )

    async with db as session:
        try:
            session.add(nova_subcategoria)
            await session.commit()
            return nova_subcategoria
        except IntegrityError:
            await session.rollback()  
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, 
                detail='Já existe uma subcategoria com este nome nesta categoria'
            )

@router.put('/editar/{id_subcategoria}', response_model=SubcategoriaSchema, status_code=status.HTTP_202_ACCEPTED)
async def put_subcategoria(
    id_subcategoria: int,
    subcategoria_update: SubcategoriaSchemaUpdate,
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    async with db as session:
        query = select(SubcategoriaModel).where(SubcategoriaModel.id_subcategoria == id_subcategoria)
        result = await session.execute(query)
        subcategoria: SubcategoriaModel = result.scalars().unique().one_or_none()

        if not subcategoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategoria não encontrada")

        query_categoria = select(CategoriaModel).where(
            CategoriaModel.id_categoria == subcategoria.id_categoria,
            CategoriaModel.id_usuario == usuario_logado.id_usuario
        )
        result_categoria = await session.execute(query_categoria)
        categoria = result_categoria.scalars().one_or_none()

        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Você não tem permissão para editar subcategorias desta categoria"
            )

        if subcategoria_update.nome:
            subcategoria.nome = subcategoria_update.nome
        if subcategoria_update.descricao:
            subcategoria.descricao = subcategoria_update.descricao

        try:
            await session.commit()
            return subcategoria
        except IntegrityError:
            await session.rollback() 
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Já existe uma subcategoria com este nome nesta categoria")
        

  
@router.get('/categoria/{id_categoria}/subcategorias', response_model=List[SubcategoriaSchema], status_code=status.HTTP_200_OK)
async def get_subcategorias_by_categoria(id_categoria: int, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query_categoria = select(CategoriaModel).where(CategoriaModel.id_categoria == id_categoria, CategoriaModel.id_usuario == usuario_logado.id_usuario)
        result_categoria = await session.execute(query_categoria)
        categoria = result_categoria.scalars().one_or_none()

        if not categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada ou não pertence ao usuário logado")
        
        query_subcategorias = select(SubcategoriaModel).where(SubcategoriaModel.id_categoria == id_categoria)
        result_subcategorias = await session.execute(query_subcategorias)
        subcategorias = result_subcategorias.scalars().all()

        return subcategorias

@router.get('/visualizar/{id_subcategoria}', response_model=SubcategoriaSchema, status_code=status.HTTP_200_OK)
async def get_subcategoria(id_subcategoria: int, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(SubcategoriaModel).join(CategoriaModel).where(
            SubcategoriaModel.id_subcategoria == id_subcategoria,
            CategoriaModel.id_usuario == usuario_logado.id_usuario
        )
        result = await session.execute(query)
        subcategoria = result.scalars().unique().one_or_none()

        if not subcategoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategoria não encontrada ou não pertence ao usuário logado")

        return subcategoria

@router.delete('/deletar/{id_subcategoria}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_subcategoria(id_subcategoria: int, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(SubcategoriaModel).join(CategoriaModel).where(
            SubcategoriaModel.id_subcategoria == id_subcategoria,
            CategoriaModel.id_usuario == usuario_logado.id_usuario
        )
        result = await session.execute(query)
        subcategoria = result.scalars().unique().one_or_none()

        if not subcategoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategoria não encontrada ou não pertence ao usuário logado")
        
        await session.delete(subcategoria)
        await session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)