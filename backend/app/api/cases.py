from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
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
    await db.delete(case)
    await db.commit()
    return None