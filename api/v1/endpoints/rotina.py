from collections import defaultdict
from datetime import datetime
import logging
from fastapi import logger
from psycopg2 import sql
from sqlalchemy import select

from core.auth import send_email
from core.deps import get_session
from models.enums import TipoMovimentacao
from models.movimentacao_model import MovimentacaoModel
from models.usuario_model import UsuarioModel
# Configuração de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_send_email():
    try:
        # Corrige o uso de 'async with' se get_session é um gerador
        async for session in get_session():
            query = (
                select(MovimentacaoModel, UsuarioModel.email)
                .join(UsuarioModel, MovimentacaoModel.id_usuario == UsuarioModel.id_usuario)
                .where(
                    MovimentacaoModel.data_pagamento < datetime.now(),
                    MovimentacaoModel.consolidado == False,
                    MovimentacaoModel.id_fatura == None,
                    MovimentacaoModel.tipoMovimentacao == TipoMovimentacao.DESPESA
                )
            )
            
            result = await session.execute(query)
            contas_vencidas = result.all()
            usuarios_contas = defaultdict(list)

            for conta, user_email in contas_vencidas:
                if user_email:
                    usuarios_contas[user_email].append(conta)
                else:
                    logger.warning(f"Movimentação '{conta.descricao}' não possui e-mail de usuário.")

            if usuarios_contas:
                for user_email, contas in usuarios_contas.items():
                    email_body = (
                        "<table border='1' style='border-collapse: collapse; width: 100%;'>"
                        "<tr><th>Descrição</th><th>Data de Vencimento</th><th>Valor</th></tr>"
                        + "".join([
                            f"<tr><td>{conta.descricao}</td><td>{conta.data_pagamento.strftime('%d/%m/%Y')}</td>"
                            f"<td>R$ {conta.valor:.2f}</td></tr>"
                            for conta in contas
                        ]) +
                        "</table>"
                    )

                    total_atraso = sum(conta.valor for conta in contas)

                    email_data = {
                        "email_subject": "Alerta: Contas em Atraso",
                        "email_body": (
                            f"Prezado usuário,<br><br>"
                            f"As seguintes contas estão em atraso:<br>"
                            f"{email_body}<br>"
                            f"<b>Total a Pagar: R$ {total_atraso:.2f}</b><br><br>"
                            f"Por favor, tome as devidas providências.<br><br>"
                            f"Atenciosamente,<br>Equipe Finanças Pessoais!"
                        )
                    }

                    logger.info(f"Enviando e-mail para {user_email}...")
                    await send_email(email_data, user_email)
                    logger.info(f"E-mail enviado com sucesso para {user_email}.")
            else:
                logger.info("Nenhuma conta vencida foi encontrada.")
    except Exception as e:
        logger.error(f"Erro na execução de check_and_send_email: {e}")

    print("Verificando vencimentos e enviando e-mails:", datetime.now())