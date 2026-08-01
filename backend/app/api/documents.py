from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.core.vector_store import add_documents, delete_documents_by_metadata, list_documents_by_case
from langchain_text_splitters import RecursiveCharacterTextSplitter


router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])

# 方案 C：子块大小。小块做索引、信号聚焦；旧数据大块靠 chunk_len 自动降级（见 vector_store._build_windows）
CHILD_SIZE = 250
CHILD_OVERLAP = 50


def chunk_text(text:str,chunk_size:int = CHILD_SIZE,overlap:int = CHILD_OVERLAP) ->list[str]:
    """
    使用langchain的库只能切割文本,
    优先级:段落->句子->词组 递归切分
    """
    if not text or not text.strip():
        return []

    #实例化切分器
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=[  # 切分优先级（从高到低）
            "\n\n",  # 1. 先按空行（段落）切
            "\n",  # 2. 再按换行切
            "。", "．", ".", "！", "？",  # 3. 按中文/英文句末标点切
            "；", ";",  # 4. 按分号切
            "，", ",",  # 5. 按逗号切
            " ",  # 6. 按空格切
            ""  # 7. 最后按字符硬切
        ],
        is_separator_regex=False,
    )

    #正式切分
    chunks = splitter.split_text(text)

    return [c.strip() for c in chunks if c and c.strip()]

@router.post("/upload")
async def upload_document(
        case_id: int,
        file: UploadFile = File(...),
):
    # 类型判断
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="抱歉,目前仅支持txt文件")

    # 读取内容
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except UnicodeError:
        raise HTTPException(status_code=400, detail="请确认文件编码为utf-8")

    # 分块（子块：小块做索引，检索时按命中块的前后邻居拼上下文窗口）
    chunks = chunk_text(text, chunk_size=CHILD_SIZE, overlap=CHILD_OVERLAP)
    if not chunks:
        raise HTTPException(status_code=400, detail="文件为空或无法分割")

    # 替换语义：同文件名先删旧块再写入，避免重复上传在 Chroma 里残留脏数据
    delete_documents_by_metadata(case_id, file.filename)

    # 只存 Chroma，不再存 MySQL
    metadatas = [
        {"case_id": case_id,
         "filename": file.filename,
         "chunk_index": i,
         "chunk_len": len(chunk)}
        for i, chunk in enumerate(chunks)
    ]
    add_documents(case_id, chunks, metadatas=metadatas)

    return {"filename": file.filename, "chunk_count": len(chunks)}


@router.get("/")
async def list_documents(case_id: int):
    docs = list_documents_by_case(case_id)
    return docs


@router.delete("/{filename}", status_code=204)
async def delete_document(case_id: int, filename: str):
    delete_documents_by_metadata(case_id, filename)
    return None

