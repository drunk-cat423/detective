from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.auth import create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    message: str = "登录成功"


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """用户登录：验证密码，返回 JWT token"""
    if not settings.auth_password:
        raise HTTPException(status_code=500, detail="服务器未配置登录密码")

    if req.password != settings.auth_password:
        raise HTTPException(status_code=401, detail="密码错误")

    token = create_access_token({"sub": "user"})
    return LoginResponse(token=token)


@router.get("/status")
async def auth_status():
    """查询当前是否开启了登录认证"""
    return {"enabled": settings.auth_enabled}
