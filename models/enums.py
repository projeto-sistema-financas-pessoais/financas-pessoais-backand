# Enumerations
from enum import Enum

    
class TipoMovimentacao(str, Enum):
    DESPESA = "Despesa"
    RECEITA = "Receita"
    TRANSFERENCIA = "Transferencia"

class FormaPagamento(str, Enum):
    DEBITO = "Débito"
    CREDITO = "Crédito"
    DINHEIRO = "Dinheiro"

class CondicaoPagamento(str, Enum):
    A_VISTA = "À vista"
    PARCELADO = "Parcelado"
    RECORRENTE = "Recorrente"

class TipoCategoria(str, Enum):
    FIXA = "Fixa"
    VARIAVEL = "Variável"
    
class TipoConta(str, Enum):
    CORRENTE = "Corrente"
    POUPANCA = "Poupança"
    CONTA_PAGAMENTO = "Conta de pagamento"
    CARTEIRA = "Carteira"
    CONTA_SALARIO = "Conta Salário"

class TipoRecoorencia(str, Enum):
    ANUAL = "Anual"
    SEMESTRAL = "Semestral"
    TRIMESTRAL = "Trimestral"
    BIMESTRAL = "Bimestral"
    MENSAL = "Mensal"
    QUINZENAL = "Quinzenal"
    SEMANAL = "Semanal"
    DIÁRIO = "Diário"
    
