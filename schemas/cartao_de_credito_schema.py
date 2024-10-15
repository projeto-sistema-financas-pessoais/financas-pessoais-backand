from datetime import date
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class CartaoCreditoSchema(BaseModel):
    nome: str
    limite: Decimal
    nome_icone: str
    ativo: Optional[bool] = True

    class Config:
        from_attributes = True

class CartaoCreditoSchemaId(CartaoCreditoSchema):
    id_usuario: int
    id_cartao_credito: int
    limite_disponivel: Decimal

class CartaoCreditoSchemaUpdate(CartaoCreditoSchema):
    nome: Optional[str] = None
    limite: Optional[Decimal] = None
    nome_icone: Optional[str] = None
    ativo: Optional[bool] = None

class CartaoCreditoSchemaFatura(CartaoCreditoSchema):
    data_fechamento: date
    data_vencimento: date

