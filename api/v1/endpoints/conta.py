from fastapi import APIRouter
from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from core.deps import get_current_user, get_session
from models.conta_model import ContaModel
from models.usuario_model import UsuarioModel
from schemas.conta_schema import ContaSchema
router = APIRouter()

# POST / Cadastro de conta
@router.post('/cadastro', status_code=status.HTTP_201_CREATED)
async def post_conta(
    conta: ContaSchema, 
    db: AsyncSession = Depends(get_session),  
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    nova_conta: ContaModel = ContaModel(
        nome=conta.nome,
        nome_icone=conta.nome_icone,
        descricao=conta.descricao,
        tipo_conta=conta.tipo_conta,
    )
    
    async with db as session:
        try:
            session.add(nova_conta)
            await session.commit()
            return nova_conta
        except IntegrityError:
            await session.rollback()  # Garantir rollback em caso de erro
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Já existe uma conta com este nome')