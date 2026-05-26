import asyncio
from app.database import async_session
from app.models.timeline_event import TimelineEvent

async def test():
    async with async_session() as session:
        from sqlalchemy import select
        try:
            result = await session.execute(select(TimelineEvent).where(TimelineEvent.case_id == 1))
            print("查询成功:", result.scalars().all())
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(test())