from fastapi import APIRouter
from api.v1.endpoints import usuario, conta, categoria, subcategoria, cartao_de_credito, fatura, parente, movimentacao

api_router = APIRouter()
api_router.include_router(usuario.router, prefix='/usuarios', tags=["usuarios"])
api_router.include_router(conta.router, prefix='/contas', tags=["contas"])
api_router.include_router(categoria.router, prefix='/categorias', tags=["categorias"])
api_router.include_router(subcategoria.router, prefix='/subcategoria', tags=["subcategoria"])
api_router.include_router(cartao_de_credito.router, prefix='/cartaoCredito', tags=["cartao_credito"])
api_router.include_router(fatura.router, prefix='/fatura', tags=["fatura"])
api_router.include_router(parente.router, prefix='/parente', tags=["parente"])
api_router.include_router(movimentacao.router, prefix='/movimentacao', tags=["movimentacao"])

"""
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNzI0NjkyOTM4LCJpYXQiOjE3MjQwODgxMzgsInN1YiI6IjEifQ.qQgD-j4r-1lK8rKAcQ_i-e3xHOfXsZWAKoYPJbmnwmE
"""