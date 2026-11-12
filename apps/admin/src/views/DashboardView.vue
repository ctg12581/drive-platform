<!-- src/views/DashboardView.vue -->
<template>
  <div class="dashboard-container">
    <div class="page-title-bar">
      <h2>📊 系统数据大盘看板</h2>
      <p>实时监控全网 𝕏 DRIVE 平台的运行状况与活跃增长</p>
    </div>

    <div v-if="loading" class="loading-hint">正在统计大盘数据...</div>

    <!-- 四大指标卡片网格 -->
    <div v-else class="stats-grid">
      <div class="stat-card blue">
        <div class="stat-icon">👤</div>
        <div class="stat-meta">
          <span class="stat-num">{{ stats.total_users }}</span>
          <span class="stat-label">全网注册用户</span>
        </div>
      </div>
      <div class="stat-card pink">
        <div class="stat-icon">💘</div>
        <div class="stat-meta">
          <span class="stat-num">{{ stats.total_attempts }}</span>
          <span class="stat-label">累计默契挑战</span>
        </div>
      </div>
      <div class="stat-card green">
        <div class="stat-icon">✨</div>
        <div class="stat-meta">
          <span class="stat-num">{{ stats.total_moments }}</span>
          <span class="stat-label">用户发布动态</span>
        </div>
      </div>
      <div class="stat-card purple">
        <div class="stat-icon">📚</div>
        <div class="stat-meta">
          <span class="stat-num">{{ stats.total_questions }}</span>
          <span class="stat-label">系统公共题目</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetch } from '../utils/api'

const loading = ref(true)
const stats = ref(null)

onMounted(() => {
  fetchDashboardStats()
})

const fetchDashboardStats = async () => {
  try {
    const res = await apiFetch('/admin/dashboard/stats')
    const data = await res.json()
    if (res.ok) {
      stats.value = data.stats
    }
  } catch {
    console.error('获取大盘数据失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dashboard-container { padding: 30px; text-align: left; }
.page-title-bar h2 { margin: 0 0 6px 0; font-size: 1.5rem; font-weight: 800; }
.page-title-bar p { margin: 0 0 30px 0; color: #6b7280; font-size: 0.95rem; }

.stats-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 24px;
}
.stat-card {
  background: white; border-radius: 16px; padding: 24px; display: flex; align-items: center; gap: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.02); border: 1px solid #f3f4f6;
}
.stat-icon { font-size: 2.5rem; }
.stat-meta { display: flex; flex-direction: column; }
.stat-num { font-size: 2rem; font-weight: 900; color: #111827; }
.stat-label { font-size: 0.85rem; color: #6b7280; font-weight: bold; margin-top: 4px; }
</style>