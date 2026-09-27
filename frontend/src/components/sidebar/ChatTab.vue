<template>
  <div class="panel-content chat-panel">
    <div ref="chatMessagesRef" class="chat-messages" role="log" aria-label="推理记录">
      <div v-if="chatHistory.length === 0" class="chat-empty">
        <p>来和小识聊聊吧。</p>
      </div>
      <div v-for="(msg, idx) in chatHistory" :key="idx" :class="['chat-msg', msg.role]">
        <div class="msg-heading">
          <img :src="msg.role === 'user' ? userAvatar : agentAvatar" class="avatar" :alt="msg.role === 'user' ? '我' : '小识'" />
          <span>{{ msg.role === 'user' ? '我的提问' : '小识的推理' }}</span>
          <small>{{ String(idx + 1).padStart(2, '0') }}</small>
        </div>
        <div v-if="msg.role === 'user'" class="msg-content">{{ msg.content }}</div>
        <div v-else class="msg-content">
          <div v-if="msg.content" v-html="renderMarkdown(msg.content)"></div>
          <span v-else-if="isThinking" class="thinking-text">正在整理线索<span class="thinking-dots">…</span></span>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <div class="composer-meta">
        <span class="composer-recipient">TO / 小识</span>
        <div class="composer-actions" aria-label="会话操作">
          <button type="button" @click="clearScreen" :disabled="chatHistory.length === 0" title="清空当前页面的记录">清空页面</button>
          <button type="button" @click="resetMemory" :disabled="chatHistory.length === 0" title="重置小识对本案的记忆">重置记忆</button>
        </div>
      </div>
      <div class="composer-row">
        <input
          type="text"
          :value="chatInput"
          placeholder="向小识提问，或记下一条疑点…"
          aria-label="输入推理问题"
          autocomplete="off"
          @keydown.enter="handleComposerKeydown"
          @input="handleComposerInput"
          :disabled="chatLoading"
        />
        <button class="send-btn" type="button" aria-label="发送消息" title="发送消息" @click="sendMessage" :disabled="chatLoading || !chatInput.trim()">
          <!-- Lucide send icon (ISC); see /third-party-notices.txt. -->
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z" />
            <path d="m21.854 2.147-10.94 10.939" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed, onMounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps<{
  chatHistory: { role: string; content: string }[]
  chatInput: string
  chatLoading: boolean
  isThinking: boolean
  userAvatar: string
  agentAvatar: string
}>()

const emit = defineEmits<{
  'update:chatInput': [value: string]
  'send': []
  'clear': []
  'reset': []
  'enter-key': [event: KeyboardEvent]
  'mounted': []
}>()

const chatMessagesRef = ref<HTMLElement | null>(null)
const chatInput = computed(() => props.chatInput)

function renderMarkdown(value: string) {
  return DOMPurify.sanitize(marked(value) as string)
}
function sendMessage() { emit('send') }
function clearScreen() { emit('clear') }
function resetMemory() { emit('reset') }
function handleComposerKeydown(event: KeyboardEvent) {
  if (event.isComposing) return
  event.preventDefault()
  emit('enter-key', event)
}
function handleComposerInput(event: Event) {
  emit('update:chatInput', (event.target as HTMLInputElement).value)
}
function scrollToBottom() {
  if (props.chatHistory.length === 0) {
    nextTick(() => {
      if (chatMessagesRef.value) chatMessagesRef.value.scrollTop = 0
    })
    return
  }
  nextTick(() => {
    if (chatMessagesRef.value) chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  })
}
watch(() => props.chatHistory.length, scrollToBottom)
watch(() => props.chatHistory, scrollToBottom, { deep: true })
watch(() => props.isThinking, (thinking) => {
  if (!thinking) scrollToBottom()
})
onMounted(() => {
  scrollToBottom()
  emit('mounted')
})
</script>

