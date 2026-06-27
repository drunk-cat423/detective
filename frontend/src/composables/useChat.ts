import { ref, nextTick, watch, reactive } from 'vue'
import { getAgentHistory, clearAgentHistory } from '@/api/index'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

export function useChat(caseId: number) {
  const chatHistory = ref<{ role: string; content: string }[]>([])
  const chatInput = ref('')
  const chatLoading = ref(false)
  const chatMessages = ref<HTMLElement | null>(null)
  const chatInputRef = ref<HTMLInputElement | null>(null)
  const isThinking = ref(false)

  const userAvatar = ref('/avatar-user.png')
  const agentAvatar = ref('/avatar-agent.png')

  function renderMarkdown(text: string) {
    if (!text) return ''
    const rawHtml = marked(text) as string
    return DOMPurify.sanitize(rawHtml)
  }

  async function loadChatHistory() {
    try {
      const res = await getAgentHistory(caseId)
      chatHistory.value = res.data.map((m: any) => ({
        role: m.role,
        content: m.content,
      }))
    } catch (err) {
      console.error('加载对话历史失败', err)
    }
  }

  function scrollToBottom() {
    if (chatMessages.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight
    }
  }

  async function sendMessage() {
    const msg = chatInput.value.trim()
    if (!msg || chatLoading.value) return

    chatInput.value = ''
    chatHistory.value.push({ role: 'user', content: msg })
    chatLoading.value = true
    isThinking.value = true

    const assistantMsg = reactive({ role: 'assistant', content: '' })
    chatHistory.value.push(assistantMsg)

    await nextTick()
    scrollToBottom()

    try {
      const response = await fetch(`http://127.0.0.1:8001/cases/${caseId}/agent/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      })

      if (!response.ok) throw new Error('Request failed')
      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue

            if (isThinking.value) {
              isThinking.value = false
            }
            assistantMsg.content += data
            await nextTick()
            scrollToBottom()
          }
        }
      }
    } catch (err) {
      console.error('流式对话失败', err)
      isThinking.value = false
      if (!assistantMsg.content) assistantMsg.content = '抱歉，请求失败，请稍后重试。'
    } finally {
      chatLoading.value = false
      isThinking.value = false
      await loadChatHistory()
      nextTick(() => {
        chatInputRef.value?.focus()
      })
    }
  }

  function handleEnterKey(event: KeyboardEvent) {
    if (event.isComposing) return
    sendMessage()
  }

  function clearScreen() {
    chatHistory.value = []
  }

  async function resetMemory() {
    if (!confirm('确定要重置吗?这将消除助手小姐关于本案的所有记忆,重新开始.')) return
    try {
      await clearAgentHistory(caseId)
      chatHistory.value = []
    } catch (err) {
      console.error('重置记忆失败', err)
    }
  }

  watch(chatHistory, () => {
    nextTick(() => {
      if (chatMessages.value) {
        chatMessages.value.scrollTop = chatMessages.value.scrollHeight
      }
    })
  }, { deep: true })

  return {
    chatHistory,
    chatInput,
    chatLoading,
    chatMessages,
    chatInputRef,
    isThinking,
    userAvatar,
    agentAvatar,
    renderMarkdown,
    loadChatHistory,
    sendMessage,
    handleEnterKey,
    clearScreen,
    resetMemory,
    scrollToBottom,
  }
}
