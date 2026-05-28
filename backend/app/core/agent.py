import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.note import Note
from app.models.timeline_event import TimelineEvent
from app.models.document import Document
from app.models.known_info import KnownInfo
from app.core.vector_store import search_documents

load_dotenv()

BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def get_llm():
    return ChatOpenAI(
        model="qwen3-max",
        base_url=BAILIAN_BASE_URL,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        temperature=0.7,
    )


async def build_system_prompt(case_id: int, db: AsyncSession, user_query: str = "") -> str:
    """构建包含案件全部已知信息的系统提示词（含 RAG 检索）"""

    parts = []

    # 1. 便签
    note_result = await db.execute(
        select(Note).where(Note.case_id == case_id)
    )
    notes = note_result.scalars().all()
    if notes:
        clue_lines = []
        suspect_lines = []
        for n in notes:
            if n.type == "clue":
                clue_lines.append(f"  • {n.content}")
            else:
                suspect_lines.append(f"  • {n.content}")
        if clue_lines:
            parts.append("【线索】\n" + "\n".join(clue_lines))
        if suspect_lines:
            parts.append("【嫌疑人】\n" + "\n".join(suspect_lines))

    # 2. 时间线
    tl_result = await db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.case_id == case_id)
        .order_by(TimelineEvent.event_time)
    )
    timelines = tl_result.scalars().all()
    if timelines:
        tl_lines = [f"  • {t.event_time}: {t.description}" for t in timelines]
        parts.append("【时间线】\n" + "\n".join(tl_lines))

    # 3. 已知信息
    info_result = await db.execute(
        select(KnownInfo).where(KnownInfo.case_id == case_id)
    )
    infos = info_result.scalars().all()
    if infos:
        info_lines = [f"  • {i.content}" for i in infos]
        parts.append("【已知信息】\n" + "\n".join(info_lines))

    # 4. 已上传文本（RAG 检索）
    doc_result = await db.execute(
        select(Document).where(Document.case_id == case_id)
    )
    docs = doc_result.scalars().all()
    if docs and user_query:
        retrieved = search_documents(case_id, user_query, k=5)
        if retrieved:
            parts.append("【相关文本片段】\n" + "\n---\n".join(retrieved))

    context = "\n\n".join(parts) if parts else "暂无已知信息。"

    return f"""你是一个推理助手，专门帮助用户在已知内容范围内进行推理分析。

重要规则：
1. 你只能依据下面【已知内容】中的信息进行分析和回答
2. 绝对不允许使用任何超出这些内容的外部知识或剧透
3. 如果问题无法从已知内容中得出结论，请明确告知用户"根据目前已知信息，无法得出结论"
4. 保持逻辑清晰，用中文回答
5. 可以帮用户：梳理线索、分析动机、找出矛盾点、推测可能性、整理时间线

【已知内容】：
{context}"""


async def chat(case_id: int, user_message: str, history: list = None, db: AsyncSession = None) -> str:
    """普通对话"""
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    llm = get_llm()

    if db:
        system_prompt = await build_system_prompt(case_id, db, user_message)
    else:
        system_prompt = "你是一个推理助手。请用中文回答。"

    messages = [SystemMessage(content=system_prompt)]

    if history:
        for msg in history[-20:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    response = await llm.ainvoke(messages)
    return response.content


async def chat_stream(case_id: int, user_message: str, history: list = None, db: AsyncSession = None) -> AsyncGenerator[
    str, None]:
    """流式对话"""
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    llm = get_llm()

    if db:
        system_prompt = await build_system_prompt(case_id, db, user_message)
    else:
        system_prompt = "你是一个推理助手。请用中文回答。"

    messages = [SystemMessage(content=system_prompt)]

    if history:
        for msg in history[-20:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content