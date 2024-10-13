from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional
from datetime import date, datetime
from models.enums import CondicaoPagamento, FormaPagamento, TipoMovimentacao, TipoRecorrencia

class MovimentacaoSchema(BaseModel):
    valor: Decimal
    descricao: Optional[str]
    tipoMovimentacao: TipoMovimentacao
    forma_pagamento: FormaPagamento
    condicao_pagamento: CondicaoPagamento
    datatime: Optional[datetime]
    quantidade_parcelas: Optional[int]
    consolidado: bool
    tipo_recorrencia: Optional[str]
    parcela_atual: Optional[str]
    data_pagamento: date
    id_conta: int
    id_categoria: int
    id_fatura: Optional[int] 

    class Config:
        from_attributes = True

class MovimentacaoSchemaUpdate(BaseModel):
    valor: Optional[Decimal] = None
    descricao: Optional[str] = None
    tipoMovimentacao: Optional[TipoMovimentacao] = None
    forma_pagamento: Optional[FormaPagamento] = None
    condicao_pagamento: Optional[CondicaoPagamento] = None
    datatime: Optional[datetime] = None
    quantidade_parcelas: Optional[int] = None
    consolidado: Optional[bool] = None
    tipo_recorrencia: Optional[str] = None
    # parcela_atual: Optional[str] = None
    data_pagamento: Optional[date] = None
    id_conta: Optional[int] = None
    id_categoria: Optional[int] = None
    id_fatura: Optional[int] = None

class MovimentacaoSchemaId(MovimentacaoSchema):

    id_movimentacao: int
   
class MovimentacaoSchemaTransferencia(BaseModel):
    valor: int
    descricao: str
    id_conta_atual: int
    id_conta_transferencia: int
    datatime: datetime 
    data_pagamento: date
    class Config:
        from_attributes = True

class MovimentacaoSchemaReceita(BaseModel):
    valor: Decimal
    descricao: str
    id_categoria: int
    id_conta: Optional[int] = None
    condicao_pagamento : CondicaoPagamento
    tipo_recorrencia: TipoRecorrencia
    # recorrencia: str
    datatime: datetime
    data_pagamento: date
    consolidado: bool

    class Config:
        from_attributes = True

class ParenteResponse(BaseModel):
    id_parente: int
    valor_parente: Decimal

class MovimentacaoSchemaDespesa(MovimentacaoSchemaReceita):
  forma_pagamento: FormaPagamento
  id_financeiro: int
  quantidade_parcelas : int
  divide_parente: List[ParenteResponse]


class IdMovimentacaoSchema(BaseModel):
    id_categoria: int

