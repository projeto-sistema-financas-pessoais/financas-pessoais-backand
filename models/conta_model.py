from sqlalchemy import Column, String, BigInteger, ForeignKey, UniqueConstraint,Boolean
from core.configs import settings
from sqlalchemy.orm import relationship


class ContaModel(settings.DBBaseModel):
    __tablename__ = "CONTA"

    id_conta = Column(BigInteger, primary_key=True) 
    descricao = Column(String(500))
    tipo_conta = Column(String(100))
    id_usuario = Column(BigInteger, ForeignKey("USUARIO.id_usuario"), nullable=False)
    nome = Column(String(500), nullable=False)
    nome_icone = Column(String(100))
    ativo = Column(Boolean, default=True)  # Adicionando a coluna ativo


    usuario = relationship("UsuarioModel", back_populates="contas")
    movimentacoes = relationship("MovimentacaoModel", back_populates="conta")
    faturas = relationship("FaturaModel", back_populates="conta")
    
    __table_args__ = (
        UniqueConstraint('nome', 'id_usuario', name='unique_nome_conta'),
    )
