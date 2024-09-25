from pydantic import BaseModel
from datetime import date
from typing import Optional

class FaturaCreateSchema(BaseModel):
    data_vencimento: date
    data_fechamento: Optional[date]
    data_pagamento: Optional[date]
    id_conta: int
    id_cartao_credito: int

    class Config:
        orm_mode = True

class FaturaUpdateSchema(BaseModel):
    data_vencimento: Optional[date] = None
    data_fechamento: Optional[date] = None
    data_pagamento: Optional[date] = None
    id_conta: Optional[int] = None
    id_cartao_credito: Optional[int] = None
