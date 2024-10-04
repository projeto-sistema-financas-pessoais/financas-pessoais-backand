from pydantic import BaseModel
from typing import Optional

class SubcategoriaSchema(BaseModel):
    nome: str
    descricao: Optional[str]
    id_categoria: int
    class Config:
        from_attributes = True


class SubcategoriaSchemaUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None