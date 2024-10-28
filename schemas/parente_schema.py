from pydantic import BaseModel
from typing import Optional

class ParenteSchema(BaseModel):
    nome: str
    email: str
    grau_parentesco: str
    ativo : Optional[bool] = True

    class Config:
        from_attributes = True

class ParenteSchemaId(ParenteSchema):
    id_usuario: int
    id_parente: int

class ParenteSchemaUpdate(ParenteSchema):
    grau_parentesco: Optional[str] = None
    nome: Optional[str] = None
    email: Optional[str] = None
    ativo : Optional[bool] = True
