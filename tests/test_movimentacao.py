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
        tolerance = 1e-9
        assert abs(conta.saldo - 50.0) < tolerance, f"Expected saldo to be 50.0, but got {conta.saldo}"


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
        tolerance = 1e-9 
        assert abs(conta.saldo - 150.0) < tolerance, f"Expected saldo to be 50.0, but got {conta.saldo}"

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
        tolerance = 1e-9 
        assert abs(conta.saldo - 150.0) < tolerance, f"Expected saldo to be 50.0, but got {conta.saldo}"

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
        tolerance = 1e-9 
        assert abs(conta.saldo - 50.0) < tolerance, f"Expected saldo to be 50.0, but got {conta.saldo}"
