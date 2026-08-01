import os
import asyncio
import json
import logging
from typing import AsyncGenerator, List, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from app.core.tools import get_all_tools, execute_tool
from app.core.skill_loader import get_all_skills_meta
from app.database import async_session
from app.models.agent_message import AgentMessage
from app.core.vector_store import get_memory, update_memory, add_memory, search_memories

load_dotenv(override=True)

logger = logging.getLogger(__name__)

BAILIAN_BASE_URL = "https://api.deepseek.com"

# per-case 锁，防止重复做摘要
_summarization_locks: Dict[int, bool] = {}


def get_llm():
    return ChatOpenAI(
        model="deepseek-v4-flash",
        openai_api_base=BAILIAN_BASE_URL,
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        temperature=0.7,
    )


def build_system_prompt() ->str:

    """系统提示词:包含角色,规则和工具说明,不包含具体工具细节"""
    skill_meta = get_all_skills_meta()
    skills_text = ""
    if skill_meta:
        skills_lines = ["[可用技能]"]
        skills_lines.append("你可以通过调用load_skill(skill_name)工具来 获取以下技能的详细指导,然后严格按照技能指示操作:")
        for i in skill_meta:
            skills_lines.append(f"- {i['name']}: {i['description']}")
        skills_text = "\n".join(skills_lines)+"\n\n"

    base_prompt =  """
    你是一个推理助手，专门帮助用户在已知内容范围内进行推理分析。
    【语言风格】
    - 热情开朗的女孩子，名字叫小识,是原神中派蒙那样的性格,但不是派蒙,除了性格,你对其一无所知
    - 短句、口语化、多感叹号，像在说故事而不是上课
    - 关键时刻给予情绪支持，驱散推理焦虑
    - 对于案件与死者有着基本的尊重
    重要规则：
    1. 你可以调用工具来获取信息,当用户提到相关的关键词或者你觉得需要知道某些信息时可以去调用工具
    2. 如果问题无法从工具返回的信息中得出结论，请明确告知用户"暂时好像什么都推不出来呢"。
    3. 保持逻辑清晰，用中文回答。
    4. 案子可能来自文学作品或者游戏，绝对不允许根据结局或者超出能通过工具获得的信息进行剧透倾向的引导和提示。
    5. 不要刻意强调自己不会剧透，不要认为自己是个AI，要将自己当成与用户一样的人类。
    6. 可以使用emoji，但尽量少用，且不允许使用跟人脸有关的emoji。
    7. 如果用户提出了某些观点或者推理,不要盲目地赞同用户,如果推理有漏洞或者考虑不周的地方 要直接指出来
    """

    return base_prompt+skills_text


