from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import date, datetime
from models.enums import CondicaoPagamento, FormaPagamento, TipoMovimentacao

class MovimentacaoSchema(BaseModel):
    valor: Decimal
    descricao: Optional[str]
    tipoMovimentacao: TipoMovimentacao
    forma_pagamento: FormaPagamento
    condicao_pagamento: CondicaoPagamento
    datatime: datetime
    quantidade_parcelas: Optional[int]
    consolidado: str
    tipo_recorrencia: Optional[str]
    recorrencia: Optional[str]
    data_pagamento: date
    id_conta: int
    id_categoria: int
    id_fatura: Optional[int]

    class Config:
        orm_mode = True

class MovimentacaoSchemaUpdate(BaseModel):
    valor: Optional[Decimal] = None
    descricao: Optional[str] = None
    tipoMovimentacao: Optional[TipoMovimentacao] = None
    forma_pagamento: Optional[FormaPagamento] = None
    condicao_pagamento: Optional[CondicaoPagamento] = None
    datatime: Optional[datetime] = None
    quantidade_parcelas: Optional[int] = None
    consolidado: Optional[str] = None
    tipo_recorrencia: Optional[str] = None
    recorrencia: Optional[str] = None
    data_pagamento: Optional[date] = None
    id_conta: Optional[int] = None
    id_categoria: Optional[int] = None
    id_fatura: Optional[int] = None

class MovimentacaoSchemaId(MovimentacaoSchema):
    id_fatura: int
    id_conta: int
    id_movimentacao: int