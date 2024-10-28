import api.v1.endpoints
from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from core.security import generate_hash
from core.deps import get_session, get_current_user
from models.usuario_model import UsuarioModel
from models.categoria_model import CategoriaModel
from models.conta_model import ContaModel
from models.parente_model import ParenteModel
from schemas.usuario_schema import UsuarioSchema, UpdateUsuarioSchema
from fastapi.security import OAuth2PasswordRequestForm
from core.auth import auth, generate_token_access

router = APIRouter()


@router.post('/cadastro', status_code=status.HTTP_201_CREATED)
async def post_usuario(usuario: UsuarioSchema, db: AsyncSession = Depends(get_session)):
    novo_usuario: UsuarioModel = UsuarioModel(
        nome_completo=usuario.nome_completo,
        data_nascimento=usuario.data_nascimento,
        email=usuario.email,
        senha=generate_hash(usuario.senha)
    )
    
    async with db as session:
        try:
            session.add(novo_usuario)
            await session.commit()

            await session.refresh(novo_usuario)

            # Criação das categorias pré definidas
            categorias = [
                CategoriaModel(
                    nome="Saúde",
                    tipo_categoria="Fixa",
                    modelo_categoria="Despesa",
                    id_usuario=novo_usuario.id_usuario,
                    valor_categoria=None,
                    nome_icone="health.svg",
                    ativo=True
                ),
                CategoriaModel(
                    nome="Alimentação",
                    tipo_categoria="Fixa",
                    modelo_categoria="Despesa",
                    id_usuario=novo_usuario.id_usuario,
                    valor_categoria=None,
                    nome_icone="food.svg",
                    ativo=True
                ),
                CategoriaModel(
                    nome="Transporte",
                    tipo_categoria="Fixa",
                    modelo_categoria="Despesa",
                    id_usuario=novo_usuario.id_usuario,
                    valor_categoria=None,
                    nome_icone="car.svg",
                    ativo=True
                ),
                CategoriaModel(
                    nome="Educação",
                    tipo_categoria="Fixa",
                    modelo_categoria="Despesa",
                    id_usuario=novo_usuario.id_usuario,
                    valor_categoria=None,
                    nome_icone="book.svg",
                    ativo=True
                ),
                CategoriaModel(
                    nome="Lazer",
                    tipo_categoria="Variável",
                    modelo_categoria="Despesa",
                    id_usuario=novo_usuario.id_usuario,
                    valor_categoria=None,
                    nome_icone="happy.svg",
                    ativo=True
                ),
                CategoriaModel(
                    nome="Salário",
                    tipo_categoria="Fixa",
                    modelo_categoria="Receita",
                    id_usuario=novo_usuario.id_usuario,
                    valor_categoria=None,
                    nome_icone="salary.svg",
                    ativo=True
                ),
                CategoriaModel(
                    nome="Extra",
                    tipo_categoria="Variável",
                    modelo_categoria="Receita",
                    id_usuario=novo_usuario.id_usuario,
                    valor_categoria=None,
                    nome_icone="extra.svg",
                    ativo=True
                )
            ]
            session.add_all(categorias)

            # Criação da conta "Carteira"
            conta_carteira = ContaModel(
                descricao="Conta padrão para despesas em dinheiro físico",
                nome="Carteira",
                nome_icone="6_carteira.svg",
                tipo_conta="Carteira",
                id_usuario=novo_usuario.id_usuario,
                ativo=True,
                saldo=0
            )
            session.add(conta_carteira)

            parente_usuario = ParenteModel(
                nome=novo_usuario.nome_completo,
                email=novo_usuario.email,
                grau_parentesco= "Eu",
                ativo=True,
                id_usuario=novo_usuario.id_usuario
            )
            session.add(parente_usuario)

            await session.commit()

            return novo_usuario
        except IntegrityError:
            await session.rollback() 
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Já existe um usuário com este email cadastrado')
    
# @router.post('/login')
# async def login(login_data: LoginDataSchema, db: AsyncSession = Depends(get_session)):
#     usuario: UsuarioSchema = await auth(email=login_data.email, senha=login_data.senha, db=db)
#     if not usuario:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Dados de acesso incorretos')
#     return JSONResponse(
#         content={
#             "acesso_token": generate_token_access(sub=usuario.id_usuario),
#             "token_tipo": "bearer",
#             "nome": usuario.nome_completo
#         },
#         status_code=status.HTTP_200_OK
#     )
    
@router.post('/login')
async def login(login_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    usuario: UsuarioSchema = await auth(email=login_data.username, senha=login_data.password, db=db)
    print(login_data.username, login_data.password)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Dados de acesso incorretos')
    return JSONResponse(
        content={
            "access_token": generate_token_access(sub=usuario.id_usuario),
            "token_type": "bearer",
            "name": usuario.nome_completo,
            "date_user": str(usuario.data_nascimento)
        },
        status_code=status.HTTP_200_OK
    )



@router.put('/editar/{id_usuario}', status_code=status.HTTP_200_OK)
async def update_usuario(
    id_usuario: int, 
    usuario_update: UpdateUsuarioSchema, 
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    # Verificar se o id_usuario é o mesmo do usuário logado
    if usuario_logado.id_usuario != id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar este usuário."
        )

    async with db as session:
        usuario = await session.get(UsuarioModel, id_usuario)
        
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        # Atualizar os campos
        usuario.nome_completo = usuario_update.nome_completo
        usuario.data_nascimento = usuario_update.data_nascimento
        
        try:
            await session.commit()
            return usuario
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Erro ao atualizar os dados do usuário')
        
@router.delete('/deletar/{id_usuario}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    id_usuario: int, 
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
    # Verificar se o id_usuario é o mesmo do usuário logado
    if usuario_logado.id_usuario != id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para deletar este usuário."
        )

    async with db as session:
        usuario = await session.get(UsuarioModel, id_usuario)
        
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        await session.delete(usuario)
        await session.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
