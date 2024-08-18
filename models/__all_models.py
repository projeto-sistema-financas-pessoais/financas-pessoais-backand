from models.usuario_model import UsuarioModel
from models.conta_model import ContaModel
from models.parente_model import ParenteModel
from models.cartao_credito_model import CartaoCreditoModel
from models.categoria_model import CategoriaModel
from models.fatura_model import FaturaModel
from models.movimentacao_model import MovimentacaoModel
from models.subcategoria_model import SubcategoriaModel
from models.associations_model import reune_table, divide_table


from core.configs import settings

# Coletar metadatas
metadata = settings.DBBaseModel.metadata

__all__ = [
    "reune_table", "divide_table",
    "CartaoCreditoModel", "CategoriaModel", "ContaModel",
    "FaturaModel", "MovimentacaoModel", "ParenteModel",
    "SubcategoriaModel", "UsuarioModel", "metadata"
]
