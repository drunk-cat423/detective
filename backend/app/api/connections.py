from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session
from app.models.connection import Connection
from app.schemas.connection import ConnectionCreate, ConnectionUpdate, ConnectionOut

router = APIRouter(prefix="/cases/{case_id}/connections", tags=["connections"])

async def get_db():
    async with async_session() as session:
        yield session

@router.get("/", response_model=list[ConnectionOut])
async def list_connections(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Connection).where(Connection.case_id == case_id)
    )
    return result.scalars().all()

@router.post("/", response_model=ConnectionOut, status_code=201)
async def create_connection(
    case_id: int, conn: ConnectionCreate, db: AsyncSession = Depends(get_db)
):
    new_conn = Connection(
        case_id=case_id,
        from_note_id=conn.from_note_id,
        to_note_id=conn.to_note_id,
        label=conn.label,
    )
    db.add(new_conn)
    await db.commit()
    await db.refresh(new_conn)
    return new_conn

@router.put("/{conn_id}", response_model=ConnectionOut)
async def update_connection(
    case_id: int, conn_id: int, conn_data: ConnectionUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Connection).where(Connection.id == conn_id, Connection.case_id == case_id)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连线不存在")
    for key, value in conn_data.model_dump(exclude_unset=True).items():
        setattr(conn, key, value)
    await db.commit()
    await db.refresh(conn)
    return conn

@router.delete("/{conn_id}", status_code=204)
async def delete_connection(case_id: int, conn_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Connection).where(Connection.id == conn_id, Connection.case_id == case_id)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连线不存在")
    await db.delete(conn)
    await db.commit()
    return None