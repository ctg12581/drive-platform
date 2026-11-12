// src/router/index.js
import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import QuestionsView from '../views/QuestionsView.vue'
import UsersView from '../views/UsersView.vue'

const routes = [
  { path: '/login', name: 'Login', component: LoginView, meta: { public: true } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: DashboardView, meta: { requiresAuth: true } },
  { path: '/questions', name: 'Questions', component: QuestionsView, meta: { requiresAuth: true } },
  { path: '/users', name: 'Users', component: UsersView, meta: { requiresAuth: true } },
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
