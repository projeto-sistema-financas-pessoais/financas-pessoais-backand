import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from api.v1.endpoints.rotina import check_and_send_email
from core.configs import settings
from api.v1.api import api_router


scheduler = BackgroundScheduler()

def executar_funcao_assincrona(loop):
    asyncio.run_coroutine_threadsafe(check_and_send_email(), loop)



# Função para agendar a execução em uma hora específica
def agendar_execucao(hora: int, minuto: int, loop):
    agora = datetime.now()
    hora_execucao = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
    
    if hora_execucao <= agora:
        hora_execucao += timedelta(days=1)
    
    scheduler.add_job(executar_funcao_assincrona, 'date', run_date=hora_execucao, args=[loop])
    print(f"Função agendada para: {hora_execucao}")
    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"Horário atual: {current_time}")

# Gerenciador de ciclo de vida do FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()  # Loop principal do FastAPI
    scheduler.start()
    agendar_execucao(11, 00,loop)  
    try:
        yield
    finally:
        scheduler.shutdown()

# Crie a aplicação FastAPI com o ciclo de vida configurado
app = FastAPI(title='Finanças Pessoais', lifespan=lifespan)

# Inclua rotas e middlewares
app.include_router(api_router, prefix=settings.API_V1_STR)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PUT"],
    allow_headers=["*"],
)

# Inicie o servidor com Uvicorn
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=9000, log_level="info", reload=True)
