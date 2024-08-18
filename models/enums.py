# Enumerations
from enum import Enum


class TipoMovimentacao(Enum):
    DESPESA = "Despesa"
    RECEITA = "Receita"

class FormaPagamento(Enum):
    DEBITO = "Débito"
    CREDITO = "Crédito"
    DINHEIRO = "Dinheiro"

class CondicaoPagamento(Enum):
    A_VISTA = "a vista"
    PARCELADO = "parcelado"
    RECORRENTE = "recorrente"

class TipoCategoria(Enum):
    FIXA = "Fixa"
    VARIAVEL = "Variável"

