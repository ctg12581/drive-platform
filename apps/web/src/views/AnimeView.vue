<!-- src/views/AnimeView.vue 动漫人物介绍页 -->
<template>
  <div class="anime-container">
    <!-- 顶端吸顶标题栏 -->
    <div class="anime-header">
      <h2 style="margin: 0; font-size: 1.25rem; font-weight: 800;">🎌 动漫人物图鉴</h2>
    </div>

    <!-- 搜索栏 -->
    <div class="anime-search-box">
      <input
        type="text"
        v-model="searchQuery"
        class="anime-search-input"
        placeholder="🔍 搜索动漫人物 / 作品名称..."
        @input="fetchList"
      />
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="anime-loading">加载角色中...</div>

    <!-- 空状态 -->
    <div v-else-if="characters.length === 0" class="anime-empty">
      <div style="font-size: 2.5rem; margin-bottom: 12px;">🎌</div>
      <p>没有找到匹配的动漫人物</p>
    </div>

    <!-- 角色卡片列表 -->
    <div v-else class="anime-grid">
      <div
        v-for="c in characters"
        :key="c.id"
        class="anime-card"
        @click="openDetail(c.id)"
      >
        <div class="anime-card-avatar">{{ c.avatar }}</div>
        <div class="anime-card-info">
          <div class="anime-card-name">{{ c.name }}</div>
          <div class="anime-card-work">{{ c.work }}</div>
          <div class="anime-card-tags">
            <span v-for="t in c.tags" :key="t" class="anime-tag">{{ t }}</span>
          </div>
        </div>
        <span class="anime-card-arrow">›</span>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="detail" class="modal-backdrop" @click.self="detail = null">
      <div class="modal-card anime-detail-card">
        <button class="modal-close" @click="detail = null">✕</button>
        <div class="anime-detail-header">
          <div class="anime-detail-avatar">{{ detail.avatar }}</div>
          <div>
            <h2 class="anime-detail-name">{{ detail.name }}</h2>
            <div class="anime-detail-en">{{ detail.name_en }}</div>
            <div class="anime-detail-work">
              <span class="anime-detail-work-label">作品</span>
              {{ detail.work }} <span class="anime-detail-en">({{ detail.work_en }})</span>
            </div>
          </div>
        </div>

        <div class="anime-detail-tags">
          <span v-for="t in detail.tags" :key="t" class="anime-tag">{{ t }}</span>
        </div>

        <div class="anime-detail-meta-row">
          <div class="anime-meta-item">
            <span class="anime-meta-label">性格</span>
            <span class="anime-meta-value">{{ detail.personality }}</span>
          </div>
          <div class="anime-meta-item">
            <span class="anime-meta-label">声优</span>
            <span class="anime-meta-value">{{ detail.voice_actor }}</span>
          </div>
        </div>

        <div class="anime-detail-intro">
          <h3 class="anime-detail-section-title">人物介绍</h3>
          <p class="anime-detail-text">{{ detail.introduction }}</p>
        </div>

        <div class="anime-detail-quote">
          <span class="anime-quote-mark">❝</span>
          <p>{{ detail.quote }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetch } from '../utils/api'

const characters = ref([])
const loading = ref(true)
const searchQuery = ref('')
const detail = ref(null)

const fetchList = async () => {
  loading.value = true
  try {
    const params = searchQuery.value.trim()
      ? `?keyword=${encodeURIComponent(searchQuery.value.trim())}`
      : ''
    const res = await apiFetch(`/anime/list${params}`)
    const data = await res.json()
    if (res.ok && data.success) {
      characters.value = data.characters || []
    }
  } catch {
    characters.value = []
  } finally {
    loading.value = false
  }
}

const openDetail = async (id) => {
  try {
    const res = await apiFetch(`/anime/${id}`)
    const data = await res.json()
    if (res.ok && data.success) {
      detail.value = data.character
    }
  } catch {
    alert('加载角色详情失败')
  }
}

onMounted(fetchList)
</script>

