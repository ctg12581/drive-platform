<!-- src/views/AnimeView.vue · 动漫图鉴（以动漫作品为主 · 中日美） -->
<template>
  <div class="anime-container">
    <div class="anime-header">
      <h2 class="anime-title">🌏 动漫图鉴</h2>
      <p class="anime-subtitle">中日美三地 · 以动漫作品为分类浏览</p>
    </div>

    <!-- 地区筛选 -->
    <div class="anime-region-tabs" role="tablist" aria-label="按地区筛选">
      <button
        v-for="r in regions"
        :key="r.key"
        type="button"
        role="tab"
        class="anime-region-tab"
        :class="{ active: activeRegion === r.key }"
        :style="activeRegion === r.key ? regionActiveStyle(r.key) : null"
        :aria-selected="activeRegion === r.key"
        @click="switchRegion(r.key)"
      >
        <span class="anime-region-emoji">{{ r.emoji }}</span>
        <span class="anime-region-name">{{ r.name }}</span>
        <span class="anime-region-count">{{ r.count }}</span>
      </button>
    </div>

    <div class="anime-search-box">
      <div class="anime-search-pill">
        <svg viewBox="0 0 24 24" class="search-icon-svg"><path d="M10.5 3a7.5 7.5 0 1 1-4.55 13.46l-3.2 3.2a1 1 0 1 1-1.42-1.42l3.2-3.2A7.5 7.5 0 0 1 10.5 3zm0 2a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11z"/></svg>
        <input type="text" v-model="searchQuery" class="anime-search-input" :placeholder="searchPlaceholder" @input="onSearch" />
      </div>
    </div>

    <!-- 动漫主页：以作品为主，下面才是角色 -->
    <template v-if="activeWork">
      <div class="work-hero">
        <button class="work-back-btn" @click="backToWorks">‹ 返回动漫列表</button>
        <div class="work-hero-body">
          <div class="work-hero-poster" :style="{ background: themeOf(activeWork.region).grad }">
            <img
              v-if="activeWork.cover"
              class="work-hero-poster-img"
              :src="activeWork.cover"
              :alt="activeWork.work"
              @error="onWorkImgError($event, activeWork)"
            />
            <span v-else class="work-hero-poster-emoji">{{ activeWork.region_emoji || '📺' }}</span>
          </div>
          <div class="work-hero-info">
            <span class="anime-region-badge inline" :style="{ background: themeOf(activeWork.region).solid }">
              {{ activeWork.region_emoji }} {{ activeWork.region_name }}
            </span>
            <h2 class="work-hero-title">{{ activeWork.work }}</h2>
            <div class="work-hero-en" v-if="activeWork.work_en && activeWork.work_en !== activeWork.work">
              {{ activeWork.work_en }}
            </div>
            <div class="work-hero-tags">
              <span v-for="t in (activeWork.tags || [])" :key="t" class="xhs-tag">{{ t }}</span>
            </div>
            <div class="work-hero-meta">
              <span class="work-hero-meta-item"><strong>{{ activeWork.count }}</strong> 位角色</span>
              <span class="work-hero-meta-item">{{ activeWork.region_full }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="section-title">角色<template v-if="!loadingChars">（{{ characters.length }}）</template></div>

      <div v-if="loadingChars" class="anime-loading">加载角色中…</div>
      <div v-else-if="characters.length === 0" class="xhs-empty">
        <div style="font-size:2.5rem;margin-bottom:12px;">🎭</div>
        <p>没有找到匹配的角色</p>
      </div>
      <div v-else class="anime-grid">
        <div v-for="(c, idx) in characters" :key="c.id" class="anime-card" @click="openDetail(c.id)">
          <div class="anime-cover" :style="coverStyle(c, idx)">
            <img v-if="c.image_url" class="anime-cover-img" :src="c.image_url" :alt="c.name" loading="lazy" @error="onImgError($event, c)" />
            <span v-else class="anime-cover-emoji">{{ c.avatar || '🎭' }}</span>
          </div>
          <div class="anime-card-info">
            <div class="anime-card-name">{{ c.name }}</div>
            <div class="anime-card-work" v-if="c.name_en">{{ c.name_en }}</div>
            <div class="anime-card-tags">
              <span v-for="t in c.tags.slice(0, 3)" :key="t" class="xhs-tag">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 动漫列表：作品为主 -->
    <template v-else>
      <div class="anime-section-hint" v-if="!loadingWorks">
        共 {{ totalWorks }} 部动漫<template v-if="works.length < totalWorks">，已加载 {{ works.length }}</template>
      </div>
      <div v-if="loadingWorks" class="anime-loading">加载动漫列表…</div>
      <div v-else-if="works.length === 0" class="xhs-empty">
        <div style="font-size:2.5rem;margin-bottom:12px;">📚</div>
        <p>没有找到匹配的动漫</p>
      </div>
      <template v-else>
        <div class="work-grid">
          <div v-for="w in works" :key="w.id" class="work-card" @click="openWork(w)">
            <div class="work-cover" :style="{ background: themeOf(w.region).grad }">
              <span class="anime-region-badge" :style="{ background: themeOf(w.region).solid }">
                {{ w.region_emoji }} {{ w.region_name }}
              </span>
              <img v-if="w.cover" class="work-cover-img" :src="w.cover" :alt="w.work" loading="lazy" @error="onWorkImgError($event, w)" />
              <span v-else class="work-cover-emoji">{{ w.region_emoji || '📺' }}</span>
            </div>
            <div class="work-info">
              <div class="work-name">{{ w.work }}</div>
              <div class="work-sub" v-if="w.work_en && w.work_en !== w.work">{{ w.work_en }}</div>
              <div class="work-tags">
                <span v-for="t in (w.tags || []).slice(0, 3)" :key="t" class="xhs-tag">{{ t }}</span>
              </div>
              <div class="work-count">{{ w.count }} 位角色 ›</div>
            </div>
          </div>
        </div>
        <div v-if="worksHasMore" class="load-more-wrap">
          <button class="load-more-btn" :disabled="loadingMoreWorks" @click="loadMoreWorks">
            {{ loadingMoreWorks ? '加载中…' : '加载更多动漫' }}
          </button>
        </div>
      </template>
    </template>

    <!-- 角色详情弹窗 -->
    <div v-if="detail" class="modal-backdrop" @click.self="detail = null">
      <div class="modal-card anime-detail-card">
        <button class="modal-close" @click="detail = null">✕</button>
        <div class="anime-detail-cover" :style="{ background: detailTheme.grad }">
          <img v-if="detail.image_url" class="anime-detail-cover-img" :src="detail.image_url" :alt="detail.name" />
          <span v-else class="anime-detail-cover-emoji">{{ detail.avatar || '🎭' }}</span>
        </div>
        <div class="anime-detail-inner">
          <div class="anime-detail-header">
            <div>
              <div class="anime-detail-region" :style="{ background: detailTheme.soft, color: detailTheme.solid }">
                {{ detail.region_emoji }} {{ detail.region_full }} · {{ detail.region_name }}
              </div>
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
            <div v-if="detail.personality" class="anime-meta-item">
              <span class="anime-meta-label">性格</span>
              <span class="anime-meta-value">{{ detail.personality }}</span>
            </div>
            <div v-if="detail.voice_actor" class="anime-meta-item">
              <span class="anime-meta-label">配音</span>
              <span class="anime-meta-value">{{ detail.voice_actor }}</span>
            </div>
          </div>

          <div v-if="detail.introduction" class="anime-detail-intro">
            <h3 class="anime-detail-section-title">人物介绍</h3>
            <p class="anime-detail-text">{{ detail.introduction }}</p>
          </div>

          <div v-if="detail.quote" class="anime-detail-quote" :style="{ background: detailTheme.soft, borderLeftColor: detailTheme.solid }">
            <span class="anime-quote-mark" :style="{ color: detailTheme.solid }">❝</span>
            <p :style="{ color: detailTheme.solid }">{{ detail.quote }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiFetch } from '../utils/api'
import { cachedFetch } from '../utils/cache'

const regions = ref([])
const works = ref([])
const characters = ref([])
const loadingWorks = ref(true)
const loadingChars = ref(false)
const searchQuery = ref('')
const activeRegion = ref('all')
const activeWork = ref(null)
const detail = ref(null)

// 动漫列表分页（角色数据进入某部动漫后再拉取）
const WORKS_PAGE_SIZE = 30
const worksPage = ref(1)
const worksHasMore = ref(false)
const loadingMoreWorks = ref(false)
const totalWorks = ref(0)

// 各地区配色（active 高亮 / 封面渐变 / 徽标 / 弹窗）
const REGION_THEME = {
  jp: { solid: '#ff5c8a', soft: 'rgba(255, 92, 138, 0.10)', grad: 'linear-gradient(135deg,#ffe3ea 0%,#fff3f6 100%)' },
  cn: { solid: '#e03131', soft: 'rgba(224, 49, 49, 0.10)', grad: 'linear-gradient(135deg,#ffe2de 0%,#fff4f1 100%)' },
  us: { solid: '#2f6bff', soft: 'rgba(47, 107, 255, 0.10)', grad: 'linear-gradient(135deg,#e0edff 0%,#f1f7ff 100%)' },
}
const ALL_THEME = { solid: '#1f1f1f', soft: 'rgba(0, 0, 0, 0.06)', grad: 'linear-gradient(135deg,#f2f2f5 0%,#fafafa 100%)' }
const themeOf = (key) => (key && REGION_THEME[key]) || ALL_THEME

const detailTheme = computed(() => themeOf(detail.value?.region))
const searchPlaceholder = computed(() =>
  activeWork.value ? '搜索该动漫的角色…' : '搜索动漫…',
)

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
  const background = REGION_THEME[c.region]?.grad || GRADS[h % GRADS.length]
  return { background, height: 150 + (h % 4) * 16 + 'px' }
}