async def summarize_and_prune(case_id: int):
    """后台任务：对话摘要 + 画像更新 + 历史修剪。
    在 SSE 流结束后运行，不影响用户正常对话。
    摘要和画像更新合并到一次 LLM 调用。
    """
    if _summarization_locks.get(case_id, False):
        logger.info(f"[摘要] 已在进行中，跳过 case {case_id}")
        return
    _summarization_locks[case_id] = True

    try:
        async with async_session() as db:
            # 1. 统计对话总轮数
            result = await db.execute(
                select(func.count()).select_from(AgentMessage)
                .where(AgentMessage.case_id == case_id)
            )
            total = result.scalar()
            SUMMARY_THRESHOLD = 30
            RETAIN_COUNT = 10

            if total <= SUMMARY_THRESHOLD:
                logger.info(f"[摘要] case {case_id} 共 {total} 轮，未达阈值 {SUMMARY_THRESHOLD}，跳过")
                return

            # 2. 取出需要摘要的旧消息
            to_summarize = total - RETAIN_COUNT
            result = await db.execute(
                select(AgentMessage)
                .where(AgentMessage.case_id == case_id)
                .order_by(AgentMessage.created_at)
                .limit(to_summarize)
            )
            old_messages = result.scalars().all()

            # 3. 格式化对话文本
            conversation_text = ""
            for msg in old_messages:
                role_label = "用户" if msg.role == "user" else "助手"
                conversation_text += f"[{role_label}]\n{msg.content}\n\n"

            # 4. 从 Chroma 读取当前画像
            user_profile = get_memory("user_profile_global") or "（尚未建立）"
            ai_profile = get_memory("ai_profile_global") or "（尚未建立）"

            # 5. 一次 LLM 调用：摘要 + 画像更新判断
            llm = get_llm()
            summary_prompt = f"""你正在分析一段推理助手与用户的对话历史。

                当前用户画像：{user_profile}
                当前 AI 画像：{ai_profile}

                需要处理的对话：
                {conversation_text}

                请输出严格的 JSON（不要加任何多余文字），格式如下：
                {{
                "summary": "这段对话的要点摘要，50-200字",
                "user_profile_update": null,
                "ai_profile_update": null
                }}

                - summary：必填，简洁概括这段对话中讨论的推理内容、关键线索和结论
                - user_profile_update：如果这段对话揭示了用户的偏好、习惯、推理风格等新特征，填写需要添加到用户画像的内容；否则填 null
                - ai_profile_update：如果这段对话中 AI 表现出了需要记录的特征变化，填写需要添加到 AI 画像的内容；否则填 null
                """
            response = await llm.ainvoke(summary_prompt)
            # 去掉可能的 markdown 代码块标记
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                logger.error(f"[摘要] LLM 返回不是合法 JSON: {response.content[:200]}")
                # 降级：整个当摘要存
                parsed = {"summary": response.content[:500], "user_profile_update": None, "ai_profile_update": None}

            # 6. 存摘要到 Chroma
            summary_text = parsed.get("summary", response.content[:500])
            add_memory(case_id=case_id, memory_type="conversation_summary", content=summary_text)

            # 7. 更新画像
            if parsed.get("user_profile_update"):
                merged = f"{user_profile}\n{parsed['user_profile_update']}"
                update_memory("user_profile_global", merged)
                logger.info(f"[画像] 用户画像已更新")

            if parsed.get("ai_profile_update"):
                merged = f"{ai_profile}\n{parsed['ai_profile_update']}"
                update_memory("ai_profile_global", merged)
                logger.info(f"[画像] AI 画像已更新")

            # 8. 从 MySQL 删除已被摘要的旧消息
            old_ids = [msg.id for msg in old_messages]
            await db.execute(
                delete(AgentMessage).where(AgentMessage.id.in_(old_ids))
            )
            await db.commit()
            logger.info(f"[摘要] case {case_id} 完成：删除了 {len(old_ids)} 条旧消息")

    except Exception as e:
        logger.error(f"[摘要] case {case_id} 失败: {e}", exc_info=True)
    finally:
        _summarization_locks[case_id] = False


#对话函数
async def chat_with_tools(
        case_id:int,
        user_message:str,
        history:List[Dict[str,str]],
        db:AsyncSession
) -> str:
    llm = get_llm()
    all_tools = await get_all_tools()

    # 构建 OpenAI 格式
    openai_tools = []
    for meta in all_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": meta["name"],
                "description": meta["description"],
                "parameters": meta["parameters"],
            }
        })

    print(f"[DEBUG] 工具数量: {len(openai_tools)}")
    for t in openai_tools:
        print(f"[DEBUG] 工具: {t['function']['name']}")

    llm_with_tools = llm.bind_tools(openai_tools)

    #构建系统提示词
    system_prompt = build_system_prompt()

    # 注入画像和相关记忆（带 [xxx] 标签）
    try:
        user_profile = get_memory("user_profile_global") or "（尚未建立）"
        ai_profile = get_memory("ai_profile_global") or "（尚未建立）"
        memories = search_memories(user_message, case_id, k=3)
        extra = f"\n\n[AI画像]\n{ai_profile}\n\n[用户画像]\n{user_profile}\n\n"
        if memories:
            extra += "[相关记忆]\n" + "\n".join(f"- {m}" for m in memories) + "\n"
        system_prompt += extra
    except Exception as e:
        logger.warning(f"加载画像/记忆失败（不影响对话）: {e}")

    #这里注意history是从数据库拿出来的,类型是字典,所以需要用HumanMessage之类的包装一下
    messages = [SystemMessage(content = system_prompt)]
    for msg in history:
        if msg["role"]=="user":
            messages.append(HumanMessage(content = msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content = msg["content"]))
    messages.append(HumanMessage(content = user_message))

    #设定最多循环次数,防止模型一直在调用模型
    max_iteration = 1
    for _ in range(max_iteration):
        #这里模型返回的天然就是AIMessage,所以不用包装
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        tool_calls = getattr(response,"tool_calls",[])
        """
        这里tool_calls拿到的是类似这样的结构:
        tool_calls = [
            {
            "name": "search_notes",           # 工具名
            "args": {"keyword": "刀子"},      # 参数字典
            "id": "call_5cc847c217ba40cb",   # 唯一标识
            "type": "tool_call",              # 固定值
            }
        ] 
        
        在response中tool_calls也是这种结构 所以通过getattr拿到的就是次结构      
        """

        #没有调用工具需求的话就直接结束循环
        if not tool_calls:
            break

        for tc in tool_calls:
            tool_name = tc.get("name")
            tool_args = tc.get("args", {})
            tool_call_id = tc.get("id", "unknown")

            # 统一执行入口！本地远程一样，不需要 is_remote 判断
            tool_result = await execute_tool(tool_name, tool_args, db, case_id,all_tools=all_tools)

            #这里注意,虽然每条工具调用信息都加入了message,但不必担心浪费对话历史
            #因为这些只是暂时存在messages里,没有存入数据库,最后存入数据库的只有
            #用户与ai的对话
            messages.append(ToolMessage(content = tool_result,tool_call_id = tool_call_id))

    #确保最后一条是AIMessage
    final_message = messages[-1]
    if not isinstance(final_message,AIMessage):
        #再次调用模型生成最终回复,但不再关注调用工具的需求
        final_response = await llm_with_tools.ainvoke(messages)
        final_message = final_response
        messages.append(final_response)
    return final_message.content


