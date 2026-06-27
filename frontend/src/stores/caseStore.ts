import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getNotes,
  getConnections,
  getTimelineEvents,
  getAgentHistory,
  getDocument,
  getKnownInfos,
  createNote,
  updateNote,
  deleteNote,
  createConnection,
  deleteConnection,
  createTimelineEvent,
  updateTimelineEvent,
  deleteTimelineEvent,
  moveTimelineEvent,
  uploadDocument,
} from '@/api'

export const useCaseStore = defineStore('case', () => {
  // ========== State ==========
  const currentCaseId = ref<number | null>(null)
  const notes = ref<any[]>([])
  const connections = ref<any[]>([])
  const timelineEvents = ref<any[]>([])
  const documents = ref<any[]>([])
  const knownInfos = ref<any[]>([])
  const messages = ref<any[]>([])
  
  const activeTab = ref<'edit' | 'chat' | 'document' | 'known'>('chat')
  const selectedNoteId = ref<number | null>(null)
  const isLoading = ref(false)
  const isStreaming = ref(false)

  // ========== Getters ==========
  const selectedNote = computed(() => 
    notes.value.find(n => n.id === selectedNoteId.value) || null
  )
  
  const clueNotes = computed(() => 
    notes.value.filter(n => n.type === 'clue')
  )
  
  const suspectNotes = computed(() => 
    notes.value.filter(n => n.type === 'suspect')
  )

  // ========== Actions ==========
  
  // 加载案件所有数据
  async function loadCaseData(caseId: number) {
    currentCaseId.value = caseId
    isLoading.value = true
    
    try {
      const [notesRes, connRes, timelineRes, docsRes, infosRes, msgRes] = 
        await Promise.all([
          getNotes(caseId),
          getConnections(caseId),
          getTimelineEvents(caseId),
          getDocument(caseId),
          getKnownInfos(caseId),
          getAgentHistory(caseId),
        ])
      
      notes.value = notesRes.data
      connections.value = connRes.data
      timelineEvents.value = timelineRes.data
      documents.value = docsRes.data
      knownInfos.value = infosRes.data
      messages.value = msgRes.data
    } catch (e) {
      console.error('加载案件数据失败:', e)
    } finally {
      isLoading.value = false
    }
  }

  // 便签操作
  async function addNote(caseId: number, data: any) {
    try {
      const res = await createNote(caseId, data)
      notes.value.push(res.data)
      return res.data
    } catch (e) {
      console.error('添加便签失败:', e)
      throw e
    }
  }

  async function updateNoteData(caseId: number, noteId: number, data: any) {
    try {
      await updateNote(caseId, noteId, data)
      const idx = notes.value.findIndex(n => n.id === noteId)
      if (idx !== -1) {
        notes.value[idx] = { ...notes.value[idx], ...data }
      }
    } catch (e) {
      console.error('更新便签失败:', e)
      throw e
    }
  }

  async function removeNote(caseId: number, noteId: number) {
    try {
      await deleteNote(caseId, noteId)
      notes.value = notes.value.filter(n => n.id !== noteId)
      connections.value = connections.value.filter(
        c => c.source !== noteId && c.target !== noteId
      )
      if (selectedNoteId.value === noteId) {
        selectedNoteId.value = null
      }
    } catch (e) {
      console.error('删除便签失败:', e)
      throw e
    }
  }

  // 连线操作
  async function addConnection(caseId: number, data: any) {
    try {
      const res = await createConnection(caseId, data)
      connections.value.push(res.data)
      return res.data
    } catch (e) {
      console.error('添加连线失败:', e)
      throw e
    }
  }

  async function removeConnection(caseId: number, connId: number) {
    try {
      await deleteConnection(caseId, connId)
      connections.value = connections.value.filter(c => c.id !== connId)
    } catch (e) {
      console.error('删除连线失败:', e)
      throw e
    }
  }

  // 时间线操作
  async function addTimelineEvent(caseId: number, data: any) {
    try {
      const res = await createTimelineEvent(caseId, data)
      timelineEvents.value.push(res.data)
      timelineEvents.value.sort((a, b) => 
        new Date(a.event_time).getTime() - new Date(b.event_time).getTime()
      )
      return res.data
    } catch (e) {
      console.error('添加时间线事件失败:', e)
      throw e
    }
  }

  async function updateTimelineEventData(caseId: number, eventId: number, data: any) {
    try {
      await updateTimelineEvent(caseId, eventId, data)
      const idx = timelineEvents.value.findIndex(e => e.id === eventId)
      if (idx !== -1) {
        timelineEvents.value[idx] = { ...timelineEvents.value[idx], ...data }
      }
    } catch (e) {
      console.error('更新时间线事件失败:', e)
      throw e
    }
  }

  async function removeTimelineEvent(caseId: number, eventId: number) {
    try {
      await deleteTimelineEvent(caseId, eventId)
      timelineEvents.value = timelineEvents.value.filter(e => e.id !== eventId)
    } catch (e) {
      console.error('删除时间线事件失败:', e)
      throw e
    }
  }

  async function moveTimelineEventOrder(caseId: number, eventId: number, direction: 'up' | 'down') {
    try {
      await moveTimelineEvent(caseId, eventId, direction)
      // 重新加载时间线
      const res = await getTimelineEvents(caseId)
      timelineEvents.value = res.data
    } catch (e) {
      console.error('移动时间线事件失败:', e)
      throw e
    }
  }

  // 文档操作
  async function addDocument(caseId: number, file: File) {
    try {
      const res = await uploadDocument(caseId, file)
      documents.value.unshift(res.data)
      return res.data
    } catch (e) {
      console.error('上传文档失败:', e)
      throw e
    }
  }

  // 对话操作
  async function sendMessage(caseId: number, message: string) {
    if (!message.trim() || isStreaming.value) return
    
    // 先显示用户消息
    const userMsg = { 
      role: 'user', 
      content: message, 
      id: Date.now(),
      created_at: new Date().toISOString()
    }
    messages.value.push(userMsg)
    isStreaming.value = true
    
    try {
      const response = await fetch(
        `http://127.0.0.1:8001/cases/${caseId}/agent/chat/stream`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message })
        }
      )
      
      if (!response.ok) {
        throw new Error('请求失败')
      }
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let aiContent = ''
      let aiMsgId = Date.now() + 1
      
      // 占位 AI 消息
      messages.value.push({ 
        role: 'assistant', 
        content: '', 
        id: aiMsgId,
        created_at: new Date().toISOString()
      })
      
      if (!reader) {
        throw new Error('无法读取响应')
      }
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const text = line.slice(6).trim()
            if (text === '[DONE]') continue
            if (!text) continue
            
            aiContent += text
            const lastMsg = messages.value[messages.value.length - 1]
            if (lastMsg && lastMsg.role === 'assistant') {
              lastMsg.content = aiContent
            }
          }
        }
      }
    } catch (e) {
      console.error('发送消息失败:', e)
      // 添加错误提示
      messages.value.push({
        role: 'assistant',
        content: '抱歉，连接出错了，请稍后再试~',
        id: Date.now(),
        created_at: new Date().toISOString()
      })
    } finally {
      isStreaming.value = false
    }
  }

  async function clearChatHistory(_caseId: number) {
    try {
      // 调用 API 清空历史
      // await clearAgentHistory(caseId)
      messages.value = []
    } catch (e) {
      console.error('清空历史失败:', e)
      throw e
    }
  }

  // UI 状态操作
  function selectNote(noteId: number | null) {
    selectedNoteId.value = noteId
    if (noteId !== null) {
      activeTab.value = 'edit'
    }
  }

  function setActiveTab(tab: 'edit' | 'chat' | 'document' | 'known') {
    activeTab.value = tab
  }

  function clearSelection() {
    selectedNoteId.value = null
  }

  // 重置状态（切换案件时用）
  function resetState() {
    currentCaseId.value = null
    notes.value = []
    connections.value = []
    timelineEvents.value = []
    documents.value = []
    knownInfos.value = []
    messages.value = []
    activeTab.value = 'chat'
    selectedNoteId.value = null
    isLoading.value = false
    isStreaming.value = false
  }

  return {
    // state
    currentCaseId,
    notes,
    connections,
    timelineEvents,
    documents,
    knownInfos,
    messages,
    activeTab,
    selectedNoteId,
    isLoading,
    isStreaming,
    // getters
    selectedNote,
    clueNotes,
    suspectNotes,
    // actions
    loadCaseData,
    addNote,
    updateNoteData,
    removeNote,
    addConnection,
    removeConnection,
    addTimelineEvent,
    updateTimelineEventData,
    removeTimelineEvent,
    moveTimelineEventOrder,
    addDocument,
    sendMessage,
    clearChatHistory,
    selectNote,
    setActiveTab,
    clearSelection,
    resetState,
  }
})