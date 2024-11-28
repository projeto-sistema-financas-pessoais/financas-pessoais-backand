

import unittest
from unittest.mock import patch, MagicMock
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from main import executar_funcao_assincrona, agendar_execucao, scheduler

# Mock para a função check_and_send_email
async def mock_check_and_send_email():
    pass

# Teste
class TestFuncoesAgendamento(unittest.TestCase):
    def setUp(self):
        # Criar um loop de evento
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Substituir a função real por um mock
        patch('api.v1.endpoints.rotina.check_and_send_email', new=mock_check_and_send_email).start()
        patch('apscheduler.schedulers.background.BackgroundScheduler.add_job').start()

    @patch('apscheduler.schedulers.background.BackgroundScheduler.add_job')
    def test_agendar_execucao(self, mock_add_job):
        # Chama a função de agendamento
        agendar_execucao(2, 54, self.loop)

        # Verifica se add_job foi chamado
        mock_add_job.assert_called_once()
        args = mock_add_job.call_args[1]['args']
        
        # Verifica se a função agendada é a correta
        self.assertEqual(args[0], executar_funcao_assincrona)
    
    @patch('api.v1.endpoints.rotina.check_and_send_email')
    def test_executar_funcao_assincrona(self, mock_check_and_send_email):
        # Testa se a função assíncrona é chamada corretamente
        mock_check_and_send_email.return_value = None  # Simula a função sem retorno

        # Executa a função
        executar_funcao_assincrona(self.loop)

        # Verifica se a função check_and_send_email foi chamada
        mock_check_and_send_email.assert_called_once()

if __name__ == "__main__":
    unittest.main()
