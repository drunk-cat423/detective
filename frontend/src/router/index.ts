import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/views/HomePage.vue'
import CaseDetail from '@/views/CaseDetail.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomePage,
  },
  {
    path: '/case/:id',
    name: 'CaseDetail',
    component: CaseDetail,
    props: true,  // 将路由参数 id 作为 props 传入
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router