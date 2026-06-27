<template>
  <div class="panel-content chat-panel">
    <div class="chat-messages" ref="chatMessagesRef">
      <div v-if="chatHistory.length === 0" class="chat-empty">
        💬 和助手小姐聊聊吧
      </div>
      <div
        v-for="(msg, idx) in chatHistory"
        :key="idx"
        :class="['chat-msg', msg.role]"
      >
        <img :src="msg.role === 'user' ? userAvatar : agentAvatar" :class="['avatar', msg.role]" />

        <div v-if="msg.role === 'user'" class="msg-bubble">{{ msg.content }}</div>

        <div v-else class="msg-bubble">
          <template v-if="msg.content">
            <div v-html="renderMarkdown(msg.content)"></div>
          </template>
          <template v-else-if="isThinking">
            <span class="thinking-text">
              小识正在努力思考
              <span class="thinking-dots">...</span>
            </span>
          </template>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <input
        :value="chatInput"
        placeholder="输入消息..."
        @keydown.enter="handleEnterKey"
        @input="emit('update:chatInput', ($event.target as HTMLInputElement).value)"
        :disabled="chatLoading"
      />
      <button @click="sendMessage" :disabled="chatLoading || !chatInput.trim()">发送</button>
      <button @click="clearScreen" :disabled="chatHistory.length === 0">清屏</button>
      <button @click="resetMemory" :disabled="chatHistory.length === 0" class="reset-btn">重置</button>
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

const chatInput = computed({
  get: () => props.chatInput,
  set: (v) => emit('update:chatInput', v)
})

function renderMarkdown(text: string) {
  if (!text) return ''
  const rawHtml = marked(text) as string
  return DOMPurify.sanitize(rawHtml)
}

function sendMessage() { emit('send') }
function clearScreen() { emit('clear') }
function resetMemory() { emit('reset') }
function handleEnterKey(event: KeyboardEvent) { emit('enter-key', event) }

function scrollToBottom() {
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })
}

watch(() => props.chatHistory.length, () => {
  scrollToBottom()
})

watch(() => props.isThinking, (thinking) => {
  if (!thinking) {
    scrollToBottom()
  }
})

onMounted(() => {
  scrollToBottom()
  emit('mounted')
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background:
    radial-gradient(circle at 0% 100%, rgba(212, 168, 67, 0.04) 0%, transparent 40%),
    radial-gradient(circle at 100% 0%, rgba(58, 123, 200, 0.04) 0%, transparent 40%),
    var(--cream);
}

.chat-empty {
  color: var(--gold-deep);
  text-align: center;
  margin-top: 80px;
  font-size: 15px;
  opacity: 0.7;
}

.chat-msg {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
  animation: fadeInUp 0.4s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-msg.user {
  align-items: flex-end;
}
.chat-msg.assistant {
  align-items: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 6px;
  border: 3px solid var(--white);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  background: #e0e0e0;
  display: block;
}

.avatar[src=""], .avatar:not([src]) {
  background: #e0e0e0;
}

.chat-msg.user .avatar {
  background: linear-gradient(135deg, var(--traveler-blue), #5B9BD5);
}

.chat-msg.assistant .avatar {
  background: linear-gradient(135deg, var(--gold), var(--gold-deep));
}

.msg-bubble {
  max-width: 85%;
  min-width: 60px;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  position: relative;
}

.chat-msg.user .msg-bubble {
  background: linear-gradient(135deg, var(--traveler-blue), #4A8FD0);
  color: var(--white);
  border: none;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 16px rgba(58, 123, 200, 0.2);
}

.chat-msg.assistant .msg-bubble {
  background: var(--white);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}

.msg-bubble :deep(p) {
  margin: 0 0 6px;
}

.msg-bubble :deep(p):last-child {
  margin-bottom: 0;
}

.msg-bubble :deep(strong) {
  color: var(--gold-deep);
  font-weight: 700;
}

.msg-bubble :deep(ul), .msg-bubble :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}

.msg-bubble :deep(code) {
  background: var(--gold-pale);
  color: var(--gold-deep);
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.msg-bubble :deep(pre) {
  background: #2D2D2D;
  color: #F0E6C8;
  padding: 12px;
  border-radius: 12px;
  overflow-x: auto;
  font-size: 12px;
  margin: 8px 0;
}

.chat-input {
  border-top: 2px solid var(--border);
  padding: 12px 16px;
  display: flex;
  gap: 8px;
  background: var(--white);
  position: relative;
  padding-right: 22px;
}

.chat-input::before {
  content: '';
  position: absolute;
  top: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--gold), var(--traveler-blue));
}

.chat-input input {
  flex: 1;
  padding: 10px 18px;
  border: 2px solid #efd587;
  border-radius: 24px;
  font-size: 14px;
  background: var(--cream);
  transition: all 0.3s;
  font-family: inherit;
}

.chat-input input:focus {
  outline: none;
  background: var(--white);
  box-shadow: 0 0 0 4px rgba(212, 168, 67, 0.35);
}

.chat-input input::placeholder {
  color: var(--text-secondary);
  opacity: 0.6;
}

.chat-input button {
  padding: 8px 14px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s;
  outline: none;
}

.chat-input button:first-of-type {
  background: linear-gradient(135deg, var(--gold), var(--gold-deep));
  color: var(--white);
  box-shadow: 0 2px 8px rgba(212, 168, 67, 0.25);
  border: 2px solid #efd587;
}

.chat-input button:first-of-type:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(212, 168, 67, 0.35);
}

.chat-input button:first-of-type:disabled {
  opacity: 0.5;
  transform: none;
  cursor: not-allowed;
}

.chat-input button:not(:first-of-type) {
  background: var(--white);
  color: var(--text-secondary);
  border: 2px solid #efd587;
  outline: none;
}

.chat-input button:not(:first-of-type):hover {
  color: var(--gold-deep);
  transform: translateY(-2px);
}

.chat-input button.reset-btn {
  background: var(--white);
  color: #c62828;
  border: 2px solid #e75765;
}

.chat-input button.reset-btn:hover {
  background: #ffebee;
  border-color: #c62828;
  color: #c62828 !important;
  transform: translateY(-2px);
}

.thinking-text {
  color: var(--gold-deep);
  font-style: italic;
  font-size: 14px;
  animation: blink 1.5s ease-in-out infinite;
  display: flex;
  align-items: center;
  gap: 8px;
}

.thinking-text::before {
  content: '✦';
  font-size: 16px;
  animation: spin 2s linear infinite;
}

.thinking-dots {
  display: inline-block;
  animation: blink 1.5s ease-in-out infinite;
  animation-delay: 0.3s;
}

@keyframes blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