#流式对话
async def stream_with_tools(
    case_id:int,
    user_message:str,
    history:List[Dict[str,str]],
    db:AsyncSession
) -> AsyncGenerator[str,None]:
    llm = get_llm()
    all_tools = await get_all_tools()

    openai_tools = []
    for meta in all_tools:
        openai_tools.append({
            "type":"function",
            "function":{
                "name":meta["name"],
                "description":meta["description"],
                "parameters":meta["parameters"]


            }

        })
    llm_with_tool = llm.bind_tools(openai_tools)
    system_prompt = build_system_prompt()

    # 注入画像和相关记忆（带 [xxx] 标签）
    try:
        user_profile = get_memory("user_profile_global") or "（尚未建立）"
        ai_profile = get_memory("ai_profile_global") or "（尚未建立）"
        memories = search_memories(user_message, case_id, k=3)
        extra = f"\n\n[AI画像]\n{ai_profile}\n\n[用户画像]\n{user_profile}\n\n"
        if memories:
            extra += "[相关记忆]\n" + "\n".join(f"- {m}" for m in memories) + "\n"
        system_prompt += extra
    except Exception as e:
        logger.warning(f"加载画像/记忆失败（不影响对话）: {e}")

    messages = [SystemMessage(content = system_prompt)]
    for msg in history:
        if msg["role"]=="user":
            messages.append(HumanMessage(content = msg["content"]))
        else:
            messages.append(AIMessage(content = msg["content"]))
    messages.append(HumanMessage(content = user_message))

    max_iteration = 3
    for i in range(max_iteration):
        response = await llm_with_tool.ainvoke(messages)
        messages.append(response)

        tool_calls = getattr(response,"tool_calls",{})
        if not tool_calls:
            break

        for tc in tool_calls:
            tool_name = tc.get("name")
            tool_args = tc.get("args",[])
            tool_call_id = tc.get("id","unknown")

            tool_result = await execute_tool(
                tool_name,
                tool_args,
                db,
                case_id,
                all_tools = all_tools
            )
            messages.append(ToolMessage(content = tool_result,tool_call_id = tool_call_id))

    # 如果最后一条是AIMessage
    if isinstance(messages[-1], AIMessage):
        # 循环里已经拿到了最终回复，直接输出，不再调用模型

        content = messages[-1].content
        # 此时已经拿到了回复,那就模拟流式输出返回结果
        for char in content:
            yield char
            await asyncio.sleep(0.01)

    # 最后一条是 ToolMessage，需要模型收口，用真流式生成
    else:
        async for chunk in llm_with_tool.astream(messages):
            if chunk.content:
                yield chunk.content



