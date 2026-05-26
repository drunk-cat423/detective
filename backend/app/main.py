from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Detective Assistant API")

import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

@app.middleware("http")
async def catch_all_errors(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(f"URL: {request.url}\n")
            f.write(traceback.format_exc())
        return JSONResponse(status_code=500, content={"detail": str(e)})


# 1. 必须先加 CORS（确保后面所有路由都生效）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 再注册路由
from app.api.cases import router as cases_router
app.include_router(cases_router)

from app.api.notes import router as notes_router
app.include_router(notes_router)

from app.api.connections import router as connections_router
app.include_router(connections_router)

from app.api.timeline import router as timeline_router
app.include_router(timeline_router)

@app.get("/")
async def root():
    return {"message": "Detective Assistant Backend v2"}

print("main.py 加载完成，所有路由注册完毕")