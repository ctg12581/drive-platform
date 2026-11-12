<!-- src/views/LoginView.vue -->
<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">𝕏 Admin</div>
      <p class="login-sub">DRIVE 平台管理后台</p>

      <form @submit.prevent="handleLogin" class="login-form">
        <label class="field">
          <span class="field-label">管理员账号</span>
          <input v-model.trim="username" type="text" autocomplete="username" placeholder="请输入管理员账号" />
        </label>
        <label class="field">
          <span class="field-label">密码</span>
          <input v-model="password" type="password" autocomplete="current-password" placeholder="请输入密码" />
        </label>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>

      <p class="login-tip">仅限 username 为 <code>admin</code> 的系统管理员登录</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:3000'
const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

const handleLogin = async () => {
  errorMsg.value = ''
  if (!username.value || !password.value) {
    errorMsg.value = '请输入账号和密码'
    return
  }
  if (username.value !== 'admin') {
    errorMsg.value = '您不是系统管理员，无权登录后台'
    return
  }

  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      errorMsg.value = data.detail || '登录失败，请检查账号密码'
      return
    }
    if (!authStore.setLogin(data.access_token, username.value)) {
      errorMsg.value = '非管理员账号，禁止登录'
      return
    }
    router.push('/dashboard')
  } catch (err) {
    errorMsg.value = '无法连接后端服务，请确认后端已启动'
    console.error('管理员登录异常:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f1419;
  padding: 20px;
  box-sizing: border-box;
}
.login-card {
  width: 100%;
  max-width: 360px;
  background: #16181c;
  border: 1px solid #2f3336;
  border-radius: 16px;
  padding: 32px 28px;
  box-sizing: border-box;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}
.login-logo {
  font-size: 1.75rem;
  font-weight: 900;
  color: #ffffff;
  text-align: center;
}
.login-sub {
  text-align: center;
  color: #8899a6;
  font-size: 0.85rem;
  margin: 6px 0 28px 0;
}
.login-form { display: flex; flex-direction: column; gap: 16px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 0.85rem; color: #c7d0d9; font-weight: 600; }
.field input {
  height: 42px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid #2f3336;
  background: #0f1419;
  color: #ffffff;
  font-size: 0.95rem;
  outline: none;
  box-sizing: border-box;
}
.field input:focus { border-color: #1d9bf0; }
.error-msg { color: #ef4444; font-size: 0.82rem; margin: 0; }
.login-btn {
  height: 44px;
  border: none;
  border-radius: 9999px;
  background: #1d9bf0;
  color: #fff;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 4px;
}
.login-btn:hover { background: #1a8cd8; }
.login-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.login-tip {
  text-align: center;
  color: #536471;
  font-size: 0.75rem;
  margin: 20px 0 0 0;
}
.login-tip code { color: #1d9bf0; }
</style>