const loadRegions = async () => {
  try {
    const data = await cachedFetch(
      'anime:regions',
      async () => {
        const res = await apiFetch('/anime/regions')
        const json = await res.json()
        if (!res.ok || !json.success) throw new Error('获取地区汇总失败')
        return json
      },
      { ttl: 10 * 60 * 1000 },
    )
    if (Array.isArray(data.regions) && data.regions.length) regions.value = data.regions
  } catch {
    regions.value = []
  }
}

const fetchWorksPage = async (targetPage) => {
  const qs = new URLSearchParams()
  if (activeRegion.value && activeRegion.value !== 'all') qs.set('region', activeRegion.value)
  const kw = searchQuery.value.trim()
  if (kw) qs.set('keyword', kw)
  qs.set('page', String(targetPage))
  qs.set('page_size', String(WORKS_PAGE_SIZE))
  const res = await apiFetch(`/anime/works?${qs.toString()}`)
  const json = await res.json()
  if (!res.ok || !json.success) throw new Error('获取动漫列表失败')
  return json
}

const loadWorks = async (force = false) => {
  loadingWorks.value = true
  worksPage.value = 1
  try {
    const region = activeRegion.value
    const keyword = searchQuery.value.trim()
    const data = await cachedFetch(
      `anime:works:${region}:${keyword}:1`,
      () => fetchWorksPage(1),
      { ttl: 10 * 60 * 1000, force },
    )
    works.value = data.works || []
    worksHasMore.value = !!data.has_more
    totalWorks.value = data.total || works.value.length
  } catch {
    works.value = []
    worksHasMore.value = false
    totalWorks.value = 0
  } finally {
    loadingWorks.value = false
  }
}

