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
from pydantic import BaseModel,Field
from app.core.skill_loader import load_skill_content



MCP_SERVER_URL = os.getenv(
    "MCP_SSE_URL",
    "https://mcp.api-inference.modelscope.net/fbe678446a5141/sse"
)


#========================此处使用的Field可简单认为是对参数进行一些设置,以便后面直接注入TOOLS_META中==========================
#================所以Field并没有生成openai需要的json格式,只是注释参数,生成json格式是agent.py文件中的.model_json_schema完成的==========
class SearchNotesInput(BaseModel):
    """search_notes 工具的参数（LLM 只需要填这些）"""
    keyword: str = Field(description="搜索用的关键词，如'刀子'、'动机'")

class TimelineInput(BaseModel):
    """get_timeline 工具的参数"""
    start_date: Optional[str] = Field(
        default=None, description="开始日期，格式YYYY-MM-DD（可选）"
    )
    end_date: Optional[str] = Field(
        default=None, description="结束日期，格式YYYY-MM-DD（可选）"
    )

class KnownInfosInput(BaseModel):
    """get_known_infos 工具无参数，但保留空模型统一处理"""
    pass

class SearchDocumentsInput(BaseModel):
    """search_documents 工具的参数"""
    query: str = Field(description="检索用的查询语句")

class WebSearchInput(BaseModel):
    """web_search 工具的参数"""
    query: str = Field(description="搜索用的关键词")
    count: int = Field(default=10, description="返回结果数量，默认10，最多50")
    offset: int = Field(default=0, description="从第几条结果开始，用于翻页，默认0")

class LoadSkillInput(BaseModel):
    skill_name : str = Field(description="要加载的技能名称,例如'motivation_analysis'")



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

#工具函数: 加载技能的详细信息,将技能披露当作工具
async def load_skill(skill_name:str,db:AsyncSession=None,case_id:int = None)-> str:
    """加载技能的详细内容,技能名称来自系统提示此中展示的"""
    try:
        content = load_skill_content(skill_name)
        return content
    except ValueError as e:
        return f"错误: {str(e)}"



#加载远程工具列表
# async def load_remote_tools() -> list[dict]:
#     try:
#         async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
#             async with ClientSession(read_stream, write_stream) as session:
#                 await session.initialize()
#                 result = await session.list_tools()
#                 mcp_tools = result.tools
#                 remote_tools = []
#                 for t in mcp_tools:
#                     remote_tools.append({
#                         "name": t.name,
#                         "description": t.description,
#                         "parameters": t.inputSchema,
#                         "func": call_mcp_tool,
#                         "is_remote": True,
#                     })
#                 return remote_tools
#
#     except Exception as e:
#         print(f"[MCP] 加载远程工具失败: {type(e).__name__}: {e}")
#         import traceback
#         traceback.print_exc()
#         return []




# ========== 通用远程执行函数 ==========
#效果不稳定 暂时取消

# async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
#     """执行远程 MCP 工具调用"""
#     try:
#         async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
#             async with ClientSession(read_stream, write_stream) as session:
#                 await session.initialize()
#                 result = await session.call_tool(tool_name, arguments=arguments)
#
#                 if result.content:
#                     texts = [item.text for item in result.content if hasattr(item, 'text')]
#                     return "\n".join(texts) if texts else "无结果"
#                 return "网络搜索未返回任何结果"
#
#     except Exception as e:
#         return f"MCP工具调用失败: {str(e)}"


# 元数据(相当于菜单 用于到时构建真正的function calling参数时的参考)
LOCAL_TOOLS_META = [
    {
        "name": "search_notes",
        "description": "根据关键词搜索便签中的信息，关键词为具体名词，如'刀子'、'动机'",
        "parameters": SearchNotesInput.model_json_schema(),  # ← 生成 JSON Schema 给 LLM
        "input_model": SearchNotesInput,                      # ← 保留 Pydantic 模型，用于校验
        "func": search_notes,
        "is_remote": False,
    },
    {
        "name": "get_timeline",
        "description": "获取案件的时间线信息，可按日期范围过滤，日期格式为YYYY-MM-DD",
        "parameters": TimelineInput.model_json_schema(),
        "input_model": TimelineInput,
        "func": get_timeline,
        "is_remote": False,
    },
    {
        "name": "get_known_infos",
        "description": "获取已知信息，无参数",
        "parameters": KnownInfosInput.model_json_schema(),
        "input_model": KnownInfosInput,
        "func": get_known_infos,
        "is_remote": False,
    },
    {
        "name": "search_documents",
        "description": "在已经上传的文档中检索相关的信息",
        "parameters": SearchDocumentsInput.model_json_schema(),
        "input_model": SearchDocumentsInput,
        "func": search_documents_tool,
        "is_remote": False,
    },
    {
        "name":"load_skill",
        "description":"加载特定技能的详细描述.当你认为某个技能有助于解决用户的问题时,调用此工具",
        "parameters":LoadSkillInput.model_json_schema(),
        "input_model":LoadSkillInput,
        "func":load_skill,
        "is_remote":False,
    }
]


_tools_cache: list[dict] = None

async def get_all_tools() -> list[dict]:
    """获取所有工具，有缓存则复用，避免每次请求都连 MCP"""
    # global _tools_cache
    # if _tools_cache is None:
    #     remote_tools = await load_remote_tools()
    #     _tools_cache = LOCAL_TOOLS_META + remote_tools
    # return _tools_cache
    return LOCAL_TOOLS_META
async def refresh_tools() -> list[dict]:
    """手动刷新工具列表（MCP 服务器工具变更时调用）"""
    global _tools_cache
    _tools_cache = None
    return await get_all_tools()

async def execute_tool(
        tool_name: str,
        arguments: dict,
        db: AsyncSession,
        case_id: int,
        all_tools: list[dict] = None  # ← 新增：可选传入工具列表
) -> str:
    """
    统一执行入口。
    如果传入 all_tools 则直接使用，否则重新获取。
    """
    # 查找工具
    if all_tools is None:
        all_tools = await get_all_tools()  # ← 没传才重新获取

    tool_meta = None
    for meta in all_tools:
        if meta["name"] == tool_name:
            tool_meta = meta
            break

    if not tool_meta:
        return f"未找到工具: {tool_name}"


    # 执行
    try:
        if tool_meta.get("is_remote", False):
            return await tool_meta["func"](tool_name, arguments)
        else:
            return await tool_meta["func"](**arguments, db=db, case_id=case_id)
    except Exception as e:
        return f"工具执行失败: {str(e)}"

