<!-- src/views/AnimeView.vue · 小红书风格动漫图鉴 -->
<template>
  <div class="anime-container">
    <div class="anime-header">
      <h2 class="anime-title">🎌 动漫人物图鉴</h2>
    </div>

    <div class="anime-search-box">
      <div class="anime-search-pill">
        <svg viewBox="0 0 24 24" class="search-icon-svg"><path d="M10.5 3a7.5 7.5 0 1 1-4.55 13.46l-3.2 3.2a1 1 0 1 1-1.42-1.42l3.2-3.2A7.5 7.5 0 0 1 10.5 3zm0 2a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11z"/></svg>
        <input type="text" v-model="searchQuery" class="anime-search-input" placeholder="搜索动漫人物 / 作品…" @input="fetchList" />
      </div>
    </div>

    <div v-if="loading" class="anime-loading">加载角色中…</div>

    <div v-else-if="characters.length === 0" class="xhs-empty">
      <div style="font-size:2.5rem;margin-bottom:12px;">🎌</div>
      <p>没有找到匹配的动漫人物</p>
    </div>

    <div v-else class="anime-grid">
      <div v-for="(c, idx) in characters" :key="c.id" class="anime-card" @click="openDetail(c.id)">
        <div class="anime-cover" :style="coverStyle(c, idx)">
          <span class="anime-cover-emoji">{{ c.avatar }}</span>
        </div>
        <div class="anime-card-info">
          <div class="anime-card-name">{{ c.name }}</div>
          <div class="anime-card-work">{{ c.work }}</div>
          <div class="anime-card-tags">
            <span v-for="t in c.tags" :key="t" class="xhs-tag">{{ t }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="detail" class="modal-backdrop" @click.self="detail = null">
      <div class="modal-card anime-detail-card">
        <button class="modal-close" @click="detail = null">✕</button>
        <div class="anime-detail-cover">
          <span class="anime-detail-cover-emoji">{{ detail.avatar }}</span>
        </div>
        <div class="anime-detail-inner">
          <div class="anime-detail-header">
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
            <span v-for="t in detail.tags" :key="t" class="xhs-tag">{{ t }}</span>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetch } from '../utils/api'
import { cachedFetch } from '../utils/cache'

const characters = ref([])
const loading = ref(true)
const searchQuery = ref('')
const detail = ref(null)

const GRADS = [
  'linear-gradient(135deg,#ffe3ea 0%,#fff3f6 100%)',
  'linear-gradient(135deg,#e0edff 0%,#f1f7ff 100%)',
  'linear-gradient(135deg,#e3f8e9 0%,#f2fdf5 100%)',
  'linear-gradient(135deg,#fff1d6 0%,#fffaef 100%)',
  'linear-gradient(135deg,#ece4ff 0%,#f7f2ff 100%)',
  'linear-gradient(135deg,#ffe4d6 0%,#fff3ec 100%)',
]
const coverStyle = (c, idx) => {
  let h = 0
  const s = String(c.id ?? '') + (c.name || '') + idx
  for (let i = 0; i < s.length; i++) { h = (h * 31 + s.charCodeAt(i)) >>> 0 }
  return { background: GRADS[h % GRADS.length], height: 132 + (h % 4) * 16 + 'px' }
}

const fetchList = async () => {
  loading.value = true
  try {
    const keyword = searchQuery.value.trim()
    const params = keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''
    characters.value = await cachedFetch(
      `anime:list:${keyword}`,
      async () => {
        const res = await apiFetch(`/anime/list${params}`)
        const data = await res.json()
        if (!res.ok || !data.success) throw new Error('获取动漫列表失败')
        return data.characters || []
      },
      { ttl: 10 * 60 * 1000 },
    )
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
  min-height: calc(100vh - var(--app-top) - var(--app-bottom));
  padding: 0 12px 32px;
  background: #fff;
}
.anime-header {
  position: sticky;
  top: var(--app-top);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(14px);
  padding: 16px 4px 12px;
  z-index: 20;
}
.anime-title { margin: 0; font-size: 1.2rem; font-weight: 800; }

.anime-search-box { padding: 4px 0 14px; }
.anime-search-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f4f4f6;
  border-radius: var(--xhs-radius-pill);
  padding: 9px 16px;
  border: 1.5px solid transparent;
  transition: all 0.16s;
}
.anime-search-pill:focus-within { background: #fff; border-color: var(--xhs-red); box-shadow: 0 0 0 3px rgba(255, 36, 66, 0.1); }
.search-icon-svg { width: 17px; height: 17px; fill: var(--xhs-text-3); flex-shrink: 0; }
.anime-search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.9rem;
  outline: none;
  color: var(--xhs-text);
}
.anime-search-input::placeholder { color: var(--xhs-text-3); }