const loadMoreWorks = async () => {
  if (loadingMoreWorks.value || !worksHasMore.value) return
  loadingMoreWorks.value = true
  const nextPage = worksPage.value + 1
  try {
    const region = activeRegion.value
    const keyword = searchQuery.value.trim()
    const data = await cachedFetch(
      `anime:works:${region}:${keyword}:${nextPage}`,
      () => fetchWorksPage(nextPage),
      { ttl: 10 * 60 * 1000 },
    )
    works.value = works.value.concat(data.works || [])
    worksPage.value = nextPage
    worksHasMore.value = !!data.has_more
    totalWorks.value = data.total ?? totalWorks.value
  } catch {
    /* 单次加载失败保留已加载动漫 */
  } finally {
    loadingMoreWorks.value = false
  }
}

const loadCharacters = async (force = false) => {
  if (!activeWork.value) return
  loadingChars.value = true
  try {
    const workId = activeWork.value.id
    const keyword = searchQuery.value.trim()
    const qs = new URLSearchParams()
    if (workId) qs.set('work_id', String(workId))
    if (keyword) qs.set('keyword', keyword)
    const data = await cachedFetch(
      `anime:chars:${workId}:${keyword}`,
      async () => {
        const res = await apiFetch(`/anime/list?${qs.toString()}`)
        const json = await res.json()
        if (!res.ok || !json.success) throw new Error('获取角色列表失败')
        return json
      },
      { ttl: 10 * 60 * 1000, force },
    )
    characters.value = data.characters || []
  } catch {
    characters.value = []
  } finally {
    loadingChars.value = false
  }
}

