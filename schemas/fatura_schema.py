from pydantic import BaseModel
from datetime import date
from typing import Optional

class FaturaSchema(BaseModel):
    id_conta: Optional[int] = None
    class Config:
        from_attributes = True

class FaturaSchemaId(FaturaSchema):
    id_fatura: int
class FaturaSchemaUpdate(BaseModel):
    data_vencimento: Optional[date] = None
    data_fechamento: Optional[date] = None
    data_pagamento: Optional[date] = None
    id_conta: Optional[int] = None
    id_cartao_credito: Optional[int] = None

