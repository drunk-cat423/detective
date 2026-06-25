from fastapi import APIRouter,Depends,HTTPException,UploadFile,File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session
from app.models.document import Document
from app.core.vector_store import add_documents
from langchain_text_splitters import RecursiveCharacterTextSplitter


router = APIRouter(prefix="/cases/{case_id}/documents",tags=["documents"])

async def get_db():
    async with async_session() as session:
        yield session

def chunk_text(text:str,chunk_size:int = 1200,overlap:int = 150) ->list[str]:
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
        case_id :int,
        file : UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    #类型判断
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400,detail = "抱歉,目前仅支持txt文件")

    #读取内容
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except UnicodeError:
        raise HTTPException(status_code=400,detail = "请确认文件编码为utf-8")


    #分块
    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400,detail="文件为空或无法分割")

    #存入chroma,压缩工作在add_documents里完成
    metadatas = [
        {"case_id":case_id,
         "filename":file.filename,
         "chunk_index":i,
         "chunk_len":len(chunk)
         }
         for i,chunk in enumerate(chunks) ]
    add_documents(case_id,chunks,metadatas =metadatas)

    #存入mysql数据库
    doc = Document(
        case_id = case_id,
        filename = file.filename,
        chunk_count = len(chunks),
        content = file.filename
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return {"id":doc.id,"filename":doc.filename,"chunk_count":doc.chunk_count}

@router.get("/")
async def list_documents(case_id:int,db:AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.case_id == case_id).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return [
        {
            "id":d.id,
            "filename":d.filename,
            "chunk_count":d.chunk_count,
            "created_at":d.created_at.isoformat() if d.created_at else None
        }
        for d in docs
    ]

