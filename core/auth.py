
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from models.usuario_model import UsuarioModel
from pydantic import EmailStr
from sqlalchemy.future import select
from typing import Optional, List
from core.security  import check_password
from pytz import timezone
from datetime import datetime, timedelta
from core.configs import settings
from jose import jwt

oauth2_schema = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/usuarios/login"
)

async def auth(email: EmailStr, senha: str, db: AsyncSession) -> Optional[UsuarioModel]:
    async with db as session:
        query = select(UsuarioModel).filter(UsuarioModel.email == email)
        result = await session.execute(query)
        usuario: UsuarioModel = result.scalars().unique().one_or_none()
        if not usuario:
            print("check=>>> user")

            return None
        if not check_password(senha, usuario.senha):
            print("check=>>>", check_password(senha, usuario.senha))
            return None
        
        return usuario
    
    
def _generate_token(tipo_token: str, tempo_vida: timedelta, sub:str) -> str:
    payload = {}
    sp = timezone('America/Sao_Paulo')
    expira = datetime.now(tz=sp) + tempo_vida
    
    payload["type"] = tipo_token
    payload["exp"] = expira
    payload["iat"] = datetime.now(tz=sp)
    payload["sub"] = str(sub)
    
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

def generate_token_access(sub: str) -> str:
    # https://jwt.io
    
    return _generate_token(
        tipo_token='access_token',
        tempo_vida=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        sub = sub
    )
    