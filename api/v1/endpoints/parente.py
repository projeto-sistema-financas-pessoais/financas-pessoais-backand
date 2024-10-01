from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from models.parente_model import ParenteModel
from schemas.parente_schema import ParenteCreateSchema, ParenteSchema, ParenteUpdateSchema
from core.deps import get_session, get_current_user
from models.usuario_model import UsuarioModel

router = APIRouter()

@router.post('/cadastro', response_model=ParenteSchema, status_code=status.HTTP_201_CREATED)
async def create_parente(parente: ParenteCreateSchema, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        if parente.id_usuario != usuario_logado.id_usuario:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não pode criar um parente para outro usuário.")

        query = select(ParenteModel).filter(ParenteModel.nome == parente.nome, ParenteModel.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        parente_existente = result.scalars().first()

        if parente_existente:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Você já possui um parente com este nome.")

        novo_parente = ParenteModel(
            grau_parentesco=parente.grau_parentesco,
            nome=parente.nome,
            id_usuario=usuario_logado.id_usuario  
        )

        session.add(novo_parente)
        try:
            await session.commit()
            return novo_parente
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao criar o parente. Verifique os dados e tente novamente.")

@router.put('/editar/{id_parente}', response_model=ParenteSchema, status_code=status.HTTP_202_ACCEPTED)
async def update_parente(id_parente: int, parente_update: ParenteUpdateSchema, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(ParenteModel).filter(ParenteModel.id_parente == id_parente)
        result = await session.execute(query)
        parente: ParenteModel = result.scalars().unique().one_or_none()

        if not parente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parente não encontrado.")

        if parente.id_usuario != usuario_logado.id_usuario:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para editar este parente.")

        if parente_update.nome:
            query_nome = select(ParenteModel).filter(ParenteModel.nome == parente_update.nome, ParenteModel.id_usuario == usuario_logado.id_usuario, ParenteModel.id_parente != id_parente)
            result_nome = await session.execute(query_nome)
            parente_existente = result_nome.scalars().first()

            if parente_existente:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Já existe um parente com este nome.")

        if parente_update.grau_parentesco is not None:
            parente.grau_parentesco = parente_update.grau_parentesco

        if parente_update.nome is not None:
            parente.nome = parente_update.nome

        try:
            await session.commit()
            return parente
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao atualizar o parente. Verifique os dados e tente novamente.")
        
@router.get('/listar', response_model=list[ParenteSchema], status_code=status.HTTP_200_OK)
async def get_parentes(db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(ParenteModel).filter(ParenteModel.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        parentes = result.scalars().all()

        if not parentes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum parente encontrado.")

        return parentes

@router.get('/visualizar/{id_parente}', response_model=ParenteSchema, status_code=status.HTTP_200_OK)
async def get_parente(id_parente: int, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(ParenteModel).filter(ParenteModel.id_parente == id_parente, ParenteModel.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        parente = result.scalars().one_or_none()

        if not parente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parente não encontrado.")

        return parente

@router.delete('/deletar/{id_parente}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_parente(id_parente: int, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        query = select(ParenteModel).filter(ParenteModel.id_parente == id_parente, ParenteModel.id_usuario == usuario_logado.id_usuario)
        result = await session.execute(query)
        parente = result.scalars().one_or_none()

        if not parente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parente não encontrado.")

        try:
            await session.delete(parente)
            await session.commit()
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao tentar deletar o parente.")