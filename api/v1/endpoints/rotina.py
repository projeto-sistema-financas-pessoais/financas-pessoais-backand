import asyncio
from collections import defaultdict
from datetime import datetime
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import logging
import smtplib
from fastapi import logger
import pdfkit
from sqlalchemy import select
from weasyprint import HTML
from core.auth import send_email
from core.deps import get_session
from models.enums import TipoMovimentacao
from models.movimentacao_model import MovimentacaoModel
from models.usuario_model import UsuarioModel
from models.fatura_model import FaturaModel
from models.cartao_credito_model import CartaoCreditoModel
from decouple import config
import io


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(email_data: dict, user_email: str) -> None:
    try:
        # Verifique se os dados de e-mail foram lidos corretamente
        sender_email = config("EMAIL_ADDRESS")
        sender_password = config("EMAIL_PASSWORD")

        print("Endereço de e-mail do remetente:", sender_email)
        print("Senha de aplicativo lida:", sender_password)

        # Configura a mensagem
        msg = MIMEMultipart()
        msg["Subject"] = email_data["email_subject"]
        msg["From"] = sender_email
        msg["To"] = user_email
        msg["Date"] = formatdate(localtime=True)

        # Adicionar o corpo do e-mail
        body = MIMEText(email_data["email_body"], "html", "utf-8")
        msg.attach(body)

        pdf_buffer = io.BytesIO()
        pdf_data = pdfkit.from_string(email_data["email_body"], False, options={"encoding": "UTF-8"})
        pdf_buffer.write(pdf_data)
        pdf_buffer.seek(0)

        # Anexar o PDF
        attachment = MIMEBase("application", "pdf")
        attachment.set_payload(pdf_buffer.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            "attachment; filename=financas.pdf"
        )
        msg.attach(attachment)

        # Conectar ao servidor SMTP do Gmail
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)  # Usa as credenciais
            server.send_message(msg)

    except Exception as e:
        raise Exception(f"Error occurred while sending email: {e}")


async def check_and_send_email():
    try:
        async for session in get_session():
            contas_vencidas, faturas_vencidas = await fetch_vencidas(session)
            usuarios_contas = process_contas(contas_vencidas)
            usuarios_faturas = process_faturas(faturas_vencidas)

            if usuarios_contas or usuarios_faturas:
                await process_and_send_emails(usuarios_contas, usuarios_faturas)
            else:
                logger.info("Nenhuma conta ou fatura vencida foi encontrada.")
    except Exception as e:
        logger.error(f"Erro na execução de check_and_send_email: {e}")
        raise


async def fetch_vencidas(session):
    """Busca contas e faturas vencidas do banco de dados."""
    query_movimentacoes = (
        select(MovimentacaoModel, UsuarioModel.email)
        .join(UsuarioModel, MovimentacaoModel.id_usuario == UsuarioModel.id_usuario)
        .where(
            MovimentacaoModel.data_pagamento < datetime.now(),
            MovimentacaoModel.consolidado == False,
            MovimentacaoModel.id_fatura == None,
        )
    )
    contas_vencidas = await session.execute(query_movimentacoes).all()

    query_faturas = (
        select(FaturaModel, UsuarioModel.email, CartaoCreditoModel)
        .join(UsuarioModel, FaturaModel.id_usuario == UsuarioModel.id_usuario)
        .join(CartaoCreditoModel, FaturaModel.id_cartao == CartaoCreditoModel.id_cartao)
        .where(
            FaturaModel.data_vencimento < datetime.now(),
            FaturaModel.paga == False,
        )
    )
    faturas_vencidas = await session.execute(query_faturas).all()

    return contas_vencidas, faturas_vencidas


def process_contas(contas_vencidas):
    """Agrupa contas vencidas por email do usuário."""
    usuarios_contas = defaultdict(list)
    for conta, user_email in contas_vencidas:
        if user_email:
            usuarios_contas[user_email].append(conta)
        else:
            logger.warning(f"Movimentação '{conta.descricao}' não possui e-mail de usuário.")
    return usuarios_contas


def process_faturas(faturas_vencidas):
    """Agrupa faturas vencidas por email do usuário."""
    usuarios_faturas = defaultdict(list)
    for fatura, user_email, cartao in faturas_vencidas:
        if user_email:
            usuarios_faturas[user_email].append((fatura, cartao))
        else:
            logger.warning(f"Fatura com ID '{fatura.id_fatura}' não possui e-mail de usuário.")
    return usuarios_faturas


async def process_and_send_emails(usuarios_contas, usuarios_faturas):
    """Processa e envia emails para os usuários."""
    all_user_emails = set(usuarios_contas.keys()) | set(usuarios_faturas.keys())
    for user_email in all_user_emails:
        try:
            email_body, total_atraso = build_email_body(user_email, usuarios_contas, usuarios_faturas)
            if email_body:
                logger.info(f"Enviando e-mail para {user_email}...")
                send_email(email_body, user_email)
                logger.info(f"E-mail enviado com sucesso para {user_email}.")
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail para {user_email}: {e}")


def build_email_body(user_email, usuarios_contas, usuarios_faturas):
    """Monta o corpo do e-mail com informações de contas e faturas vencidas."""
    email_body = ""
    total_atraso = 0

    if user_email in usuarios_contas:
        contas = usuarios_contas[user_email]
        email_body += build_table("Contas em atraso", contas, total_atraso)

    if user_email in usuarios_faturas:
        faturas_info = usuarios_faturas[user_email]
        if email_body:
            email_body += "<br>"
        email_body += build_table("Faturas em atraso", faturas_info, total_atraso, is_fatura=True)

    return email_body, total_atraso


def build_table(title, items, total, is_fatura=False):
    """Constrói uma tabela HTML para contas ou faturas."""
    table_html = (
        f"<h4>{title}:</h4>"
        f"<table style='border-collapse: collapse; width: 100%;'>"
        f"<thead>"
        f"<tr style='background-color: #f2f2f2;'>"
    )

    if is_fatura:
        table_html += (
            f"<th style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>Cartão</th>"
            f"<th style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>Data de Vencimento</th>"
            f"<th style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>Valor</th>"
        )
    else:
        table_html += (
            f"<th style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>Descrição</th>"
            f"<th style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>Data de Vencimento</th>"
            f"<th style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>Valor</th>"
        )

    table_html += "</tr></thead><tbody>"
    for item in items:
        if is_fatura:
            fatura, cartao = item
            table_html += (
                f"<tr>"
                f"<td style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>Fatura - {cartao.nome}</td>"
                f"<td style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>{fatura.data_vencimento.strftime('%d/%m/%Y')}</td>"
                f"<td style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>R$ {fatura.fatura_gastos:.2f}</td>"
                f"</tr>"
            )
            total += fatura.fatura_gastos
        else:
            table_html += (
                f"<tr>"
                f"<td style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>{item.descricao}</td>"
                f"<td style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>{item.data_pagamento.strftime('%d/%m/%Y')}</td>"
                f"<td style='border: 1px solid #dddddd; text-align: left; padding: 8px;'>R$ {item.valor:.2f}</td>"
                f"</tr>"
            )
            total += item.valor

    table_html += "</tbody></table>"
    return table_html
