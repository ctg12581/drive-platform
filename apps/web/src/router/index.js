// src/router/index.js
import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

// 全部路由按需懒加载，减小首屏主包体积
const routes = [
  { path: '/', redirect: '/home' },
  { path: '/auth', name: 'Auth', component: () => import('../views/AuthView.vue') },
  { path: '/home', name: 'Home', component: () => import('../views/HomeView.vue'), meta: { requiresAuth: true } },
  { path: '/search', name: 'Search', component: () => import('../views/SearchView.vue'), meta: { requiresAuth: true } },
  { path: '/notifications', name: 'Notifications', component: () => import('../views/NotificationsView.vue'), meta: { requiresAuth: true } },
  { path: '/quiz', name: 'Quiz', component: () => import('../views/QuizView.vue'), meta: { requiresAuth: true } },
  { path: '/chat', name: 'Chat', component: () => import('../views/ChatView.vue'), meta: { requiresAuth: true } },
  { path: '/quiz/design', name: 'QuizDesign', component: () => import('../views/QuizDesignView.vue'), meta: { requiresAuth: true } },
  { path: '/anime', name: 'Anime', component: () => import('../views/AnimeView.vue'), meta: { requiresAuth: true } },
  { path: '/drive', name: 'Drive', component: () => import('../views/DriveView.vue'), meta: { requiresAuth: true } },

  // 兜底：未知路由统一回到主页，避免白屏
  { path: '/:pathMatch(.*)*', redirect: '/home' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/auth')
  } else {
    next()
  }
})

export default router
