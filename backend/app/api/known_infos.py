from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select ,delete
from app.database import async_session
from app.models.known_info import KnownInfo
from app.schemas.know_infos import KnownInfoUpdate,KnownInfoOut,KnownInfoCreate
from typing import List

router = APIRouter(prefix="/cases/{case_id}/known-infos",tags=["known_infos"])

async def get_db():
    async with async_session() as session:
        yield session

@router.get("/",response_model=List[KnownInfoOut])
async def list_known_infos(case_id:int,db:AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnownInfo).where(KnownInfo.case_id == case_id).order_by(KnownInfo.created_at.desc())
    )
    #db.execute返回的对象是类似<<KnownInfo>>的,scalars的作用是把它变成<KnownInfo>
    #.all()的作用是把多个<KnownInfo>整理成列表
    #router里写了response_model,所以fastapi会根据KnownInfoOut转化数据
    #KnownInfoOut里有个from_attributes,作用就是让fastapi能够读对象的方式读KnownInfo

    return result.scalars().all()


@router.post("/",response_model=KnownInfoOut,status_code=201)
async def create_known_info(
    case_id:int,
    info:KnownInfoCreate,
    db:AsyncSession = Depends(get_db)
):
    new_info = KnownInfo(
        case_id=case_id,
        content = info.content
    )
    """
    这里很想git,add时是告诉数据库追踪这个数据
    commit是提交到数据库,但在提交的瞬间会把主键返回给new_info
    然后refresh通过主键把整条新数据拿出来返回给前端
    """
    db.add(new_info)
    await db.commit()
    await db.refresh(new_info)
    return new_info


@router.put("/{info_id}",response_model=KnownInfoOut)
async def update_known_info(
        case_id:int,
        info_id:int,
        info:KnownInfoUpdate,
        db:AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(KnownInfo).where(KnownInfo.case_id == case_id,KnownInfo.id == info_id)

    )
    known_info = result.scalar_one_or_none()
    if not known_info:
        raise HTTPException(status_code = 404,detail="已知信息不存在")
    known_info.content = info.content
    db.add(known_info)
    await db.commit()
    await db.refresh(known_info)
    return known_info

@router.delete("/{info_id}",status_code=204)
async def delete_known_info(
        case_id:int,
        info_id:int,
        db:AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(KnownInfo).where(KnownInfo.case_id == case_id,KnownInfo.id == info_id)
    )

    known_info = result.scalar_one_or_none()
    if not known_info:
        raise HTTPException(status_code=404,detail="已知信息不存在")

    #这里不用先db.add的原因,可以理解为上面select的时候已经追踪到这个对象了
    await db.delete(known_info)
    await db.commit()
    return None
