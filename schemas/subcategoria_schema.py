from pydantic import BaseModel
from typing import Optional

class SubcategoriaCreateSchema(BaseModel):
    nome: str
    descricao: Optional[str]
    id_categoria: int

class SubcategoriaSchema(SubcategoriaCreateSchema):
    id_subcategoria: int

    class Config:
        orm_mode = True


class SubcategoriaUpdateSchema(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None