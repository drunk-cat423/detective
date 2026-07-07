import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/views/HomePage.vue'
import CaseDetail from '@/views/CaseDetail.vue'
import LoginPage from '@/views/LoginPage.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
  },
  {
    path: '/',
    name: 'Home',
    component: HomePage,
    meta: { requiresAuth: true },
  },
  {
    path: '/case/:id',
    name: 'CaseDetail',
    component: CaseDetail,
    props: true,
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：检查登录状态
router.beforeEach(async (to, _from, next) => {
  if (to.name === 'Login') {
    return next()
  }

  // 先检查 auth 是否开启（通过 localStorage 缓存结果）
  let authEnabled = localStorage.getItem('auth_enabled')
  if (authEnabled === null) {
    try {
      const res = await fetch('/api/auth/status')
      const data = await res.json()
      authEnabled = String(data.enabled)
      localStorage.setItem('auth_enabled', authEnabled)
    } catch {
      authEnabled = 'false'
      localStorage.setItem('auth_enabled', 'false')
    }
  }

  if (authEnabled === 'true') {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      return next({ name: 'Login' })
    }
  }

  next()
})

export default router
