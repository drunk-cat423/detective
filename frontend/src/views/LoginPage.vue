<template>
  <div class="login-page">
    <div class="login-card">
      <div class="icon-row">
        <span class="logo-icon">🔍</span>
      </div>
      <h1>推理助手</h1>
      <p class="subtitle">Detective Assistant</p>
      <div v-if="loading" class="loading">检查登录状态...</div>
      <div v-else-if="!authEnabled" class="no-auth">
        <p>认证未开启，即将跳转...</p>
      </div>
      <form v-else @submit.prevent="handleLogin">
        <div class="error" v-if="errorMsg">{{ errorMsg }}</div>
        <input
          v-model="password"
          type="password"
          placeholder="请输入登录密码"
          autofocus
        />
        <button type="submit" :disabled="!password.trim() || submitting">
          {{ submitting ? '登录中...' : '登录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const password = ref('')
const errorMsg = ref('')
const loading = ref(true)
const submitting = ref(false)
const authEnabled = ref(false)

async function checkAuthStatus() {
  try {
    const res = await fetch('/api/auth/status')
    const data = await res.json()
    authEnabled.value = data.enabled
  } catch {
    authEnabled.value = false
  } finally {
    loading.value = false
  }
}

async function handleLogin() {
  if (!password.value.trim()) return
  submitting.value = true
  errorMsg.value = ''

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: password.value }),
    })

    if (!res.ok) {
      const err = await res.json()
      errorMsg.value = err.detail || '登录失败'
      return
    }

    const data = await res.json()
    localStorage.setItem('auth_token', data.token)
    router.push('/')
  } catch {
    errorMsg.value = '网络错误，请稍后重试'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await checkAuthStatus()
  if (!authEnabled.value) {
    setTimeout(() => router.push('/'), 1000)
  }
})
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 44px);
  background: linear-gradient(135deg, #FFF8E8 0%, #FFF5D6 50%, #FFFBF0 100%);
}

.login-card {
  background: #FFFFFF;
  padding: 48px 40px 40px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(184, 146, 46, 0.08);
  border: 1px solid #E8D9B0;
  width: 360px;
  max-width: 90vw;
  text-align: center;
  transition: box-shadow 0.3s;
}

.login-card:hover {
  box-shadow: 0 8px 24px rgba(184, 146, 46, 0.16);
}

.icon-row {
  margin-bottom: 16px;
}

.logo-icon {
  font-size: 48px;
  line-height: 1;
}

h1 {
  margin: 0 0 4px;
  font-size: 28px;
  color: #2D2D2D;
  font-weight: 600;
}

.subtitle {
  margin: 0 0 28px;
  color: #6B6B6B;
  font-size: 14px;
  letter-spacing: 0.5px;
}

input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #E8D9B0;
  border-radius: 8px;
  font-size: 16px;
  outline: none;
  box-sizing: border-box;
  transition: all 0.2s;
  background: #FFFBF0;
  color: #2D2D2D;
}

input::placeholder {
  color: #B8A88A;
}

input:focus {
  border-color: #D4A843;
  background: #FFFFFF;
  box-shadow: 0 0 0 3px rgba(212, 168, 67, 0.12);
}

button {
  width: 100%;
  margin-top: 16px;
  padding: 12px 24px;
  background: #D4A843;
  color: #FFFFFF;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}

button:hover:not(:disabled) {
  background: #B8922E;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(184, 146, 46, 0.3);
}

button:active:not(:disabled) {
  transform: translateY(0);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error {
  background: #FFF5F5;
  color: #C53030;
  border: 1px solid #FED7D7;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.loading,
.no-auth {
  color: #6B6B6B;
  padding: 20px 0;
  font-size: 14px;
}
</style>
