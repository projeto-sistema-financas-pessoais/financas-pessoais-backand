from pydantic import BaseModel, constr
from typing import Optional
from decimal import Decimal

class CartaoCreditoSchema(BaseModel):
    id_cartao_credito: int
    nome: str
    limite: Decimal
    id_usuario: int
    nome_icone: Optional[str]
    ativo: bool

    class Config:
        orm_mode = True

class CartaoCreditoCreateSchema(BaseModel):
    nome: Decimal
    limite: Decimal
    nome_icone: Optional[str]

    class Config:
        orm_mode = True

class CartaoCreditoUpdateSchema(BaseModel):
    nome: Optional[str] = None
    limite: Optional[Decimal] = None
    nome_icone: Optional[str] = None
    ativo: Optional[bool] = None

    class Config:
        orm_mode = True