<style scoped>
.chat-panel { display: flex; flex-direction: column; height: 100%; min-height: 0; padding: 0; color: #40392f; }
.chat-messages { flex: 1; min-height: 0; overflow-y: auto; padding: 18px 22px 22px 3px; scrollbar-width: none; }
.chat-messages::-webkit-scrollbar { display: none; }
.chat-empty { display: grid; place-items: center; min-height: 100%; padding: 0 4px; text-align: center; }
.chat-empty p { margin: 0; color: #897a69; font: 19px/1.5 var(--serif); letter-spacing: .08em; }
.msg-heading small { color: #8c8070; font: 10px/1.4 'Courier New', monospace; letter-spacing: .12em; }
.chat-msg { margin: 0 1px 26px 0; animation: note-arrive 240ms ease-out both; }
.msg-heading { display: flex; align-items: center; gap: 9px; margin-bottom: 8px; color: #796d5c; font: 11px/1.2 var(--serif); letter-spacing: .12em; }
.chat-msg.user .msg-heading { color: #925248; }
.msg-heading small { margin-left: auto; }
.avatar { width: 24px; height: 24px; object-fit: cover; border: 1px solid rgba(79, 62, 44, .34); padding: 2px; background: #eee6d6; }
.msg-content { margin-left: 33px; padding: 0 4px 0 11px; border-left: 1px solid rgba(96, 79, 54, .25); font-size: 13px; line-height: 1.85; word-break: break-word; }
.chat-msg.user .msg-content { border-left: 2px solid #9d5a50; color: #3e372e; }
.msg-content :deep(p) { margin: 0 0 8px; }
.msg-content :deep(p:last-child) { margin-bottom: 0; }
.msg-content :deep(strong) { color: #8e453d; }
.msg-content :deep(ul), .msg-content :deep(ol) { padding-left: 19px; margin: 5px 0 9px; }
.msg-content :deep(code) { background: rgba(119, 93, 60, .1); padding: 1px 3px; font-size: .92em; }
.msg-content :deep(pre) { overflow-x: auto; padding: 10px; background: #e9dfca; border: 1px solid rgba(92, 70, 46, .2); font-size: 12px; }
.thinking-text { color: #8f7666; font-family: var(--serif); }
.thinking-dots { animation: blink 1.4s ease-in-out infinite; }
.chat-input { flex: none; position: relative; padding: 9px 18px 6px 3px; border-top: 1px solid rgba(83, 66, 43, .22); background: transparent; }
.composer-meta { display: flex; align-items: center; justify-content: space-between; gap: 10px; min-height: 18px; margin-bottom: 5px; }
.composer-recipient { flex: none; color: #806858; font: 11px/1.3 'Courier New', monospace; letter-spacing: .08em; }
.composer-row { display: grid; grid-template-columns: minmax(0, 1fr) 34px; align-items: end; column-gap: 12px; height: 36px; }
.composer-row input { display: block; width: 100%; min-width: 0; height: 36px; box-sizing: border-box; padding: 8px 2px 0; border: 0; border-bottom: 1px solid rgba(96, 80, 58, .44); border-radius: 0; background: transparent; color: #40392f; font: 14px/26px var(--serif); box-shadow: none; }
.composer-row input::placeholder { color: #918573; }
.composer-row input:focus { outline: none; }
.send-btn { position: relative; top: 3px; display: flex; align-items: flex-end; justify-content: center; width: 34px; height: 34px; padding: 0; border: 0; background: transparent; color: #98534a; cursor: pointer; transition: color 150ms ease; }
.send-btn svg { display: block; width: 24px; height: 24px; transform: translateY(2px); transition: transform 160ms ease; }
.send-btn:hover:not(:disabled) { color: #763e37; }
.send-btn:hover:not(:disabled) svg { transform: translate(2px, 2px); }
.send-btn:focus-visible { outline: 2px solid #99564b; outline-offset: 1px; }
.send-btn:disabled { color: #b7a89a; cursor: not-allowed; }
.composer-actions { display: flex; justify-content: flex-end; gap: 13px; }
.composer-actions button { padding: 2px 0; border: 0; border-bottom: 1px solid transparent; background: transparent; color: #817160; font: 12px var(--serif); cursor: pointer; white-space: nowrap; }
.composer-actions button:hover:not(:disabled), .composer-actions button:focus-visible { color: #8e493f; border-bottom-color: currentColor; }
.composer-actions button:disabled { color: #8e806f; cursor: not-allowed; }
@keyframes note-arrive { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
@keyframes blink { 50% { opacity: .35; } }
@media (max-width: 480px) {
  .chat-messages { padding-right: 11px; }
  .chat-input { padding-right: 8px; }
  .composer-actions { gap: 7px; }
  .composer-actions button { font-size: 10px; }
}
@media (prefers-reduced-motion: reduce) {
  .chat-msg { animation: none; }
  .send-btn { transition: none; }
  .send-btn svg { transition: none; }
}
</style>
