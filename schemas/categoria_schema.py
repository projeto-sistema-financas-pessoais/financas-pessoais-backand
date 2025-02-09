from pydantic import BaseModel, ConfigDict
from models.enums import TipoMovimentacao, TipoCategoria
from typing import Optional
from decimal import Decimal

class CategoriaSchema(BaseModel):
    nome: str
    tipo_categoria: TipoCategoria
    modelo_categoria: TipoMovimentacao
    valor_categoria: Optional[Decimal] = None
    nome_icone: str
    ativo : Optional[bool] = True
    model_config = ConfigDict(from_attributes=True)


class CategoriaSchemaUpdate(BaseModel):
    nome: Optional[str] = None
    tipo_categoria: Optional[TipoCategoria] = None
    modelo_categoria: Optional[TipoMovimentacao] = None
    valor_categoria: Optional[Decimal] = None
    nome_icone: Optional[str] = None
    ativo : Optional[bool] = True
      
class CategoriaSchemaId(CategoriaSchema):
    id_usuario: int
    id_categoria: int
    valor_categoria: Optional[Decimal] = None


