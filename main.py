import asyncio
import fcntl
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from api.v1.endpoints.rotina import check_and_send_email
from core.configs import settings
from api.v1.api import api_router
import tempfile
import os
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
LOCK_DIR = tempfile.gettempdir()

# Garantir que o diretório existe com permissões restritas
os.makedirs(LOCK_DIR, mode=0o700, exist_ok=True)

def acquire_file_lock():
    try:
        # Criar um arquivo temporário no diretório dedicado
        lock_file = tempfile.NamedTemporaryFile(dir=LOCK_DIR, delete=False)
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        logger.info(f"Lock adquirido com sucesso no arquivo: {lock_file.name}")
        return lock_file
    except IOError as e:
        logger.info("Outro processo já está executando a tarefa.")
        return None

def release_file_lock(lock_file):
    if lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)  # Libera o lock
        lock_file.close()  # Fecha o arquivo
        os.unlink(lock_file.name)  # Remove o arquivo
        logger.info(f"Lock liberado e arquivo removido: {lock_file.name}")

def executar_funcao_assincrona(loop):
    lock_file = acquire_file_lock()  # Caminho do arquivo de lock
    if lock_file:
        try:
            asyncio.run_coroutine_threadsafe(check_and_send_email(), loop)
        finally:
            release_file_lock(lock_file)


def agendar_execucao(hora: int, minuto: int, loop):
    agora = datetime.now()
    hora_execucao = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
    
    if hora_execucao <= agora:
        hora_execucao += timedelta(days=1)
    
    scheduler.add_job(
        executar_funcao_assincrona,
        'cron',  # Tipo cron para execução recorrente
        hour=hora,
        minute=minuto,
        args=[loop],
        id="execucao_diaria",  # ID único para evitar duplicações
        replace_existing=True  # Substitui a tarefa caso já exista
    )
    current_time = datetime.now().strftime('%H:%M:%S')
    logger.info(f"Tarefa diária agendada para {hora:02d}:{minuto:02d}. Hora atual {current_time}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()  # Loop principal do FastAPI
    scheduler.start()
    agendar_execucao(11, 00,loop)  
    try:
        yield
    finally:
        scheduler.shutdown()

app = FastAPI(title='Finanças Pessoais', lifespan=lifespan)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PUT"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=9000, log_level="info", reload=True)
