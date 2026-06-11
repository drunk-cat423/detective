from typing import Optional,List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.note import Note
from app.models.timeline_event import TimelineEvent
from app.models.known_info import KnownInfo
from app.core.vector_store import search_documents


#工具函数:搜索便签
async def search_notes(keyword:str,db:AsyncSession,case_id:int) -> str:
    result = await db.execute(
        select(Note).where(Note.case_id == case_id,Note.content.contains(keyword))
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

#工具函数:获取时间线信息
async def get_timeline(start_date:Optional[str],end_date:Optional[str],db:AsyncSession,case_id:int) ->str:
    #注意此处没有await db.execute
    #因为query并不是查询 只是在构建查询语句
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
    lines = [f"· {e.event_time}:{e.description} "for e in events]
    return "\n".join(lines)

#工具函数: 获取已知信息
async def get_known_infos(db:AsyncSession,case_id:int) -> str:
    result = await db.execute(
        select(KnownInfo).where(KnownInfo.case_id == case_id)
    )
    infos = result.scalars().all()
    if not infos:
        return "暂无已知信息"
    lines = [f"· {i.content}" for i in infos]
    return "\n".join(lines)

#工具函数:获取文案(rag方式)
async def search_documents_tool(query:str,db:AsyncSession,case_id:int) -> str:
    result = search_documents(case_id,query,k =5)
    if not result:
        return "无相关文档"
    return"\n-----\n".join(result)

#元数据(相当于菜单 用于到时构建真正的function calling参数时的参考)
TOOLS_META= [

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
            "func": "get_timeline",
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

        }

]


