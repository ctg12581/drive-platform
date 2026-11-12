// src/utils/api.js
import { useAuthStore } from '../store/auth'
import router from '../router'

// 这里的端口请根据您实际运行的 FastAPI 后端服务端口进行配置 (本地通常为 3000)
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:3000'

/**
 * 后台专属 API 请求工具，自动拦截 401 报错并重定向到管理员登录 /login 页面
 */
export async function apiFetch(endpoint, options = {}) {
  const authStore = useAuthStore()

  const headers = { ...options.headers }
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  if (authStore.token) {
    headers['Authorization'] = `Bearer ${authStore.token}`
  }

  const mergedOptions = {
    ...options,
    headers,
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, mergedOptions)

    // 💡 拦截器：一旦管理员登录到期，自动抹除凭证，并强制重定向到 /login 登录页
    if (response.status === 401) {
      authStore.logout()
      router.push('/login')
      throw new Error('管理员登录凭证已失效，请重新登录')
    }

    return response
  } catch (err) {
    console.error('API 请求异常:', err)
    throw err
  }
}