from fastapi import APIRouter, Depends
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