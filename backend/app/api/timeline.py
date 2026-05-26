from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session
from app.models.timeline_event import TimelineEvent
from app.schemas.timeline import TimelineEventCreate, TimelineEventUpdate, TimelineEventOut

router = APIRouter(prefix="/cases/{case_id}/timeline", tags=["timeline"])

async def get_db():
    async with async_session() as session:
        yield session

@router.post("/", response_model=TimelineEventOut, status_code=201)
async def create_event(
    case_id: int, event: TimelineEventCreate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TimelineEvent.sort_order)
        .where(TimelineEvent.case_id == case_id)
        .order_by(TimelineEvent.sort_order.desc())
    )
    max_order = result.scalar() or 0

    new_event = TimelineEvent(
        case_id=case_id,
        event_time=event.event_time,
        description=event.description,
        source=event.source,
        sort_order=max_order + 1,
    )
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return new_event

@router.get("/", response_model=list[TimelineEventOut])
async def list_events(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.case_id == case_id)
        .order_by(TimelineEvent.sort_order)
    )
    return result.scalars().all()

@router.put("/{event_id}/move", response_model=TimelineEventOut)
async def move_event(
    case_id: int, event_id: int, direction: str, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TimelineEvent).where(TimelineEvent.case_id == case_id).order_by(TimelineEvent.sort_order)
    )
    events = result.scalars().all()
    idx = next((i for i, e in enumerate(events) if e.id == event_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="事件不存在")

    if direction == "up" and idx > 0:
        events[idx].sort_order, events[idx - 1].sort_order = events[idx - 1].sort_order, events[idx].sort_order
    elif direction == "down" and idx < len(events) - 1:
        events[idx].sort_order, events[idx + 1].sort_order = events[idx + 1].sort_order, events[idx].sort_order

    await db.commit()
    await db.refresh(events[idx])
    return events[idx]

@router.put("/{event_id}", response_model=TimelineEventOut)
async def update_event(
    case_id: int, event_id: int, event_data: TimelineEventUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TimelineEvent).where(TimelineEvent.id == event_id, TimelineEvent.case_id == case_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    for key, value in event_data.model_dump(exclude_unset=True).items():
        setattr(event, key, value)
    await db.commit()
    await db.refresh(event)
    return event

@router.delete("/{event_id}", status_code=204)
async def delete_event(case_id: int, event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TimelineEvent).where(TimelineEvent.id == event_id, TimelineEvent.case_id == case_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    await db.delete(event)
    await db.commit()
    return None