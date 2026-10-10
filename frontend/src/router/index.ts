import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/views/SpatialHome.vue'
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

// 每次打开页面重新读取服务配置，避免旧的本地缓存保留登录要求。
let authStatus: Promise<boolean> | undefined

router.beforeEach(async (to, _from, next) => {
  if (!authStatus) {
    authStatus = (async () => {
      try {
        const res = await fetch('/api/auth/status')
        if (!res.ok) throw new Error('无法读取认证配置')
        const data = await res.json()
        const enabled = data.enabled === true
        localStorage.setItem('auth_enabled', String(enabled))
        return enabled
      } catch {
        return localStorage.getItem('auth_enabled') === 'true'
      }
    })()
  }

  const authEnabled = await authStatus

  if (to.name === 'Login') {
    return authEnabled ? next() : next({ name: 'Home', replace: true })
  }

  if (authEnabled) {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      return next({ name: 'Login' })
    }
  }

  next()
})

export default router
