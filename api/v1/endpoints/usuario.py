import api.v1.endpoints
from fastapi import APIRouter
from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.exc import IntegrityError
from core.security import generate_hash

from core.deps import get_session
from models.usuario_model import UsuarioModel
from schemas.usuario_schema import LoginDataSchema, UsuarioSchema

from fastapi.security import OAuth2PasswordRequestForm

from core.auth import auth, generate_token_access



router = APIRouter()


# POST / Signup
@router.post('/cadastro', status_code=status.HTTP_201_CREATED)
async def post_usuario (usuario: UsuarioSchema, db: AsyncSession = Depends(get_session)):
    
    novo_usuario: UsuarioModel = UsuarioModel(nome_completo = usuario.nome_completo,
                                              data_nascimento = usuario.data_nascimento,
                                              email= usuario.email,
                                              senha = generate_hash(usuario.senha)
                                              )
    async with db as session:
        try:
            session.add(novo_usuario)
            await session.commit()
            return novo_usuario
        except IntegrityError:
             raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Já existe um usuário com este email cadastrado')
    
@router.post('/login')
async def login(login_data: LoginDataSchema, db: AsyncSession = Depends(get_session)):
    usuario: UsuarioSchema = await auth(email=login_data.email, senha=login_data.senha, db=db)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Dados de acesso incorretos')
    return JSONResponse(
        content={
            "acesso_token": generate_token_access(sub=usuario.id_usuario),
            "token_tipo": "bearer",
            "nome": usuario.nome_completo
        },
        status_code=status.HTTP_200_OK
    )
    
@router.post('/login')
async def login(login_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    usuario: UsuarioSchema = await auth(email=login_data.email, senha=login_data.senha, db=db)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Dados de acesso incorretos')
    return JSONResponse(
        content={
            "acesso_token": generate_token_access(sub=usuario.id_usuario),
            "token_tipo": "bearer",
            "nome": usuario.nome_completo
        },
        status_code=status.HTTP_200_OK
    )