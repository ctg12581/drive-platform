// src/router/index.js
import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'
import AuthView from '../views/AuthView.vue'
import HomeView from '../views/HomeView.vue'
import SearchView from '../views/SearchView.vue'
import NotificationsView from '../views/NotificationsView.vue'
import ChatView from '../views/ChatView.vue'
import QuizView from '../views/QuizView.vue' // 💡 引入新页面
import AnimeView from '../views/AnimeView.vue' // 💡 动漫人物介绍页

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/auth', name: 'Auth', component: AuthView },
  { path: '/home', name: 'Home', component: HomeView, meta: { requiresAuth: true } },
  { path: '/search', name: 'Search', component: SearchView, meta: { requiresAuth: true } },
  { path: '/notifications', name: 'Notifications', component: NotificationsView, meta: { requiresAuth: true } },
  
  // 💡 新增：5. 默契挑战专用页面
  { path: '/quiz', name: 'Quiz', component: QuizView, meta: { requiresAuth: true } },
  
  { path: '/chat', name: 'Chat', component: ChatView, meta: { requiresAuth: true } },
    { path: '/quiz/design', name: 'QuizDesign', component: () => import('../views/QuizDesignView.vue'), meta: { requiresAuth: true } },
    
  // 💡 新增：6. 动漫人物介绍专用页面
  { path: '/anime', name: 'Anime', component: AnimeView, meta: { requiresAuth: true } },

  // 💡 新增：7. DRIVE 人格评测专用页面（原为孤儿页面，已接入路由）
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