import axios from "axios"

const api = axios.create(
    {
        baseURL:"http://127.0.0.1:8001",
        timeout:10000
    }
)

export const createSuspect = (name:string,age:number,gender:string,crime_scene:string)=>
{
    return api.post(`/suspects/`,{name,age,gender,crime_scene})
}

export const getSuspectList =(status:string,keyword:string)=>
{
    return api.get(`/suspects/`,{params:{status,keyword}})
}

export const getSuspect = (caseId:number) =>
{
    return api.get(`/suspects/${caseId}`)
}

export const updateSuspect = (caseId:number,age:number,crime_scene:string) =>
{
    return api.put(`/suspects/${caseId}/`,{age,crime_scene})
}

export const deleteSuspect = (caseId:number) =>
{
    return api.delete(`/suspects/${caseId}/`)
}

export const uploadSuspectPhoto = (file:File,description:string,caseId:number) =>
{
    const formdata = new FormData()
    formdata.append("file",file)
    formdata.append("description",description)
    return api.post(`/suspects/${caseId}/photos`,formdata)

}



