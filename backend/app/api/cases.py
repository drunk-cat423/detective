from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import async_session
from app.models.case import Case
from sqlalchemy import select

router = APIRouter(prefix="/cases", tags=["cases"])

async def get_db():
    async with async_session() as session:
        yield session

@router.post("/")
async def create_case(name: str, description: str | None = None, db: AsyncSession = Depends(get_db)):
    new_case = Case(name=name, description=description)
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)
    return new_case

@router.get("/")
async def list_cases(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case))
    return result.scalars().all()

@router.delete("/{case_id}",status_code=204)
async  def delete_case(case_id:int,db:AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Case).where(Case.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 先删除所有关联数据（外键约束）
    related_tables = ["agent_messages", "case_skill_link", "connections",
                      "documents", "known_infos", "notes", "skills", "timeline_events"]
    for table in related_tables:
        await db.execute(text(f"DELETE FROM {table} WHERE case_id = :cid"), {"cid": case_id})

    await db.delete(case)
    await db.commit()
    return None