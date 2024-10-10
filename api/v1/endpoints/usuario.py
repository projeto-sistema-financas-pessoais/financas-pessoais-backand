from fastapi import APIRouter, Request, status, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from core.security import generate_hash
from core.deps import get_session, get_current_user
from models.usuario_model import UsuarioModel
from models.categoria_model import CategoriaModel
from models.conta_model import ContaModel
from schemas.usuario_schema import UsuarioSchema, UpdateUsuarioSchema
from schemas.resetPasswordRequest import ResetPasswordRequest
from schemas.recoverPasswordRequest import RecoverPasswordRequest
from fastapi.security import OAuth2PasswordRequestForm
from core.auth import auth, generate_token_access, decoded_token, send_email_to_reset_password
import jwt
from smtplib import SMTPException  # Para tratamento do envio de email
from sqlalchemy.future import select


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

            # Criação das categorias pré-definidas
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

            await session.commit()
            return novo_usuario
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, 
                detail='Já existe um usuário com este email cadastrado'
            )

@router.post('/login')
async def login(login_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    usuario = await auth(email=login_data.username, senha=login_data.password, db=db)
    
    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Dados de acesso incorretos')
    
    return JSONResponse(
        content={
            "access_token": generate_token_access(sub=usuario.id_usuario),
            "token_type": "bearer",
            "name": usuario.nome_completo
        },
        status_code=status.HTTP_200_OK
    )
from sqlalchemy import text  # Certifique-se de importar a função text

from sqlalchemy.future import select
from fastapi import HTTPException
from models import UsuarioModel  # Certifique-se de que sua model está corretamente importada

from sqlalchemy.future import select
from models import UsuarioModel

@router.post('/reset-password/{token}')
async def reset_password(token: str, 
                         schema: ResetPasswordRequest, 
                         db: AsyncSession = Depends(get_session)):

    try:
        decoded_data = decoded_token(token)
    except jwt.ExpiredSignatureError:
        print("Erro: Token expirado")
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={'message': "Expired Token!"})
    except jwt.InvalidTokenError:
        print("Erro: Token inválido")
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={'message': 'Invalid token'})

    async with db as session:
        try:
            # Recupera o ID do usuário do token e converte para inteiro
            user_id = int(decoded_data['sub'])  # Converte para inteiro

            # Faz a consulta através da model
            result = await session.execute(select(UsuarioModel).where(UsuarioModel.id_usuario == user_id))
            user_data = result.scalars().first()
        except Exception as e:
            print(f"Erro ao consultar o banco de dados: {e}")
            raise HTTPException(status_code=500, detail="Database query failed")

        if user_data:
            # Atualiza a senha usando o valor do schema
            user_data.senha = generate_hash(schema.password)
            await session.commit()
            return JSONResponse(status_code=status.HTTP_200_OK, content={"message": f"Password for user ID {user_data.id_usuario} updated successfully"})
        else:
            print("Erro: Usuário não encontrado.")
    
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={'message': 'Error while validating token'})

@router.post("/recover-password", status_code=status.HTTP_202_ACCEPTED)
async def recover_password(schema: RecoverPasswordRequest, 
                           request: Request, 
                           db: AsyncSession = Depends(get_session)):
    
    async with db as session:
        try:
            print(f"E-mail recebido no schema: {schema.email}")

            query = await session.execute(select(UsuarioModel).filter(UsuarioModel.email == schema.email))
            user_data = query.scalars().first()

            if user_data:
                try:
                    token = generate_token_access(user_data.id_usuario)
                    send_email_to_reset_password(request, user_data, token, True)
                    print("E-mail enviado com sucesso")

                    return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'success'})
                except SMTPException as e:
                    print(f"Erro ao enviar e-mail: {e}")
                    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': 'Error while sending e-mail'})
            else:
                print("Usuário não encontrado no banco de dados")
        except Exception as e:
            print(f"Erro durante a execução da função: {e}")

    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={'message': 'e-mail not found in database'})


@router.put('/editar/{id_usuario}', status_code=status.HTTP_200_OK)
async def update_usuario(
    id_usuario: int, 
    usuario_update: UpdateUsuarioSchema, 
    db: AsyncSession = Depends(get_session),
    usuario_logado: UsuarioModel = Depends(get_current_user)
):
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
