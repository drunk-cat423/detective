import axios from 'axios'
import type { InternalAxiosRequestConfig } from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截器：自动携带 token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('auth_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：检测 401 自动跳转登录
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_enabled')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ========== 案件相关 API ==========
export const getCases = () => api.get('/cases/')

export const createCase = (name: string, description?: string) =>
  api.post('/cases/', null, { params: { name, description } })

// ========== 便签相关 API ==========
export const getNotes = (caseId: number) =>
  api.get(`/cases/${caseId}/notes/`)

export const createNote = (caseId: number, data: any) =>
  api.post(`/cases/${caseId}/notes/`, data)

export const updateNote = (caseId: number, noteId: number, data: any) =>
  api.put(`/cases/${caseId}/notes/${noteId}`, data)

export const deleteNote = (caseId: number, noteId: number) =>
  api.delete(`/cases/${caseId}/notes/${noteId}`)

// ========== 连线相关 API ==========
export const getConnections = (caseId: number) =>
  api.get(`/cases/${caseId}/connections/`)

export const createConnection = (caseId: number, data: any) =>
  api.post(`/cases/${caseId}/connections/`, data)

export const updateConnection = (caseId: number, connId: number, data: any) =>
  api.put(`/cases/${caseId}/connections/${connId}`, data)

export const deleteConnection = (caseId: number, connId: number) =>
  api.delete(`/cases/${caseId}/connections/${connId}`)

// ========== 时间线相关 API ==========
export const getTimelineEvents = (caseId: number) =>
  api.get(`/cases/${caseId}/timeline/`)

export const createTimelineEvent = (caseId: number, data: any) =>
  api.post(`/cases/${caseId}/timeline/`, data)

export const updateTimelineEvent = (caseId: number, eventId: number, data: any) =>
  api.put(`/cases/${caseId}/timeline/${eventId}`, data)

export const deleteTimelineEvent = (caseId: number, eventId: number) =>
  api.delete(`/cases/${caseId}/timeline/${eventId}`)

export const moveTimelineEvent = (caseId: number, eventId: number, direction: string) =>
  api.put(`/cases/${caseId}/timeline/${eventId}/move`, null, { params: { direction } })

// ========== Agent 对话 API ==========
export const getAgentHistory = (caseId: number) =>
  api.get(`/cases/${caseId}/agent/history`)

export const sendAgentMessage = (caseId: number, message: string) =>
  api.post(`/cases/${caseId}/agent/chat`, { message })

export const clearAgentHistory = (caseId: number) =>
  api.delete(`/cases/${caseId}/agent/history`)

export const deleteCaseApi = (id: number) => api.delete(`/cases/${id}`)

export const uploadDocument = (caseId:number,file:File) =>{
  const formData = new FormData()
  formData.append('file',file)
  return api.post(`/cases/${caseId}/documents/upload`,formData,{
    headers:{'Content-Type':'multipart/form-data'}
  })
}

export const getDocument = (caseId:number) =>
  api.get(`/cases/${caseId}/documents/`)

export const deleteDocument = (caseId: number, filename: string) =>
  api.delete(`/cases/${caseId}/documents/${encodeURIComponent(filename)}`)

//已知信息相关api
export const getKnownInfos = (caseId:number) =>
  api.get(`/cases/${caseId}/known-infos/`)

export const createKnownInfo = (caseId:number,content:string) =>
  api.post(`/cases/${caseId}/known-infos/`,{content})

export const updateKnownInfo = (caseId:number,infoId:number,content:string) =>
  api.put(`/cases/${caseId}/known-infos/${infoId}`,{content})

export const deleteKnownInfo = (caseId:number,infoId:number) =>
  api.delete(`/cases/${caseId}/known-infos/${infoId}`)
