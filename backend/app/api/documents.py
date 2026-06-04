from fastapi import APIRouter,Depends,HTTPException,UploadFile,File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session
from app.models.document import Document
from app.core.vector_store import add_documents

router = APIRouter(prefix="/cases/{case_id}/documents",tags=["documents"])

async def get_db():
    async with async_session() as session:
        yield session

def chunk_text(text:str,chunk_size:int = 800,overlap:int = 50) ->list[str]:
    if not text:
        return []
    paragraphs = text.split('/n')
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para)+1 <= chunk_size:
            if current_chunk:
                current_chunk += "/n"+para
            else:
                current_chunk = para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if overlap and len(current_chunk)>overlap:
                overlap_text = current_chunk[-overlap:]
            else:
                overlap_text = ""
            if overlap_text:
                current_chunk = overlap_text + "/n" +para
            else:
                current_chunk = para
        if current_chunk:
                chunks.append(current_chunk)
        chunks = [c for c in chunks if c and c.strip()]
        return chunks

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
    metadatas = [{"case_id":case_id,"filename":file.filename,"chunk_index":i,"chunk_len":len(chunk)} for i,chunk in enumerate(chunks) ]
    add_documents(case_id,chunks,metadatas =metadatas)

    #存入mysql数据库
    doc = Document(
        case_id = case_id,
        filename = file.filename,
        content = text,
        chunk_count = len(chunks)
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

