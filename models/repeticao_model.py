from core.configs import settings
from sqlalchemy import Column, String, BigInteger, ForeignKey, Date, DECIMAL
from sqlalchemy.orm import relationship

class RepeticaoModel(settings.DBBaseModel):
    __tablename__ = "REPETICAO"

    id_repeticao = Column(BigInteger, primary_key=True)
    quantidade_parcelas = Column(BigInteger, nullable=False)
    tipo_recorrencia = Column(String(100), nullable=False)
    valor_total = Column(DECIMAL, nullable=False)
    data_inicio = Column(Date, nullable=False)

    movimentacoes = relationship("MovimentacaoModel", back_populates="repeticao")
