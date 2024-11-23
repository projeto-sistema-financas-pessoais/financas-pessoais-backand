import pytest
from unittest.mock import MagicMock
from api.v1.endpoints.movimentacao import ajustar_saldo_conta, TipoMovimentacao
class TestAjustarSaldoConta:
    def test_despesa_consolidada(self):
        # Arrange
        conta = MagicMock()
        conta.saldo = 100.0
        
        movimentacao = MagicMock()
        movimentacao.tipoMovimentacao = TipoMovimentacao.DESPESA
        movimentacao.valor = 50.0

        consolidado = True

        # Act
        ajustar_saldo_conta(conta, movimentacao, consolidado)

        # Assert
        assert conta.saldo == 50.0  # 100 - 50

    def test_despesa_nao_consolidada(self):
        # Arrange
        conta = MagicMock()
        conta.saldo = 100.0

        movimentacao = MagicMock()
        movimentacao.tipoMovimentacao = TipoMovimentacao.DESPESA
        movimentacao.valor = 50.0

        consolidado = False

        # Act
        ajustar_saldo_conta(conta, movimentacao, consolidado)

        # Assert
        assert conta.saldo == 150.0  # 100 + 50

    def test_receita_consolidada(self):
        # Arrange
        conta = MagicMock()
        conta.saldo = 100.0

        movimentacao = MagicMock()
        movimentacao.tipoMovimentacao = TipoMovimentacao.RECEITA
        movimentacao.valor = 50.0

        consolidado = True

        # Act
        ajustar_saldo_conta(conta, movimentacao, consolidado)

        # Assert
        assert conta.saldo == 150.0  # 100 + 50

    def test_receita_nao_consolidada(self):
        # Arrange
        conta = MagicMock()
        conta.saldo = 100.0

        movimentacao = MagicMock()
        movimentacao.tipoMovimentacao = TipoMovimentacao.RECEITA
        movimentacao.valor = 50.0

        consolidado = False

        # Act
        ajustar_saldo_conta(conta, movimentacao, consolidado)

        # Assert
        assert conta.saldo == 50.0  # 100 - 50
