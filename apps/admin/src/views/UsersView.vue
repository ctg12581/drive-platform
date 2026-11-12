<!-- src/views/UsersView.vue -->
<template>
  <div class="users-container">
    <div class="page-title-bar" style="text-align: left; margin-bottom: 30px;">
      <h2 style="margin: 0 0 6px 0; font-size: 1.5rem; font-weight: 800;">👤 全网用户活跃监控</h2>
      <p style="margin: 0; color: #6b7280; font-size: 0.95rem;">实时追踪、统计和审计全网所有 DRIVE Space 注册用户的活跃行为状态</p>
    </div>

    <!-- 用户数据大表 -->
    <div class="table-card">
      <table class="admin-table">
        <thead>
          <tr>
            <th>注册头像</th>
            <th>唯一账号 (Username)</th>
            <th>个性昵称 (Nickname)</th>
            <th>发帖数 (Moments)</th>
            <th>评测数 (DRIVE)</th>
            <th>默契测试数 (Quiz)</th>
            <th>加入时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.username">
            <td>
              <div class="avatar-cell">
                <img v-if="isUrl(user.avatar)" :src="user.avatar" class="avatar-img" />
                <span v-else>{{ user.avatar }}</span>
              </div>
            </td>
            <td class="bold-text">@{{ user.username }}</td>
            <td>{{ user.nickname }}</td>
            <td class="count-cell">{{ user.posts_count }} 篇</td>
            <td class="count-cell">{{ user.drive_count }} 次</td>
            <td class="count-cell">{{ user.attempts_count }} 回</td>
            <td class="time-cell">{{ formatLocalTime(user.created_at, 'YYYY-MM-DD') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { isUrl } from '@drive/shared'
import { apiFetch } from '../utils/api'
import { formatLocalTime } from '../utils/date'

const users = ref([])

onMounted(() => {
  fetchUsers()
})

const fetchUsers = async () => {
  try {
    const res = await apiFetch('/admin/users')
    const data = await res.json()
    if (res.ok) {
      users.value = data.users
    }
  } catch {
    console.error('获取用户列表失败')
  }
}
</script>

<style scoped>
.users-container { padding: 30px; }
.table-card { background: white; border-radius: 16px; border: 1px solid #e5e7eb; box-shadow: 0 4px 20px rgba(0,0,0,0.02); overflow: hidden; }

/* 极简后台数据表格 */
.admin-table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }
.admin-table th { background: #f9fafb; padding: 14px 20px; font-weight: bold; color: #4b5563; border-bottom: 1px solid #e5e7eb; }
.admin-table td { padding: 14px 20px; border-bottom: 1px solid #f3f4f6; color: #111827; }
.admin-table tbody tr:hover { background: #f9fafb; }

.avatar-cell { width: 32px; height: 32px; background: #f3f4f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; overflow: hidden; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.bold-text { font-weight: bold; color: #2563eb !important; }
.count-cell { font-weight: bold; }
.time-cell { color: #6b7280; }
</style>