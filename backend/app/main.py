from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.vector_store import preload_reranker
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app:FastAPI):
    preload_reranker()
    yield



app = FastAPI(title="Detective Assistant API",lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#服务启动时加载重排序器




from app.api.cases import router as cases_router
app.include_router(cases_router)

from app.api.notes import router as notes_router
app.include_router(notes_router)

from app.api.connections import router as connections_router
app.include_router(connections_router)

from app.api.timeline import router as timeline_router
app.include_router(timeline_router)

from app.api.agent import router as agent_router
app.include_router(agent_router)

from app.api.documents import router as documents_router
app.include_router(documents_router)

from app.api.known_infos import router as known_infos_router
app.include_router(known_infos_router)

@app.get("/")
async def root():
    return {"message": "Detective Assistant Backend v2"}