<style scoped>
.anime-container {
  min-height: 80vh;
  padding: 0 16px 40px;
}
.anime-header {
  position: sticky;
  top: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  padding: 12px 0;
  border-bottom: 1px solid var(--x-border);
  z-index: 10;
}
.anime-search-box {
  padding: 12px 0;
}
.anime-search-input {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 14px;
  border-radius: 9999px;
  border: 1px solid var(--x-border);
  background: #f7f9fa;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.anime-search-input:focus {
  border-color: var(--x-blue);
  box-shadow: 0 0 0 3px rgba(29, 155, 240, 0.15);
  background: #fff;
}
.anime-loading,
.anime-empty {
  text-align: center;
  color: var(--x-text-gray);
  padding: 60px 0;
}
.anime-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
.anime-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border: 1px solid var(--x-border);
  border-radius: 16px;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}
.anime-card:hover {
  background: var(--x-bg-hover);
  transform: translateY(-1px);
}
.anime-card-avatar {
  width: 56px;
  height: 56px;
  min-width: 56px;
  border-radius: 16px;
  background: #f7f9fa;
  border: 1px solid var(--x-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
}
.anime-card-info {
  flex: 1;
  min-width: 0;
}
.anime-card-name {
  font-weight: 800;
  font-size: 1.05rem;
}
.anime-card-work {
  font-size: 0.85rem;
  color: var(--x-text-gray);
  margin-top: 2px;
}
.anime-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.anime-tag {
  background: #eef4ff;
  color: var(--x-blue);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 9999px;
}
.anime-card-arrow {
  color: var(--x-text-gray);
  font-size: 1.4rem;
  font-weight: 300;
}

/* 详情弹窗 */
.anime-detail-card {
  max-width: 480px !important;
  max-height: 85vh;
  overflow-y: auto;
  padding: 24px 22px;
  text-align: left;
}
.modal-backdrop {
  position: fixed; top: 0; bottom: 0; left: 0; right: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-card {
  width: 90%;
  max-width: 450px;
  background: white;
  border-radius: 20px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}
.modal-close {
  position: absolute; top: 16px; right: 16px;
  background: transparent; border: none;
  font-size: 1.25rem; font-weight: bold;
  cursor: pointer; color: var(--x-text-gray);
  z-index: 5;
}
.anime-detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}
.anime-detail-avatar {
  width: 72px;
  height: 72px;
  min-width: 72px;
  border-radius: 20px;
  background: #f7f9fa;
  border: 1px solid var(--x-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.6rem;
}
.anime-detail-name {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 800;
}
.anime-detail-en {
  font-size: 0.8rem;
  color: var(--x-text-gray);
}
.anime-detail-work {
  margin-top: 6px;
  font-size: 0.9rem;
  color: var(--x-text-main);
}
.anime-detail-work-label {
  background: #f0f1f3;
  color: var(--x-text-gray);
  font-size: 0.72rem;
  padding: 1px 6px;
  border-radius: 6px;
  margin-right: 6px;
}
.anime-detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}
.anime-detail-meta-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #f7f9fa;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 16px;
}
.anime-meta-item {
  display: flex;
  gap: 8px;
}
.anime-meta-label {
  color: var(--x-text-gray);
  font-size: 0.85rem;
  min-width: 40px;
}
.anime-meta-value {
  font-size: 0.9rem;
  font-weight: 600;
}
.anime-detail-section-title {
  margin: 0 0 8px 0;
  font-size: 0.95rem;
  font-weight: 800;
}
.anime-detail-text {
  margin: 0;
  font-size: 0.92rem;
  line-height: 1.7;
  color: var(--x-text-main);
}
.anime-detail-quote {
  margin-top: 18px;
  background: #fff5f5;
  border-left: 4px solid #ff7a7a;
  border-radius: 0 12px 12px 0;
  padding: 14px 16px;
}
.anime-quote-mark {
  color: #ff5c5c;
  font-size: 1.2rem;
  font-weight: 800;
}
.anime-detail-quote p {
  margin: 4px 0 0 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #b91c1c;
}
</style>