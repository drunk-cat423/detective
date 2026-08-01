"""冒烟测试：验证方案 C（子块检索 + 上下文窗口）能召回埋没在长段落里的关键线索。

用法（需在 backend/ 目录下运行，.env 已配置 SILICONFLOW_API_KEY）：
    conda activate detective
    python smoke_rag.py

通过标准：查询"凶器"能召回含"刀""雷切特"的上下文窗口。
"""
import os
import sys

# Windows GBK 控制台无法编码部分字符，强制 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 必须在 import app 之前设置：vector_store 在模块加载时读取该路径
os.environ["CHROMA_PERSIST_DIRECTORY"] = "./chroma_data_smoke"

from app.core import vector_store as vs
from langchain_text_splitters import RecursiveCharacterTextSplitter

CASE_ID = 9999
FILLER = "阳光透过窗子洒在地板上，房间里的陈设整洁而安静，没有人说话，空气仿佛凝固了。"


def make_fixture() -> str:
    """构造测试文本：大量无关叙述，中间埋一条关键线索。"""
    return (
        "\n".join([FILLER] * 20)
        + "\n雷切特先生的口袋里掉出了一把刀，刀刃上还沾着暗红色的痕迹。\n"
        + "\n".join([FILLER] * 20)
    )


def chunk_text(text: str, size: int = 250, overlap: int = 50) -> list[str]:
    """与 documents.py 一致的递归分块。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "．", ".", "！", "？", "；", ";", "，", ",", " ", ""],
        is_separator_regex=False,
    )
    return [c.strip() for c in splitter.split_text(text) if c and c.strip()]


def cleanup() -> None:
    try:
        vs.get_chroma_client().delete_collection(f"case_{CASE_ID}")
    except Exception:
        pass


def test_old_data_degradation() -> None:
    """旧数据（1200 字大块）应降级为单块窗口，不把上下文撑爆（坑 6）。

    直接构造命中块调用 _build_windows，绕开检索的不确定性。
    """
    print("\n=== 旧数据降级测试 ===")
    case_id = 9998
    try:
        vs.get_chroma_client().delete_collection(f"case_{case_id}")
    except Exception:
        pass

    big_chunks = [
        "无关内容甲。" * 200,                          # ~1200 字
        "雷切特口袋里的刀就是凶器。" + "无" * 1180,    # ~1200 字，含线索
        "无关内容乙。" * 200,                          # ~1200 字
    ]
    metas = [
        {"case_id": case_id, "filename": "old.txt", "chunk_index": i, "chunk_len": len(c)}
        for i, c in enumerate(big_chunks)
    ]
    vs.add_documents(case_id, big_chunks, metadatas=metas)

    # 只命中中间那块：若半径未降级会拼上前后两块（~3600 字）
    collection = vs.get_or_create_collection(case_id)
    windows = vs._build_windows(collection, [(big_chunks[1], metas[1])], radius=1)
    assert len(windows) == 1, f"期望 1 个窗口，实际 {len(windows)}"
    assert len(windows[0]) <= 1300, f"旧数据窗口过大（{len(windows[0])} 字），半径未降级"

    print("✅ 通过：旧数据大块自动降级为单块窗口")
    try:
        vs.get_chroma_client().delete_collection(f"case_{case_id}")
    except Exception:
        pass


def main() -> None:
    print("=== 冒烟测试：方案 C 子块检索 + 上下文窗口 ===")
    cleanup()

    text = make_fixture()
    chunks = chunk_text(text)
    metadatas = [
        {"case_id": CASE_ID, "filename": "fixture.txt", "chunk_index": i, "chunk_len": len(c)}
        for i, c in enumerate(chunks)
    ]
    vs.add_documents(CASE_ID, chunks, metadatas=metadatas)
    print(f"已写入 {len(chunks)} 个子块")

    result = vs.search_documents(CASE_ID, "凶器是什么？", k=5)
    print(f"\n检索返回 {len(result)} 个窗口：")
    for i, w in enumerate(result, 1):
        print(f"--- 窗口 {i}（{len(w)} 字）---")
        print(w[:120])
        print()

    joined = "".join(result)
    assert "刀" in joined, "失败：关键线索'刀'没有被召回进窗口"
    assert "雷切特" in joined, "失败：线索上下文（人名）没有进入窗口"
    assert len(joined) >= 500, "失败：窗口过小，没有包含邻居上下文"
    print("✅ 通过：关键线索及其上下文都进入了检索窗口")

    cleanup()
    print("已清理临时数据")

    test_old_data_degradation()


if __name__ == "__main__":
    main()
