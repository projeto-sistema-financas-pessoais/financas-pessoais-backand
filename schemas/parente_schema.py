from pydantic import BaseModel
from typing import Optional

class ParenteSchema(BaseModel):
    nome: str
    grau_parentesco: str

    class Config:
        orm_mode = True

class ParenteSchemaId(ParenteSchema):
    id_usuario: int
    id_parente: int

class ParenteSchemaUpdate(ParenteSchema):
    grau_parentesco: Optional[str] = None
    nome: Optional[str] = None

