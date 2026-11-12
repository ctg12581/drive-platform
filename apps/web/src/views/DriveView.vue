<template>
  <div class="drive-container">
    <!-- 评测表单 -->
    <div class="compose-card">
      <h2 class="section-title">🧠 DRIVE 人格评测</h2>
      <p class="section-sub">选择每个维度最贴近你的等级，生成专属雷达图</p>
      <form @submit.prevent="submitEvaluate">
        <div class="select-group" v-for="(label, key) in dimensions" :key="key">
          <div class="select-label">{{ label }}</div>
          <select v-model="form[key]" class="x-select">
            <option value="S">S 级 · 战略 / 反脆弱</option>
            <option value="A">A 级 · 独立 / 高效</option>
            <option value="B">B 级 · 合格 / 常规</option>
            <option value="C">C 级 · 被动 / 依赖</option>
            <option value="D">D 级 · 回避 / 脆弱</option>
          </select>
        </div>
        <div class="action-row">
          <button type="submit" class="xhs-btn-primary">开始诊断</button>
        </div>
      </form>
    </div>

    <!-- 诊断结果 -->
    <div v-show="result" class="result-feed">
      <div class="result-card">
        <div class="result-head">
          <div class="result-avatar">🧠</div>
          <div class="result-meta">
            <span class="result-author">系统诊断姬</span>
            <span class="result-handle">@drive_bot · 刚刚</span>
          </div>
        </div>
        <div class="result-content">
          <p>根据你的评级，为你生成了专属 𝕏 雷达图，综合诊断如下：</p>
          <p class="synthesis-text">💡 <strong>成长建议：</strong>{{ result ? result.synthesis : '' }}</p>
          <div class="chart-wrapper">
            <canvas id="radarChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onUnmounted } from 'vue'
import { apiFetch } from '../utils/api'
import Chart from 'chart.js/auto'

const form = reactive({ d: 'B', r: 'B', i: 'B', v: 'B', e: 'B' })
const result = ref(null)
let chartInstance = null

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})

const dimensions = {
  d: 'Decision (决策力)',
  r: 'Resilience (意志力/韧性)',
  i: 'Intelligence (智力)',
  v: 'Values (价值观)',
  e: 'Elasticity (灵活性)'
}

const submitEvaluate = async () => {
  try {
    const res = await apiFetch('/drive/evaluate', {
      method: 'POST',
      body: JSON.stringify(form),
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
        backgroundColor: 'rgba(255, 36, 66, 0.12)',
        borderColor: '#ff2442',
        borderWidth: 2,
        pointBackgroundColor: '#ff2442'
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
.drive-container { width: 100%; background: #fff; min-height: calc(100vh - var(--app-top) - var(--app-bottom)); }

.compose-card { padding: 18px 16px 20px; border-bottom: 1px solid var(--xhs-line); }
.section-title { font-size: 1.2rem; font-weight: 900; margin: 0 0 4px; }
.section-sub { font-size: 0.8rem; color: var(--xhs-text-3); margin: 0 0 18px; }

.select-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  background: #fafafa;
  border-radius: 14px;
  padding: 10px 14px;
}
.select-label { font-size: 0.88rem; font-weight: 600; color: var(--xhs-text); }
.x-select {
  width: 48%;
  padding: 9px 12px;
  border: 1.5px solid transparent;
  border-radius: 10px;
  background: #fff;
  color: var(--xhs-text);
  font-size: 0.82rem;
  outline: none;
}
.x-select:focus { border-color: var(--xhs-red); }

.action-row { display: flex; justify-content: center; margin-top: 20px; }
.action-row .xhs-btn-primary { width: 100%; height: 46px; font-size: 1rem; }

/* 结果卡片 */
.result-feed { padding: 16px; }
.result-card {
  background: #fff;
  border: 1px solid var(--xhs-line);
  border-radius: 18px;
  padding: 16px;
  box-shadow: var(--xhs-shadow);
}
.result-head { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.result-avatar {
  width: 42px; height: 42px; border-radius: 50%;
  background: var(--xhs-red-soft);
  display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
}
.result-meta { display: flex; flex-direction: column; }
.result-author { font-weight: 800; font-size: 0.92rem; }
.result-handle { color: var(--xhs-text-3); font-size: 0.76rem; }
.result-content p { font-size: 0.88rem; line-height: 1.6; color: var(--xhs-text-2); }
.synthesis-text {
  background: var(--xhs-red-soft);
  color: var(--xhs-text);
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 0.9rem;
  line-height: 1.6;
}
.chart-wrapper { max-width: 320px; margin: 16px auto 0; }
</style>
