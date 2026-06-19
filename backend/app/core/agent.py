import os
import asyncio
from typing import AsyncGenerator,List,Dict,Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage,ToolMessage
from app.core.tools import get_all_tools,execute_tool
from app.core.skill_loader import get_all_skills_meta


load_dotenv()

BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def get_llm():
    return ChatOpenAI(
        model="qwen3-max",
        base_url=BAILIAN_BASE_URL,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
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

    #这里注意history是从数据库拿出来的,类型是字典,所以需要用HumanMessage之类的包装一下
    messages = [SystemMessage(content = system_prompt)]
    for msg in history:
        if msg["role"]=="user":
            messages.append(HumanMessage(content = msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content = msg["content"]))
    messages.append(HumanMessage(content = user_message))

    #设定最多循环次数,防止模型一直在调用模型
    max_iteration = 5
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

    messages = [SystemMessage(content = system_prompt)]
    for msg in history:
        if msg["role"]=="user":
            messages.append(HumanMessage(content = msg["content"]))
        else:
            messages.append(AIMessage(content = msg["content"]))
    messages.append(HumanMessage(content = user_message))

    max_iteration = 5
    for i in range(max_iteration):
        response = await llm_with_tool.ainvoke(messages)
        messages.append(response)

        tool_calls = getattr(response,"tool_calls",[])
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

        #确保最后一条是AImessage
    async for chunk in llm.astream(messages):
        content = chunk.content
        if content:
            yield content