.anime-loading { text-align: center; color: var(--xhs-text-3); padding: 60px 0; }

.anime-grid { columns: 2; column-gap: 10px; }
.anime-card {
  break-inside: avoid;
  margin: 0 0 10px;
  background: #fff;
  border: 1px solid #f2f2f4;
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: transform 0.15s, box-shadow 0.15s;
  animation: xhs-fade-up 0.3s ease both;
}
.anime-card:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(0, 0, 0, 0.09); }
.anime-cover {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.anime-cover-emoji { font-size: 2.6rem; filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.12)); }
.anime-card-info { padding: 9px 10px 11px; }
.anime-card-name { font-weight: 800; font-size: 0.92rem; color: var(--xhs-text); }
.anime-card-work { font-size: 0.76rem; color: var(--xhs-text-3); margin-top: 3px; }
.anime-card-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }

/* 详情弹窗 */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.45); backdrop-filter: blur(2px);
  display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px;
}
.modal-card {
  width: 100%; max-width: 440px; background: #fff; border-radius: 22px; max-height: 86vh;
  display: flex; flex-direction: column; overflow: hidden; position: relative;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}
.modal-close {
  position: absolute; top: 12px; right: 12px; z-index: 3;
  width: 30px; height: 30px; border-radius: 50%; background: rgba(0, 0, 0, 0.28);
  color: #fff; border: none; font-size: 0.85rem; cursor: pointer;
}
.anime-detail-cover {
  height: 140px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #ffe3ea, #fff2f5 60%, #f3f7ff);
}
.anime-detail-cover-emoji { font-size: 4rem; filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.14)); }
.anime-detail-inner { padding: 18px 22px 24px; overflow-y: auto; }
.anime-detail-header { display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }
.anime-detail-name { margin: 0; font-size: 1.3rem; font-weight: 900; }
.anime-detail-en { font-size: 0.78rem; color: var(--xhs-text-3); }
.anime-detail-work { margin-top: 6px; font-size: 0.86rem; color: var(--xhs-text); }
.anime-detail-work-label {
  background: var(--xhs-red-soft); color: var(--xhs-red);
  font-size: 0.7rem; font-weight: 700; padding: 1px 7px; border-radius: 6px; margin-right: 6px;
}
.anime-detail-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
.anime-detail-meta-row {
  display: flex; flex-direction: column; gap: 10px;
  background: #fafafa; border-radius: 14px; padding: 14px; margin-bottom: 16px;
}
.anime-meta-item { display: flex; gap: 10px; }
.anime-meta-label { color: var(--xhs-text-3); font-size: 0.84rem; min-width: 40px; }
.anime-meta-value { font-size: 0.88rem; font-weight: 600; }
.anime-detail-section-title { margin: 0 0 8px; font-size: 0.94rem; font-weight: 800; }
.anime-detail-text { margin: 0; font-size: 0.9rem; line-height: 1.75; color: var(--xhs-text); }
.anime-detail-quote {
  margin-top: 18px; background: var(--xhs-red-soft);
  border-left: 4px solid var(--xhs-red); border-radius: 0 12px 12px 0; padding: 14px 16px;
}
.anime-quote-mark { color: var(--xhs-red); font-size: 1.2rem; font-weight: 800; }
.anime-detail-quote p { margin: 4px 0 0; font-size: 0.93rem; font-weight: 600; color: var(--xhs-red); }
</style>
