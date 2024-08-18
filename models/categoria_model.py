from sqlalchemy import Column, String, BigInteger,  Enum as SqlEnum
from core.configs import settings
from sqlalchemy.orm import relationship
from models.associations_model import reune_table
from models.enums import TipoMovimentacao, TipoCategoria



class CategoriaModel(settings.DBBaseModel):
    __tablename__ = "CATEGORIA"

    id_categoria = Column(BigInteger, primary_key=True)
    nome = Column(String(60), nullable=False)
    descricao = Column(String(500))
    tipo_categoria = Column(SqlEnum(TipoCategoria), nullable=False)
    modelo_categoria = Column(SqlEnum(TipoMovimentacao), nullable=False)

    subcategorias = relationship("SubcategoriaModel", back_populates="categoria")
    movimentacoes = relationship("MovimentacaoModel", back_populates="categoria")
    usuarios = relationship("UsuarioModel", secondary=reune_table, back_populates="categorias")