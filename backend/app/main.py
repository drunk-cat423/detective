from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.auth import get_current_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Detective Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 公开路由（无需登录） =====
from app.api.auth import router as auth_router
app.include_router(auth_router)

# ===== 受保护路由（需要登录，通过 include_router 注入 auth 依赖） =====
auth_deps = [Depends(get_current_user)]

from app.api.cases import router as cases_router
app.include_router(cases_router, dependencies=auth_deps)

from app.api.notes import router as notes_router
app.include_router(notes_router, dependencies=auth_deps)

from app.api.connections import router as connections_router
app.include_router(connections_router, dependencies=auth_deps)

from app.api.timeline import router as timeline_router
app.include_router(timeline_router, dependencies=auth_deps)

from app.api.agent import router as agent_router
app.include_router(agent_router, dependencies=auth_deps)

from app.api.documents import router as documents_router
app.include_router(documents_router, dependencies=auth_deps)

from app.api.known_infos import router as known_infos_router
app.include_router(known_infos_router, dependencies=auth_deps)


@app.get("/")
async def root():
    return {"message": "Detective Assistant Backend v2"}
