
from sqlalchemy import Column, String, BigInteger, ForeignKey, UniqueConstraint,Boolean
from core.configs import settings
from sqlalchemy.orm import relationship


class SubcategoriaModel(settings.DBBaseModel):
    __tablename__ = "SUBCATEGORIA"

    id_subcategoria = Column(BigInteger, primary_key=True)
    descricao = Column(String(500))
    nome = Column(String(60), nullable=False)
    id_categoria = Column(BigInteger, ForeignKey("CATEGORIA.id_categoria"), nullable=False)

    categoria = relationship("CategoriaModel", back_populates="subcategorias")

    __table_args__ = (UniqueConstraint('nome', 'id_categoria', name='SUBCATEGORIA_UK'),)
