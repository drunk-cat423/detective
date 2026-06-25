from fastapi import APIRouter,UploadFile,File,Form
from pydantic import BaseModel

router = APIRouter(prefix="/suspects")

class AddSuspect(BaseModel):
    name:str
    age:int
    gender:str
    crime_scene:str

class updateSuspect(BaseModel):
    age:int
    crime_scene:str
@router.post("/")
async def create_suspect(data:AddSuspect):
    result = {
        "id":1,
        "name":data.name,
        "age":data.age,
        "gender":data.gender,
        "crime_scene":data.crime_scene,
        "status":"active",
        "photo_url":"http://127.0.0.1:8001/static/photos/1.jpg"
    }
    return result

@router.get("/")
async def getSuspectList(status:str,keyword:str):
    result = f"status:{status},keywork:{keyword}"
    return result
@router.get("/{id}/")
async def getSuspect(id:int):
    result = {
        "id":id,
        "sql":"select.from ..."
    }
    return result

@router.put("/{id}/")
async def updateSuspect(id:int,data:updateSuspect):
    result = {
        "id":id,
        "age":data.age,
        "crime_scene":data.crime_scene
    }
    return result

@router.delete("/{id}")
async def deleteSuscept(id:int):
    result = {
        f"delete :{id}"
    }
    return None

@router.post("/{id}/photos/")
async def uploadSuspectPhoto(id:int,file:UploadFile = File(...),description:str = Form(...)):
    content = await file.read()
    result = {
        "description":description,
        "filename":file.filename,
        "size":len(content)
    }
    return result













