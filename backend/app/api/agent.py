from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import async_session
from app.models.agent_message import AgentMessage
from app.core.agent import chat, chat_stream
from pydantic import BaseModel

router = APIRouter(prefix="/cases/{case_id}/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


async def get_db():
    async with async_session() as session:
        yield session


@router.post("/chat", response_model=ChatResponse)
async def agent_chat(
        case_id: int,
        request: ChatRequest,
        db: AsyncSession = Depends(get_db)
):
    """普通对话"""
    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.case_id == case_id)
        .order_by(AgentMessage.created_at)
    )
    history_messages = result.scalars().all()
    history = [{"role": msg.role, "content": msg.content} for msg in history_messages]

    reply = await chat(case_id, request.message, history, db=db)

    user_msg = AgentMessage(case_id=case_id, role="user", content=request.message)
    db.add(user_msg)

    assistant_msg = AgentMessage(case_id=case_id, role="assistant", content=reply)
    db.add(assistant_msg)

    await db.commit()

    return ChatResponse(reply=reply)


@router.post("/chat/stream")
async def agent_chat_stream(
        case_id: int,
        request: ChatRequest,
        db: AsyncSession = Depends(get_db)
):
    """流式对话"""
    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.case_id == case_id)
        .order_by(AgentMessage.created_at)
    )
    history_messages = result.scalars().all()
    history = [{"role": msg.role, "content": msg.content} for msg in history_messages]

    user_msg = AgentMessage(case_id=case_id, role="user", content=request.message)
    db.add(user_msg)
    await db.commit()

    async def generate():
        full_reply = ""
        async for chunk in chat_stream(case_id, request.message, history, db=db):
            full_reply += chunk
            yield f"data: {chunk}\n\n"

        assistant_msg = AgentMessage(case_id=case_id, role="assistant", content=full_reply)
        db.add(assistant_msg)
        await db.commit()

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history")
async def get_history(case_id: int, db: AsyncSession = Depends(get_db)):
    """获取对话历史"""
    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.case_id == case_id)
        .order_by(AgentMessage.created_at)
    )
    messages = result.scalars().all()
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        }
        for msg in messages
    ]


@router.delete("/history", status_code=204)
async def clear_history(case_id: int, db: AsyncSession = Depends(get_db)):
    """清空对话历史"""
    await db.execute(
        delete(AgentMessage).where(AgentMessage.case_id == case_id)
    )
    await db.commit()
    return None