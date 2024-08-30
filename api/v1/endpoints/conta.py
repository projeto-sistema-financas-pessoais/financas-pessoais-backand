from fastapi import APIRouter
from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from core.deps import get_current_user, get_session
from models.conta_model import ContaModel
from models.enums import TipoConta
from models.usuario_model import UsuarioModel
from schemas.conta_schema import ContaSchema, ContaSchemaUp

from sqlalchemy.future import select

router = APIRouter()

# POST / Cadastro de conta
@router.post('/cadastro', status_code=status.HTTP_201_CREATED)
async def post_conta(
    conta: ContaSchema, 
    db: AsyncSession = Depends(get_session),  
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    nova_conta: ContaModel = ContaModel(
        descricao=conta.descricao,
        tipo_conta=str (conta.tipo_conta.value),
        id_usuario = usuario_logado.id_usuario,
        nome=conta.nome,
        nome_icone=conta.nome_icone,
        ativo=conta.ativo if conta.ativo is not None else True  # Garantindo o valor padrão
            
    )
    
    async with db as session:
        try:
            session.add(nova_conta)
            await session.commit()
            return nova_conta
        except IntegrityError:
            await session.rollback()  # Garantir rollback em caso de erro
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Já existe uma conta com este nome')
        
# PUT artigo
@router.put('/{conta_id}', response_model=ContaSchema, status_code=status.HTTP_202_ACCEPTED)
async def put_curso (conta_id: int, conta: ContaSchemaUp, db: AsyncSession = Depends(get_session), usuario_logado: UsuarioModel = Depends(get_current_user)):
    async with db as session:

       
        query = select(ContaModel).filter(ContaModel.id_conta == conta_id)
        result = await session.execute(query)
        conta_up: ContaModel = result.scalars().unique().one_or_none()
        
        if conta_up:
            
            if conta_up.id_usuario != usuario_logado.id_usuario:
                raise HTTPException(
                    detail="Você não tem permissão para editar esta conta.",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            if conta.descricao:
                conta_up.descricao = conta.descricao
            if conta.tipo_conta:
                conta_up.tipo_conta = conta.tipo_conta.value

            if conta.nome:
                conta_up.nome = conta.nome
            if conta.nome_icone:
                conta_up.nome_icone = conta.nome_icone
            if conta.ativo is not None:
                conta_up.ativo = bool(conta.ativo)
            
            await session.commit()
                
            return conta_up
        else:
            raise HTTPException (detail= 'Conta não encontrada.', status_code=status.HTTP_404_NOT_FOUND)
