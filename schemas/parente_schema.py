from pydantic import BaseModel
from typing import Optional

class ParenteBaseSchema(BaseModel):
    grau_parentesco: Optional[str]
    nome: str

class ParenteCreateSchema(ParenteBaseSchema):
    id_usuario: int

class ParenteSchema(ParenteBaseSchema):
    id_parente: int
    id_usuario: int

    class Config:
        orm_mode = True

class ParenteUpdateSchema(ParenteBaseSchema):
    grau_parentesco: Optional[str] = None
    nome: Optional[str] = None

