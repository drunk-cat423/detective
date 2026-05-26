from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteOut
from app.models.connection import Connection


router = APIRouter(prefix="/cases/{case_id}/notes", tags=["notes"])

async def get_db():
    async with async_session() as session:
        yield session

# 获取某个案件的所有便签
@router.get("/", response_model=list[NoteOut])
async def list_notes(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Note).where(Note.case_id == case_id).order_by(Note.created_at)
    )
    return result.scalars().all()

# 创建一个便签
@router.post("/", response_model=NoteOut, status_code=201)
async def create_note(case_id: int, note: NoteCreate, db: AsyncSession = Depends(get_db)):
    new_note = Note(
        case_id=case_id,
        type=note.type,
        content=note.content,
        pos_x=note.pos_x,
        pos_y=note.pos_y,
        width=note.width,
        height=note.height,
        color=note.color,
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note

# 更新便签（位置、内容等）
@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    case_id: int, note_id: int, note_data: NoteUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.case_id == case_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="便签不存在")
    # 只更新传入的字段
    for key, value in note_data.model_dump(exclude_unset=True).items():
        setattr(note, key, value)
    await db.commit()
    await db.refresh(note)
    return note

# 删除便签
@router.delete("/{note_id}", status_code=204)
async def delete_note(case_id: int, note_id: int, db: AsyncSession = Depends(get_db)):
    # 1. 先找到这个便签
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.case_id == case_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="便签不存在")

    # 2. 删除所有引用这个便签的连线（作为起点或终点）
    for conn_cls, col in [(Connection, Connection.from_note_id), (Connection, Connection.to_note_id)]:
        conn_result = await db.execute(
            select(Connection).where(col == note_id, Connection.case_id == case_id)
        )
        for conn in conn_result.scalars().all():
            await db.delete(conn)

    # 3. 再删除便签本身
    await db.delete(note)
    await db.commit()
    return None