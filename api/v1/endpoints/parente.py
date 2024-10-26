from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from models.parente_model import ParenteModel
from schemas.parente_schema import ParenteSchema, ParenteSchemaUpdate, ParenteSchemaId
from core.deps import get_session, get_current_user
from models.usuario_model import UsuarioModel


router = APIRouter()

@router.post('/cadastro', status_code=status.HTTP_201_CREATED)
async def post_parente(
    parente: ParenteSchema, 
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    if parente.nome.lower() == usuario_logado.nome_completo.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido cadastrar um parente com o nome do usuário."
        )
    
    novo_parente: ParenteModel = ParenteModel(
        nome=parente.nome,
        grau_parentesco=parente.grau_parentesco,
        id_usuario=usuario_logado.id_usuario,
        ativo=parente.ativo
    )
    
    async with db as session:
        try:
            session.add(novo_parente)
            await session.commit()
            return novo_parente
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Parente já cadastrada para este usuário")

@router.put('/editar/{id_parente}', response_model=ParenteSchemaId, status_code=status.HTTP_202_ACCEPTED)
async def update_parente(id_parente: int, parente_update: ParenteSchemaUpdate, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
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
            
        if parente_update.ativo is not None:
            parente.ativo = bool(parente_update.ativo)

            
            
     

        try:
            await session.commit()
            return parente
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao atualizar o parente. Verifique os dados e tente novamente.")
        
@router.get('/listar/{somente_ativo}', response_model=list[ParenteSchemaId], status_code=status.HTTP_200_OK)
async def get_parentes(somente_ativo: bool, db: AsyncSession = Depends(get_session), 
                       usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:
        try:
            query = select(ParenteModel).where(
                ParenteModel.id_usuario == usuario_logado.id_usuario,
                ParenteModel.ativo if somente_ativo else True
            )

            result = await session.execute(query)
            
            parentes: List[ParenteSchemaId] = result.scalars().all()
            if not parentes:
                print("Nenhum parente encontrado.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum parente encontrado.")

            return parentes

        except Exception as e:
            # Capturando e imprimindo qualquer erro que ocorrer
            print(f"Erro durante a execução: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao listar parentes.")


@router.get('/visualizar/{id_parente}', response_model=ParenteSchemaId, status_code=status.HTTP_200_OK)
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