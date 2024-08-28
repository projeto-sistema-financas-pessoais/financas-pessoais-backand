from fastapi import APIRouter
from api.v1.endpoints import usuario, conta

api_router = APIRouter()
api_router.include_router(usuario.router, prefix='/usuarios', tags=["usuarios"])
api_router.include_router(conta.router, prefix='/contas', tags=["contas"])



"""
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNzI0NjkyOTM4LCJpYXQiOjE3MjQwODgxMzgsInN1YiI6IjEifQ.qQgD-j4r-1lK8rKAcQ_i-e3xHOfXsZWAKoYPJbmnwmE
"""