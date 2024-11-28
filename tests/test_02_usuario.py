import unittest
import pytest
import traceback
from httpx import AsyncClient, ASGITransport
from fastapi import status, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from unittest.mock import AsyncMock, patch

from main import app
from models.usuario_model import UsuarioModel
from tests.config import getValidToken

class TestPostUsuario(unittest.IsolatedAsyncioTestCase):


    @classmethod
    def setUpClass(cls):
        # Configura o patch do get_session compartilhado para todos os testes
        cls.mock_get_session = AsyncMock()
        cls.session_patch = patch(
            "api.v1.endpoints.usuario.get_session", new=AsyncMock(return_value=cls.mock_get_session)
        )
        cls.session_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.session_patch.stop()
            
    async def asyncSetUp(self):
        # Configuração antes de cada teste
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://testserver")
        self.token = getValidToken()


    async def asyncTearDown(self):
        # Limpeza após cada teste
        await self.client.aclose()

    # @pytest.mark.asyncio
    # @patch("api.v1.endpoints.usuario.get_session", new_callable=AsyncMock)
    # @patch("api.v1.endpoints.usuario.handle_db_exceptions")
    # async def test_post_usuario_success(self, mock_handle_exceptions, mock_get_session):
    #     # Configurar mock da sessão
    #     mock_session = AsyncMock()
        
    #     # Simula os dados recebidos
    #     usuario_data = {
    #         "nome_completo": "Usuário Teste",
    #         "data_nascimento": "1990-01-01",
    #         "email": "teste12@example.com",
    #         "senha": "senha123"
    #     }
        
    #     # Fazer a requisição

    #     response = await self.client.post("/api/v1/usuarios/cadastro", json=usuario_data)
        
    #     # Verificações
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    #     # Verificar chamadas de mock
    #     mock_get_session.return_value.__aenter__.assert_called_once()
    #     mock_session.add.assert_called_once()
    #     mock_session.commit.assert_called_once()
    #     mock_session.refresh.assert_called_once()
    #     mock_session.add_all.assert_called_once()
        
    #     # Garantir que handle_db_exceptions não foi chamado
    #     mock_handle_exceptions.assert_not_called()

    @pytest.mark.asyncio
    @patch("api.v1.endpoints.usuario.handle_db_exceptions")
    async def test_post_usuario_duplicado(self, mock_handle_exceptions):
        # Configurar mock da sessão
        mock_session = AsyncMock()
        self.mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Simular IntegrityError para email duplicado
        mock_session.commit.side_effect = IntegrityError(
            statement=None, 
            params=None, 
            orig=Exception("Violação de constraint de email único")
        )
        
        # Configurar mock de handle_db_exceptions para lançar HTTPException esperada
        mock_handle_exceptions.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade no banco de dados: Violação de constraint de email único"
        )
        
        # Simula os dados recebidos
        usuario_data = {
            "nome_completo": "Usuário Teste",
            "data_nascimento": "1990-01-01",
            "email": "teste@example.com",
            "senha": "senha123"
        }
        
        # Fazer a requisição
        response = await self.client.post("/api/v1/usuarios/cadastro", json=usuario_data)
        
        # Verificações
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        


    @pytest.mark.asyncio
    @patch("api.v1.endpoints.usuario.handle_db_exceptions")
    async def test_post_usuario_erro_generico(self, mock_handle_exceptions):

        # Configurar mock da sessão
        mock_session = AsyncMock()
        self.mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Simular erro genérico do SQLAlchemy
        mock_session.commit.side_effect = SQLAlchemyError("Erro genérico de banco de dados")
        
        # Configurar mock de handle_db_exceptions para lançar HTTPException esperada
        mock_handle_exceptions.side_effect = HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro no banco de dados, tente novamente mais tarde."
        )
        
        # Simula os dados recebidos
        usuario_data = {
            "nome_completo": "Usuário Teste",
            "data_nascimento": "1990-01-01",
            "email": "teste@example.com",
            "senha": "senha123"
        }
        
        # Fazer a requisição
        response = await self.client.post("/api/v1/usuarios/cadastro", json=usuario_data)
        
        # Verificações
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @pytest.mark.asyncio
    @patch("api.v1.endpoints.usuario.auth")
    async def test_post_usuario_login(self, mock_auth):

        mock_session = AsyncMock()
        self.mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Simula o sucesso da autenticação
        mock_auth.return_value = AsyncMock(id_usuario=1, nome_completo="Usuário Teste")
        
        # Simula os dados de login
        login_data = {
            "username": "teste@example.com",
            "password": "senha123"
        }
        
        # Fazer a requisição de login
        response = await self.client.post("/api/v1/usuarios/login", data=login_data)
        
        # Verificações
        self.assertIn("access_token", response.json())
        self.assertEqual(response.json()["name"], "Usuário Teste")
            # Imprimir o access_token
        # access_token = response.json().get("access_token")
        access_token = response.json().get("access_token")

        print("Access Token:", access_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    

class TestGetUsuario(unittest.IsolatedAsyncioTestCase):
    
    @classmethod
    def setUpClass(cls):
        # Configura o patch do get_session compartilhado para todos os testes
        cls.mock_get_session = AsyncMock()
        cls.session_patch = patch(
            "api.v1.endpoints.usuario.get_session", new=AsyncMock(return_value=cls.mock_get_session)
        )
        cls.session_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.session_patch.stop()

    async def asyncSetUp(self):
        # Configuração antes de cada teste
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://testserver")
        self.token = getValidToken()


    async def asyncTearDown(self):
        # Limpeza após cada teste
        await self.client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.order(1)
    @patch("api.v1.endpoints.usuario.get_current_user", new_callable=AsyncMock)
    async def test_get_usuario_success(self, mock_get_current_user):
        # Configurar mock da sessão
        mock_session = AsyncMock()
        self.mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Simula um usuário logado com dados específicos
        mock_usuario = AsyncMock(
            nome_completo="Usuário Teste",
            data_nascimento="1990-01-01"
        )
        mock_get_current_user.return_value = mock_usuario
        
        # Fazer a requisição
        headers = {"Authorization": f"Bearer { self.token}"}

        response = await self.client.get("/api/v1/usuarios/listar_usuario", headers=headers)
        
        # Verificações
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    # @pytest.mark.asyncio
    # async def test_update_usuario_success(self):
    #     # Configuração do mock de sessão
    #     mock_session = AsyncMock()
    #     self.mock_get_session.return_value.__aenter__.return_value = mock_session

    #     # Simula um usuário autenticado
    #     mock_usuario = AsyncMock(
    #         id_usuario=1,
    #         nome_completo="Usuário Atualizado",
    #         data_nascimento="1990-01-01"
    #     )
    #     # mock_get_current_user.return_value = mock_usuario

    #     headers = {"Authorization": f"Bearer { self.token}"}

    #     # Fazer a requisição PUT
    #     response = await self.client.put(
    #         "/api/v1/usuarios/editar",
    #         json={"nome_completo": "Novo Nome", "data_nascimento": "1991-02-02"},
    #         headers=headers
    #     )

    #     # Verificações
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.json()["nome_completo"], "Novo Nome")
    #     self.assertEqual(response.json()["data_nascimento"], "1991-02-02")
        
    #     # Verificar chamadas de mock
    #     # mock_get_current_user.assert_called_once()
    #     self.mock_get_session.return_value.__aenter__.assert_called_once()
    #     mock_session.commit.assert_called_once()

        
    
        
    # @pytest.mark.asyncio
    # @patch("api.v1.endpoints.usuario.get_session", new_callable=AsyncMock)
    # async def test_reset_password_error(self, mock_get_session):
    #     # Configuração do mock de sessão
    #     mock_session = AsyncMock()
    #     mock_get_session.return_value.__aenter__.return_value = mock_session

    #     # Fazer a requisição POST com o token e a nova senha
    #     response = await self.client.post(
    #         "/api/v1/usuarios/reset-password/valid_token",
    #         json={"password": "nova_senha"}
    #     )

    #     # Verificações
    #     self.assertEqual(response.json()["detail"], "Token inválido ou expirado: Not enough segments")


    @pytest.mark.asyncio
    @patch("api.v1.endpoints.usuario.send_email_to_reset_password", new_callable=AsyncMock)
    async def test_recover_password_error(self, mock_send_email_to_reset_password):
        # Configurar mock da sessão
        mock_session = AsyncMock()
        self.mock_get_session.return_value.__aenter__.return_value = mock_session

        # Simular a resposta do banco de dados
        mock_usuario = UsuarioModel(id_usuario=1, email="test@example.com")
        mock_session.execute = AsyncMock(return_value=AsyncMock(scalars=AsyncMock(first=AsyncMock(return_value=mock_usuario))))

        # Simular o token gerado
        mock_generate_token_access = AsyncMock(return_value="mock_token")
        patch("api.v1.endpoints.usuario.generate_token_access", mock_generate_token_access).start()

        # Fazer a requisição
        response = await self.client.post(
            "/api/v1/usuarios/recover-password",
            json={"email": "test@example.com"}
        )

