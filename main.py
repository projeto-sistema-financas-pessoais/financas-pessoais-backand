import asyncio
import fcntl
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from api.v1.endpoints.rotina import check_and_send_email
from core.configs import settings
from api.v1.api import api_router


scheduler = BackgroundScheduler()

def acquire_file_lock(file_path):
    try:
        lock_file = open(file_path, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("Lock adquirido com sucesso.")
        
        return lock_file
    except IOError:
        print("Outro processo já está executando a tarefa.")
        return None

def release_file_lock(lock_file):
    
    if lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)  # Libera o lock
        lock_file.close()
        print("Lock liberado.")

def executar_funcao_assincrona(loop):
    lock_file = acquire_file_lock('/tmp/check_and_send_email.lock')  # Caminho do arquivo de lock
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
    
    scheduler.add_job(executar_funcao_assincrona, 'date', run_date=hora_execucao, args=[loop])
    print(f"Função agendada para: {hora_execucao}")
    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"Horário atual: {current_time}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()  # Loop principal do FastAPI
    scheduler.start()
    agendar_execucao(11, 0,loop)  
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
