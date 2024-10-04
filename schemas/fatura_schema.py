from pydantic import BaseModel
from datetime import date
from typing import Optional

class FaturaSchema(BaseModel):
    data_vencimento: date
    data_fechamento: Optional[date]
    data_pagamento: Optional[date]
    id_conta: int
    id_cartao_credito: int

    class Config:
        from_attributes = True
class FaturaSchemaId(FaturaSchema):
    id_cartao_credito: int
    id_conta: int
    id_fatura: int
class FaturaSchemaUpdate(BaseModel):
    data_vencimento: Optional[date] = None
    data_fechamento: Optional[date] = None
    data_pagamento: Optional[date] = None
    id_conta: Optional[int] = None
    id_cartao_credito: Optional[int] = None