let searchTimer = null
const onSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    activeWork.value ? loadCharacters() : loadWorks()
  }, 250)
}

const switchRegion = (key) => {
  if (activeRegion.value === key) return
  activeRegion.value = key
  activeWork.value = null
  characters.value = []
  loadWorks()
}

const openWork = (work) => {
  activeWork.value = work
  characters.value = []
  loadCharacters()
  if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' })
}

const backToWorks = () => {
  activeWork.value = null
  characters.value = []
  loadWorks()
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

const onImgError = (event, character) => {
  if (character) character.image_url = ''
  if (event?.target) event.target.style.display = 'none'
}
const onWorkImgError = (event, work) => {
  if (work) work.cover = ''
  if (event?.target) event.target.style.display = 'none'
}

onMounted(() => {
  loadRegions()
  loadWorks()
})
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
  padding: 16px 4px 10px;
  z-index: 20;
}
.anime-title { margin: 0; font-size: 1.2rem; font-weight: 800; }
.anime-subtitle { margin: 4px 0 0; font-size: 0.76rem; color: var(--xhs-text-3); }

/* 地区筛选 */
.anime-region-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 4px 2px 10px;
  scrollbar-width: none;
}
.anime-region-tabs::-webkit-scrollbar { display: none; }
.anime-region-tab {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 13px;
  border-radius: var(--xhs-radius-pill);
  border: 1.5px solid #ececf0;
  background: #f6f6f8;
  color: var(--xhs-text-2, #555);
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.anime-region-tab:active { transform: scale(0.97); }
.anime-region-emoji { font-size: 0.95rem; }
.anime-region-count {
  min-width: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: rgba(0, 0, 0, 0.07);
  font-size: 0.7rem;
  font-weight: 700;
  text-align: center;
}
.anime-region-tab.active .anime-region-count { background: rgba(255, 255, 255, 0.28); }

.anime-search-box { padding: 2px 0 14px; }
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
.anime-section-hint { font-size: 0.76rem; color: var(--xhs-text-3); padding: 0 4px 10px; }
.section-title { font-size: 0.95rem; font-weight: 800; color: var(--xhs-text); margin: 2px 4px 10px; }

/* 角色瀑布流 */
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
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.anime-region-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 9px;
  color: #fff;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.2px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}
.anime-region-badge.inline { position: static; box-shadow: none; }
.anime-cover-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  padding: 8px;
  box-sizing: border-box;
}
.anime-cover-emoji { font-size: 2.6rem; filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.12)); }
.anime-card-info { padding: 9px 10px 11px; }
.anime-card-name { font-weight: 800; font-size: 0.92rem; color: var(--xhs-text); }
.anime-card-work { font-size: 0.74rem; color: var(--xhs-text-3); margin-top: 2px; }
.anime-card-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }

