"""
独立测试 - 直接测试必应中文搜索MCP服务
不依赖项目代码，纯粹使用MCP SDK
"""
import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client


async def test_bing_mcp():
    """直接测试必应中文搜索MCP服务"""
    print("=" * 60)
    print("🧪 独立测试必应中文搜索MCP服务")
    print("=" * 60)

    # 必应中文搜索MCP服务地址
    sse_url = "https://mcp.api-inference.modelscope.net/fbe678446a5141/sse"
    print(f"\n🔗 服务地址: {sse_url}")

    try:
        print("\n📡 正在连接MCP服务...")
        async with sse_client(sse_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("✅ 连接成功！\n")

                # 列出所有可用工具
                print("=" * 60)
                print("🔧 可用工具列表")
                print("=" * 60)
                tools = await session.list_tools()
                for tool in tools.tools:
                    print(f"\n  📌 {tool.name}")
                    print(f"     描述: {tool.description}")
                    if tool.inputSchema:
                        print(f"     参数: {json.dumps(tool.inputSchema, ensure_ascii=False, indent=6)}")

                # 测试1: 搜索"氰化物中毒症状"
                print("\n" + "=" * 60)
                print("🔍 测试1: 搜索 '氰化物中毒症状'")
                print("=" * 60)
                result = await session.call_tool(
                    "bing_search",
                    arguments={"query": "氰化物中毒症状", "count": 3}
                )
                if result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            print(item.text[:2000])
                else:
                    print("❌ 无结果")

                # 测试2: 搜索"Python教程"
                print("\n" + "=" * 60)
                print("🔍 测试2: 搜索 'Python教程'")
                print("=" * 60)
                result = await session.call_tool(
                    "bing_search",
                    arguments={"query": "Python教程", "count": 3}
                )
                if result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            print(item.text[:2000])
                else:
                    print("❌ 无结果")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bing_mcp())