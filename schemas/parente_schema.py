from pydantic import BaseModel
from typing import Optional

class ParenteSchema(BaseModel):
    id_parente: int
    id_usuario: int

    class Config:
        orm_mode = True

class ParenteSchemaId(ParenteSchema):
    id_usuario: int
    id_parente: int

class ParenteSchemaUpdate(ParenteSchema):
    grau_parentesco: Optional[str] = None
    nome: Optional[str] = None