/* 动漫列表网格（海报卡片） */
.work-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.work-card {
  background: #fff;
  border: 1px solid #f2f2f4;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  transition: transform 0.15s, box-shadow 0.15s;
  animation: xhs-fade-up 0.3s ease both;
}
.work-card:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(0, 0, 0, 0.09); }
.work-cover {
  position: relative;
  aspect-ratio: 3 / 4;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.work-cover-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  padding: 10px;
  box-sizing: border-box;
}
.work-cover-emoji { font-size: 2.6rem; }
.work-info { padding: 9px 11px 12px; }
.work-name {
  font-weight: 800;
  font-size: 0.92rem;
  color: var(--xhs-text);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.work-sub {
  font-size: 0.72rem;
  color: var(--xhs-text-3);
  margin-top: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.work-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 7px; }
.work-count { font-size: 0.72rem; color: var(--xhs-red); font-weight: 700; margin-top: 8px; }
.load-more-wrap { display: flex; justify-content: center; padding: 14px 0 4px; }
.load-more-btn {
  border: 1.5px solid #ececf0;
  background: #f6f6f8;
  color: var(--xhs-text-2, #555);
  border-radius: 999px;
  padding: 9px 22px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
}
.load-more-btn:disabled { opacity: 0.6; cursor: default; }

/* 动漫主页 Hero */
.work-hero { padding: 2px 2px 14px; }
.work-back-btn {
  border: 1.5px solid #ececf0;
  background: #f6f6f8;
  color: var(--xhs-text-2, #555);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  margin-bottom: 12px;
}
.work-hero-body { display: flex; gap: 14px; }
.work-hero-poster {
  flex: 0 0 132px;
  width: 132px;
  aspect-ratio: 3 / 4;
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.work-hero-poster-img { width: 100%; height: 100%; object-fit: contain; padding: 8px; box-sizing: border-box; }
.work-hero-poster-emoji { font-size: 2.6rem; }
.work-hero-info { flex: 1; min-width: 0; }
.work-hero-title { margin: 6px 0 0; font-size: 1.15rem; font-weight: 900; color: var(--xhs-text); line-height: 1.3; }
.work-hero-en { font-size: 0.76rem; color: var(--xhs-text-3); margin-top: 3px; }
.work-hero-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
.work-hero-meta { display: flex; gap: 14px; margin-top: 12px; font-size: 0.8rem; color: var(--xhs-text-3); }
.work-hero-meta-item strong { color: var(--xhs-text); font-size: 0.95rem; }

/* 角色详情弹窗 */
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
  position: relative;
  height: 200px;
  display: flex; align-items: center; justify-content: center;
}
.anime-detail-cover-img {
  width: 100%; height: 100%;
  object-fit: contain; object-position: center; padding: 10px; box-sizing: border-box;
}
.anime-detail-cover-emoji { font-size: 4rem; filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.14)); }
.anime-detail-inner { padding: 18px 22px 24px; overflow-y: auto; }
.anime-detail-header { display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }
.anime-detail-region {
  display: inline-block;
  font-size: 0.68rem;
  font-weight: 800;
  padding: 2px 9px;
  border-radius: 8px;
  margin-bottom: 7px;
}
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
  margin-top: 18px; border-left: 4px solid var(--xhs-red);
  border-radius: 0 12px 12px 0; padding: 14px 16px;
}
.anime-quote-mark { font-size: 1.2rem; font-weight: 800; }
.anime-detail-quote p { margin: 4px 0 0; font-size: 0.93rem; font-weight: 600; }
</style>
