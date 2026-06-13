from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.note import Note
from app.models.timeline_event import TimelineEvent
from app.models.known_info import KnownInfo
from app.core.vector_store import search_documents
import os
from mcp import ClientSession
from mcp.client.sse import sse_client


# 工具函数:搜索便签
async def search_notes(keyword: str, db: AsyncSession, case_id: int) -> str:
    result = await db.execute(
        select(Note).where(Note.case_id == case_id, Note.content.contains(keyword))
    )
    notes = result.scalars().all()
    if not notes:
        return f"未找到匹配的便签"
    lines = []
    for n in notes:
        if n.type == 'clue':
            type_label = "线索"
        else:
            type_label = "嫌疑人"
        if n.name:
            name_info = f"({n.name})"
        else:
            name_info = ""
        lines.append(f"· [{type_label}]{name_info}:{n.content}")
    return "\n".join(lines)


# 工具函数:获取时间线信息
async def get_timeline(start_date: Optional[str], end_date: Optional[str], db: AsyncSession, case_id: int) -> str:
    # 注意此处没有await db.execute
    # 因为query并不是查询 只是在构建查询语句
    query = (
        select(TimelineEvent).where(TimelineEvent.case_id == case_id)
        .order_by(TimelineEvent.event_time)
    )
    if start_date:
        query = query.where(TimelineEvent.event_time >= start_date)
    if end_date:
        query = query.where(TimelineEvent.event_time <= end_date)
    result = await db.execute(query)
    events = result.scalars().all()
    if not events:
        return "暂无时间线信息"
    lines = [f"· {e.event_time}:{e.description} " for e in events]
    return "\n".join(lines)


# 工具函数: 获取已知信息
async def get_known_infos(db: AsyncSession, case_id: int) -> str:
    result = await db.execute(
        select(KnownInfo).where(KnownInfo.case_id == case_id)
    )
    infos = result.scalars().all()
    if not infos:
        return "暂无已知信息"
    lines = [f"· {i.content}" for i in infos]
    return "\n".join(lines)


# 工具函数:获取文案(rag方式)
async def search_documents_tool(query: str, db: AsyncSession, case_id: int) -> str:
    result = search_documents(case_id, query, k=5)
    if not result:
        return "无相关文档"
    return "\n-----\n".join(result)


async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """通过MCP SDK调用远程MCP服务"""
    sse_url = os.getenv("MCP_SSE_URL", "https://mcp.api-inference.modelscope.net/fbe678446a5141/sse")

    try:

        async with sse_client(sse_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()


                result = await session.call_tool(tool_name, arguments=arguments)


                if result.content:
                    texts = []
                    for i, item in enumerate(result.content):
                        if hasattr(item, 'text'):
                            texts.append(item.text)

                    final_text = "\n".join(texts) if texts else "无结果"
                    return final_text
                else:
                    print("查找返回内容为空")
                    return "网络搜索未返回任何结果"
    except Exception as e:
        return f"MCP工具调用失败: {str(e)}"


# 元数据(相当于菜单 用于到时构建真正的function calling参数时的参考)
TOOLS_META = [

    {
        "name": "search_notes",
        "description": "根据关键词搜索便签中的信息,关键词为具体名词,如'刀子','动机'",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索用的关键词"}
            },
            "required": ["keyword"],
        },
        "func": search_notes,
    },

    {
        "name": "get_timeline",
        "description": "获取案件的时间线信息,可按日期范围过滤,日期格式为YYYY-MM-DD.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "开始日期(可选)"},
                "end_date": {"type": "string", "description": "结束时间(可选)"},
            },
            "required": [],

        },
        "func": get_timeline,
    },

    {
        "name": "get_known_infos",
        "description": "获取已知信息,无参数",
        "parameters": {
            "type": "object",
            "properties": {},
        },
        "func": get_known_infos,
    },

    {
        "name": "search_documents",
        "description": "在已经上传的文档中检索相关的信息",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索用的查询"}
            },
            "required": ["query"]
        },
        "func": search_documents_tool,

    },

    # mcp远程工具
    {
        "name": "web_search",
        "description": "通过必应搜索引擎搜索中文网络信息,获取案件相关的背景知识、专业术语解释或历史背景",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索用的关键词"},
                "count": {"type": "integer", "description": "返回结果数量,默认10,最多50", "default": 10},
                "offset": {"type": "integer", "description": "从第几条结果开始,用于翻页,默认0", "default": 0}
            },
            "required": ["query"]

        },
        "func": call_mcp_tool,
        "is_remote": True,
        "mcp_tool_name":"bing_search"

    }

]


