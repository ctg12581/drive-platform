<template>
  <div class="feed-container">
    <!-- 发推风格的评测卡片 -->
    <div class="compose-card">
      <h2 class="section-title">DRIVE Space 新建评测</h2>
      <form @submit.prevent="submitEvaluate">
        <div class="select-group" v-for="(label, key) in dimensions" :key="key">
          <div class="select-label">{{ label }}</div>
          <select v-model="form[key]" class="x-select">
            <option value="S">S 级 (战略/反脆弱/灯塔)</option>
            <option value="A">A 级 (独立/高效/敏捷)</option>
            <option value="B">B 级 (合格/常规/合规)</option>
            <option value="C">C 级 (被动/依赖/僵化)</option>
            <option value="D">D 级 (回避/脆弱/流失)</option>
          </select>
        </div>
        <div class="action-row">
          <button type="submit" class="x-btn-primary">开始诊断</button>
        </div>
      </form>
    </div>

    <!-- 诊断结果展示 (完美融入主内容流) -->
    <div v-show="result" class="result-feed">
      <div class="tweet-card">
        <div class="tweet-header">
          <div class="tweet-avatar">🧠</div>
          <div class="tweet-meta">
            <span class="tweet-author">系统诊断姬</span>
            <span class="tweet-handle">@drive_bot · 刚刚</span>
          </div>
        </div>
        <div class="tweet-content">
          <p>以下是根据您选择的评级，为您动态构建的 𝕏 雷达图。综合诊断如下：</p>
          <p class="synthesis-text">💡 <strong>成长建议：</strong>{{ result ? result.synthesis : '' }}</p>
          
          <!-- 雷达图容器 -->
          <div class="chart-wrapper">
            <canvas id="radarChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick } from 'vue'
import { useAuthStore } from '../store/auth'
import Chart from 'chart.js/auto'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:3000'
const authStore = useAuthStore()
const form = reactive({ d: 'B', r: 'B', i: 'B', v: 'B', e: 'B' })
const result = ref(null)
let chartInstance = null

const dimensions = {
  d: 'Decision (决策力)',
  r: 'Resilience (意志力/韧性)',
  i: 'Intelligence (智力)',
  v: 'Values (价值观)',
  e: 'Elasticity (灵活性)'
}

const submitEvaluate = async () => {
  try {
    const res = await fetch(`${API_BASE}/drive/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify(form)
    })
    const data = await res.json()
    if (res.ok) {
      result.value = data
      nextTick(() => { renderChart(data.scores) })
    } else {
      alert(data.detail || '评测失败')
    }
  } catch {
    alert('请求失败，请确保后端数据库运行正常')
  }
}

const renderChart = (scores) => {
  const ctx = document.getElementById('radarChart').getContext('2d')
  if (chartInstance) { chartInstance.destroy() }
  chartInstance = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['决策 (D)', '韧性 (R)', '智力 (I)', '价值观 (V)', '弹性 (E)'],
      datasets: [{
        label: '评价得分',
        data: [scores.d, scores.r, scores.i, scores.v, scores.e],
        backgroundColor: 'rgba(29, 155, 240, 0.1)',
        borderColor: '#1d9bf0',
        borderWidth: 2,
        pointBackgroundColor: '#1d9bf0'
      }]
    },
    options: {
      responsive: true,
      scales: { r: { min: 0, max: 5, ticks: { stepSize: 1, display: false } } }
    }
  })
}
</script>

<style scoped>
.feed-container { width: 100%; }
.section-title { font-size: 1.25rem; font-weight: 800; padding: 12px 16px; margin: 0; border-bottom: 1px solid var(--x-border); }

/* Compose 表单推文卡片 */
.compose-card { padding: 16px; border-bottom: 1px solid var(--x-border); }
.select-group { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.select-label { font-size: 0.95rem; font-weight: 600; color: var(--x-text-main); }
.x-select {
  width: 50%; padding: 8px 12px; border: 1px solid var(--x-border); border-radius: 8px;
  background: #ffffff; color: var(--x-text-main); font-size: 0.9rem; outline: none;
}
.x-select:focus { border-color: var(--x-blue); }

.action-row { display: flex; justify-content: flex-end; margin-top: 16px; }
.x-btn-primary {
  background: var(--x-blue); color: #ffffff; border: none; font-weight: bold;
  padding: 0 16px; height: 36px; border-radius: 9999px; cursor: pointer; transition: background 0.2s;
}
.x-btn-primary:hover { background: #1a8cd8; }

/* Tweet 展现结果卡片 */
.tweet-card { display: flex; padding: 16px; border-bottom: 1px solid var(--x-border); gap: 12px; }
.tweet-avatar {
  width: 40px; height: 40px; border-radius: 50%; background: #f7f9fa;
  display: flex; align-items: center; justify-content: center; font-size: 1.25rem;
}
.tweet-content { flex: 1; }
.tweet-meta { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.tweet-author { font-weight: bold; font-size: 0.95rem; }
.tweet-handle { color: var(--x-text-gray); font-size: 0.85rem; }
.synthesis-text { background: #f7f9fa; padding: 12px; border-radius: 12px; font-size: 0.95rem; line-height: 1.5; }
.chart-wrapper { max-width: 320px; margin: 16px auto 0 auto; }
</style>