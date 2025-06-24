
from fastapi import APIRouter
from .endpoints import user_router, devices_router, logs_router

api_router = APIRouter()

api_router.include_router(user_router.router, prefix="/auth")
api_router.include_router(devices_router.router, prefix="/devices")
api_router.include_router(logs_router.router, prefix="/logs")

