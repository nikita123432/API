from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.routers import api_router
from app.database import engine, Base


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#
#     yield
#     await engine.dispose()
#

app = FastAPI()
app.include_router(api_router, prefix="/api/v1")

# if __name__ == "__main__":
#     uvicorn.run("app.main.app", host="0.0.0.0", port=8000, reload=True)
