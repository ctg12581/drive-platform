// src/router/index.js
import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

// 全部路由按需懒加载
const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true } },
  { path: '/questions', name: 'Questions', component: () => import('../views/QuestionsView.vue'), meta: { requiresAuth: true } },
  { path: '/users', name: 'Users', component: () => import('../views/UsersView.vue'), meta: { requiresAuth: true } },
  // 兜底：未知路由统一回到后台首页
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 💡 登录守卫：未登录访问后台页面跳转 /login；已登录访问 /login 则回后台首页
router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    return { path: '/login' }
  }
  if (to.path === '/login' && authStore.isLoggedIn) {
    return { path: '/dashboard' }
  }
  return true
})

export default router
