import asyncio
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field


# ========== 方式一：手动字典（你的方式）==========

class SearchInput(BaseModel):
    keyword: str = Field(description="搜索关键词")


def build_openai_tools():
    """你的手动方式"""
    return [{
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "根据关键词搜索便签",
            "parameters": SearchInput.model_json_schema(),
        }
    }]


# ========== 方式二：StructuredTool ===========

from langchain_core.tools import StructuredTool


async def search_notes(keyword: str) -> str:
    return f"找到 {keyword}"


tool = StructuredTool.from_function(
    coroutine=search_notes,
    name="search_notes",
    description="根据关键词搜索便签",
    args_schema=SearchInput,
)


# ========== 测试 ===========

async def test_both():
    llm = ChatOpenAI(
        model="qwen3-max",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        temperature=0.7,
    )

    print("=" * 50)
    print("方式一：手动字典")
    print("=" * 50)

    llm_1 = llm.bind_tools(build_openai_tools())
    response_1 = await llm_1.ainvoke([HumanMessage(content="搜索刀子的线索")])

    tc_1 = response_1.tool_calls[0]
    print(f"tool_calls[0] 类型: {type(tc_1)}")
    print(f"isinstance(dict): {isinstance(tc_1, dict)}")
    print(f"tc['name']: {tc_1['name']}")
    print(f"tc.get('args'): {tc_1.get('args')}")
    print(f"hasattr .name: {hasattr(tc_1, 'name')}")
    if hasattr(tc_1, 'name'):
        print(f"tc.name: {tc_1.name}")
    print()

    print("=" * 50)
    print("方式二：StructuredTool")
    print("=" * 50)

    llm_2 = llm.bind_tools([tool])
    response_2 = await llm_2.ainvoke([HumanMessage(content="搜索刀子的线索")])

    tc_2 = response_2.tool_calls[0]
    print(f"tool_calls[0] 类型: {type(tc_2)}")
    print(f"isinstance(dict): {isinstance(tc_2, dict)}")
    print(f"tc['name']: {tc_2['name']}")
    print(f"tc.get('args'): {tc_2.get('args')}")
    print(f"hasattr .name: {hasattr(tc_2, 'name')}")
    if hasattr(tc_2, 'name'):
        print(f"tc.name: {tc_2.name}")
    print()


if __name__ == "__main__":
    asyncio.run(test_both())