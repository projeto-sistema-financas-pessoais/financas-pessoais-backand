from pydantic import BaseModel
from models.enums import TipoMovimentacao, TipoCategoria
from typing import Optional
from decimal import Decimal

class CategoriaSchema(BaseModel):
    id_categoria: int
    nome: str
    descricao: Optional[str]
    tipo_categoria: TipoCategoria
    modelo_categoria: TipoMovimentacao
    id_usuario: int
    valor_categoria: Decimal
    nome_icone: str


    class Config:
        orm_mode = True

class CategoriaCreateSchema(BaseModel):
    nome: str
    descricao: Optional[str]
    tipo_categoria: TipoCategoria
    modelo_categoria: TipoMovimentacao
    id_usuario: int
    valor_categoria: Decimal
    nome_icone: str


class CategoriaUpdateSchema(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    tipo_categoria: Optional[TipoCategoria] = None
    modelo_categoria: Optional[TipoMovimentacao] = None
    valor_categoria: Optional[Decimal] = None
    nome_icone: Optional[str] = None


class CategoriaSchemaId(CategoriaSchema):
    id_usuario: int
    id_c: int