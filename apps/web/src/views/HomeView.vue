<!-- src/views/HomeView.vue · 小红书瀑布流首页 -->
<template>
  <div class="feed-container">
    <!-- 顶部频道切换：首页（国内/国外/关注）与热榜（国内/国外） -->
    <div class="feed-tabs">
      <template v-if="isRankView">
        <button @click="changeTab('rank')" :class="['feed-tab-btn', { active: currentSubTab === 'rank' }]">
          <span class="tab-text">国内</span>
        </button>
        <button @click="changeTab('rank_intl')" :class="['feed-tab-btn', { active: currentSubTab === 'rank_intl' }]">
          <span class="tab-text">国外</span>
        </button>
      </template>
      <template v-else>
        <button @click="changeTab('cn')" :class="['feed-tab-btn', { active: currentSubTab === 'cn' }]">
          <span class="tab-text">国内</span>
        </button>
        <button @click="changeTab('intl')" :class="['feed-tab-btn', { active: currentSubTab === 'intl' }]">
          <span class="tab-text">国外</span>
        </button>
        <button @click="changeTab('following')" :class="['feed-tab-btn', { active: currentSubTab === 'following' }]">
          <span class="tab-text">关注</span>
        </button>
      </template>
    </div>

    <!-- 有新动态提示 -->
    <div v-if="currentSubTab === 'following' && newPostsCount > 0" class="new-posts-banner" @click="applyNewPosts">
      {{ newPostsCount }} 条新笔记，点击查看
    </div>

    <!-- ============ 推荐 / 热榜：瀑布流卡片 ============ -->
    <section v-if="currentSubTab !== 'following'" class="feed-section">
      <div class="section-bar">
        <span class="section-title-text">{{ isRankView ? (currentSubTab === 'rank_intl' ? '🏆 国外热榜' : '🏆 国内热榜') : currentSubTab === 'intl' ? '🌍 国外热点' : '🔥 国内热点' }}</span>
        <span class="section-count">
          {{ activeList.total }} 条<span v-if="activeList.updatedAt"> · {{ formatLocalTime(activeList.updatedAt) }}</span>
        </span>
        <button class="section-refresh" @click="loadPage(currentSubTab, 1)" :disabled="activeList.loading">
          {{ activeList.loading ? '刷新中' : '刷新' }}
        </button>
      </div>

      <div v-if="activeList.loading && activeList.items.length === 0" class="waterfall">
        <div v-for="i in 4" :key="i" class="note-card skeleton-note">
          <div class="skeleton-cover" :style="{ height: (150 + (i % 3) * 26) + 'px' }"></div>
          <div class="skeleton-body">
            <div class="skeleton-line long"></div>
            <div class="skeleton-line mid"></div>
          </div>
        </div>
      </div>

      <div v-else-if="activeList.items.length" class="waterfall">
        <article
          v-for="(n, idx) in activeList.items"
          :key="n.id"
          class="note-card"
          @click="openSource(n)"
        >
          <div class="note-cover" :class="{ 'has-image': coverImage(n) }" :style="coverStyle(n, idx)">
            <img v-if="coverImage(n)" :src="coverImage(n)" class="cover-img" loading="lazy" alt="" @error="onCoverError" />
            <div v-else class="cover-text">
              <span class="cover-text-inner">{{ coverText(n) }}</span>
              <span class="cover-watermark">{{ noteEmoji(n, idx) }}</span>
            </div>
            <span v-if="isRankView" class="cover-rank">{{ (activeList.page - 1) * NEWS_PAGE_SIZE + idx + 1 }}</span>
            <span v-else-if="n.category" class="cover-chip">{{ n.category }}</span>
            <span class="cover-jump">↗</span>
          </div>
          <div class="note-body">
            <h3 class="note-title">{{ n.title }}</h3>
            <div class="note-foot">
              <span class="note-src"><span class="note-src-icon">{{ sourceIcon(n.source) }}</span>{{ n.source }}</span>
              <span class="note-like">
                <span v-if="isRankView && n.hot">🔥 {{ formatHot(n.hot) }}</span>
                <span v-else>♡ {{ likeCount(n, idx) }}</span>
              </span>
            </div>
          </div>
        </article>
      </div>

      <div v-else class="xhs-empty">暂无数据，抓取源可能暂不可达，正在自动重试…</div>

      <div v-if="activeList.total > NEWS_PAGE_SIZE" class="pager">
        <button class="pager-btn" :disabled="activeList.page <= 1" @click="goPage(currentSubTab, activeList.page - 1)">上一页</button>
        <span class="pager-info">{{ activeList.page }} / {{ totalPages(currentSubTab) }}</span>
        <button class="pager-btn" :disabled="!activeList.hasMore" @click="goPage(currentSubTab, activeList.page + 1)">下一页</button>
      </div>
      <div class="feed-hint">内容来自各站点公开热榜 · 点击跳转原文</div>
    </section>

    <!-- ============ 关注：好友笔记瀑布流 ============ -->
    <section v-else class="feed-section">
      <div v-if="loading && posts.length === 0" class="waterfall">
        <div v-for="i in 4" :key="i" class="note-card skeleton-note">
          <div class="skeleton-cover" :style="{ height: (150 + (i % 3) * 26) + 'px' }"></div>
          <div class="skeleton-body">
            <div class="skeleton-line long"></div>
            <div class="skeleton-line mid"></div>
          </div>
        </div>
      </div>

      <template v-else>
        <div v-if="posts.length === 0" class="xhs-empty">
          👋 还没有任何笔记<br />去搜索关注新朋友，TA 们的笔记会出现在这里
        </div>

        <div v-else class="waterfall">
          <article
            v-for="(post, idx) in posts"
            :key="post.id"
            class="note-card"
            @click="openUserProfile(post.username)"
          >
            <div class="note-cover" :class="{ 'has-image': coverImage(post) }" :style="coverStyle(post, idx)">
              <img v-if="coverImage(post)" :src="coverImage(post)" class="cover-img" loading="lazy" alt="" @error="onCoverError" />
              <div v-else class="cover-text">
                <span class="cover-text-inner">{{ coverText(post) }}</span>
                <span class="cover-watermark">{{ noteEmoji(post, idx) }}</span>
              </div>
            </div>
            <div class="note-body">
              <h3 class="note-title">{{ post.content }}</h3>
              <div class="note-foot">
                <div class="note-author">
                  <span class="mini-avatar">
                    <img v-if="isUrl(post.avatar)" :src="post.avatar" class="avatar-img-el" />
                    <span v-else-if="post.avatar && post.avatar !== '👤'">{{ post.avatar }}</span>
                    <span v-else>{{ post.username[0].toUpperCase() }}</span>
                  </span>
                  <span class="note-author-name">{{ post.nickname }}</span>
                </div>
                <span class="note-like">♡ {{ likeCount(post, idx) }}</span>
              </div>
            </div>
          </article>
        </div>
      </template>

      <div v-if="followingTotal > FOLLOWING_PAGE_SIZE" class="pager">
        <button class="pager-btn" :disabled="followingPage <= 1" @click="goFollowingPage(followingPage - 1)">上一页</button>
        <span class="pager-info">{{ followingPage }} / {{ followingTotalPages() }}</span>
        <button class="pager-btn" :disabled="!followingHasMore" @click="goFollowingPage(followingPage + 1)">下一页</button>
      </div>
    </section>

    <!-- 🌟 个人主页弹窗 -->
    <div v-if="activeProfile" class="modal-backdrop" @click.self="activeProfile = null">
      <div class="modal-card profile-modal">
        <button class="modal-close" @click="activeProfile = null">✕</button>
        <div class="profile-cover"></div>
        <div class="profile-modal-head">
          <div class="modal-avatar-big">
            <img v-if="isUrl(activeProfile.user.avatar)" :src="activeProfile.user.avatar" class="avatar-img-el" />
            <span v-else-if="activeProfile.user.avatar && activeProfile.user.avatar !== '👤'">{{ activeProfile.user.avatar }}</span>
            <span v-else>{{ activeProfile.user.username[0].toUpperCase() }}</span>
          </div>
          <div class="profile-modal-meta">
            <h2 class="modal-nickname">{{ activeProfile.user.nickname }}</h2>
            <p class="modal-handle">@{{ activeProfile.user.username }}</p>
          </div>
        </div>

        <div class="modal-body">
          <h3 class="modal-tab-title">TA 的笔记 ({{ activeProfile.posts.length }})</h3>
          <div v-if="activeProfile.posts.length === 0" class="xhs-empty" style="padding:32px 0;">TA 还没有发布过任何笔记。</div>
          <div v-for="p in activeProfile.posts" :key="p.id" class="modal-note">
            <img v-if="coverImage(p)" :src="coverImage(p)" class="modal-note-img" loading="lazy" alt="" @error="onCoverError" />
            <div class="modal-note-time">{{ formatLocalTime(p.time) }}</div>
            <div class="modal-note-content">{{ p.content }}</div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { isUrl } from '@drive/shared'
import { useAuthStore } from '../store/auth'
import { useMomentsStore } from '../store/home'
import { useChatStore } from '../store/chat'
import { formatLocalTime } from '../utils/date'
import { apiFetch } from '../utils/api'
import { fetchUserProfile } from '../utils/userProfile'

const authStore = useAuthStore()
const momentsStore = useMomentsStore()
const chatStore = useChatStore()
const route = useRoute()
const router = useRouter()

// 频道可由底部「热榜」入口通过 ?tab=rank 打开
const queryTab = route.query.tab
const initialTab = ['rank', 'rank_intl', 'following', 'intl'].includes(queryTab) ? queryTab : 'cn'
const currentSubTab = ref(initialTab) // 'cn' 国内, 'intl' 国外, 'rank' 热榜国内, 'rank_intl' 热榜国外, 'following' 关注
const posts = ref(momentsStore.cachedPosts)
const loading = ref(posts.value.length === 0)
const activeProfile = ref(null)

// 关注流分页状态（每页 20 条）
const FOLLOWING_PAGE_SIZE = 20
const followingPage = ref(1)
const followingTotal = ref(0)
const followingHasMore = ref(false)

// 热点 / 榜单两个列表的分页状态（每页 20 条）
const NEWS_PAGE_SIZE = 20
const lists = reactive({
  cn: { items: [], loading: false, page: 1, total: 0, hasMore: false, updatedAt: null },
  intl: { items: [], loading: false, page: 1, total: 0, hasMore: false, updatedAt: null },
  rank_cn: { items: [], loading: false, page: 1, total: 0, hasMore: false, updatedAt: null },
  rank_intl: { items: [], loading: false, page: 1, total: 0, hasMore: false, updatedAt: null },
})

// 频道 -> 列表 key / 接口 kind / region
const TAB_META = {
  cn: { key: 'cn', kind: 'news', region: 'cn' },
  intl: { key: 'intl', kind: 'news', region: 'intl' },
  rank: { key: 'rank_cn', kind: 'rank', region: 'cn' },
  rank_intl: { key: 'rank_intl', kind: 'rank', region: 'intl' },
}

const isRankView = computed(() => currentSubTab.value === 'rank' || currentSubTab.value === 'rank_intl')

// 当前列表：国内 / 国外 / 热榜（国内 / 国外）
const activeKey = computed(() => (TAB_META[currentSubTab.value] || TAB_META.cn).key)
const activeList = computed(() => lists[activeKey.value])

// ===== 瀑布流视觉辅助：封面渐变 / 表情 / 点赞数（确定性伪随机）=====
const COVER_GRADIENTS = [
  'linear-gradient(135deg,#ffd8e2 0%,#fff0f4 100%)',
  'linear-gradient(135deg,#d9e9ff 0%,#eef5ff 100%)',
  'linear-gradient(135deg,#dcf7e3 0%,#f1fdf4 100%)',
  'linear-gradient(135deg,#fff0d1 0%,#fff9ed 100%)',
  'linear-gradient(135deg,#e8e0ff 0%,#f6f1ff 100%)',
  'linear-gradient(135deg,#ffe0d1 0%,#fff2eb 100%)',
  'linear-gradient(135deg,#d6f4ef 0%,#edfbf8 100%)',
  'linear-gradient(135deg,#fbdcee 0%,#fdeef7 100%)',
]
const COVER_EMOJIS = ['🌿', '☕', '📷', '🍜', '🎨', '🏃', '📚', '✈️', '🎧', '🌷', '🍰', '🐱', '🌊', '🍓']

const hashStr = (s = '') => {
  let h = 2166136261
  const str = String(s)
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

const seedOf = (item, idx) => hashStr(`${item?.id ?? ''}|${item?.title ?? item?.content ?? ''}|${idx}`)

const coverStyle = (item, idx) => {
  const h = seedOf(item, idx)
  const bg = COVER_GRADIENTS[h % COVER_GRADIENTS.length]
  // 让封面高度有节奏地错落，形成瀑布流
  const height = 132 + ((h >>> 5) % 6) * 16
  return { background: bg, height: height + 'px' }
}

const noteEmoji = (item, idx) => COVER_EMOJIS[seedOf(item, idx) % COVER_EMOJIS.length]

// 真实封面图：有 image 字段则用真实图片，否则回退到渐变+emoji
const coverImage = (item) => {
  const img = item && item.image
  return img && isUrl(img) ? img : ''
}
const onCoverError = (e) => {
  if (e && e.target) e.target.style.display = 'none'
}
// 无图笔记：直接把文字做成封面（仿小红书文字笔记）
const coverText = (item) => {
  const t = (item && (item.content || item.title)) || ''
  return t.trim()
}

const likeCount = (item, idx) => {
  const h = seedOf(item, idx)
  const num = 30 + (h % 6800)
  return num >= 1000 ? `${(num / 1000).toFixed(1)}k` : `${num}`
}

// 分类配色
const CAT_COLORS = {
  科技: { color: '#1d6df0', backgroundColor: '#e8f1fe' },
  财经: { color: '#d97706', backgroundColor: '#fef3c7' },
  体育: { color: '#16a34a', backgroundColor: '#dcfce7' },
  娱乐: { color: '#db2777', backgroundColor: '#fce7f3' },
  社会: { color: '#7c3aed', backgroundColor: '#ede9fe' },
  国际: { color: '#0d9488', backgroundColor: '#ccfbf1' },
  健康: { color: '#ef4444', backgroundColor: '#fee2e2' },
  教育: { color: '#2563eb', backgroundColor: '#dbeafe' },
  热点: { color: '#ff2442', backgroundColor: '#fff1f3' },
}

// 来源小图标
const SOURCE_ICONS = {
  'Google新闻': '🌐',
  'BBC中文': '📰',
  '36氪': '💼',
  '微博热搜': '🔥',
  '知乎热榜': '💡',
  '百度热搜': '🔍',
  '今日头条': '📱',
}
const sourceIcon = (source) => SOURCE_ICONS[source] || '📰'

const formatHot = (value) => {
  const num = Number(value) || 0
  return num >= 10000 ? `${(num / 10000).toFixed(1)}万` : `${num}`
}

const totalPages = (tab) => Math.max(1, Math.ceil((lists[(TAB_META[tab] || TAB_META.cn).key].total || 0) / NEWS_PAGE_SIZE))

const loadPage = async (tab, page = 1) => {
  const meta = TAB_META[tab]
  if (!meta) return
  const st = lists[meta.key]
  const target = Math.max(1, page)
  st.loading = true
  try {
    const url = `/news/hot?page=${target}&page_size=${NEWS_PAGE_SIZE}&kind=${meta.kind}&region=${meta.region}`
    const res = await apiFetch(url)
    const data = await res.json()
    if (res.ok && data.success) {
      st.items = data.news || []
      st.total = data.total || 0
      st.page = data.page || target
      st.hasMore = !!data.has_more
      st.updatedAt = data.updated_at || null
    }
  } catch (err) {
    console.error('获取列表异常:', err)
  } finally {
    st.loading = false
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const goPage = (tab, page) => {
  const key = (TAB_META[tab] || TAB_META.cn).key
  const target = Math.min(Math.max(1, page), totalPages(tab))
  if (target === lists[key].page && lists[key].items.length) return
  loadPage(tab, target)
}

const openSource = (item) => {
  if (!item || !item.url) return
  window.open(item.url, '_blank', 'noopener,noreferrer')
}

// 实时动态探针
const newPostsCount = ref(0)
let lastFetchedTime = ''
let checkInterval = null

onMounted(() => {
  if (initialTab === 'following') {
    fetchTimeline(1)
  } else {
    loadPage(initialTab, 1)
  }
  window.addEventListener('moments:new', onNewMoments)
  checkInterval = setInterval(checkNewPosts, 60000)
})

onUnmounted(() => {
  if (checkInterval) clearInterval(checkInterval)
  window.removeEventListener('moments:new', onNewMoments)
})

watch(() => momentsStore.refreshTick, () => fetchTimeline(1, true))

const fetchTimeline = async (page = 1, silent = false) => {
  const target = Math.max(1, page)
  if (!silent) loading.value = true
  try {
    const offset = (target - 1) * FOLLOWING_PAGE_SIZE
    const res = await apiFetch(`/moments/following?limit=${FOLLOWING_PAGE_SIZE}&offset=${offset}`)
    const data = await res.json()
    if (res.ok) {
      posts.value = data.moments || []
      followingPage.value = target
      followingTotal.value = data.total || 0
      followingHasMore.value = !!data.has_more

      if (target === 1) {
        if ((data.moments || []).length > 0) {
          lastFetchedTime = data.moments[0].time
          momentsStore.setPosts(data.moments)
        } else {
          lastFetchedTime = new Date().toISOString()
        }
        newPostsCount.value = 0
      }
    }
  } catch (err) {
    console.error('获取时间线异常:', err)
  } finally {
    loading.value = false
  }
}

const followingTotalPages = () => Math.max(1, Math.ceil((followingTotal.value || 0) / FOLLOWING_PAGE_SIZE))

const goFollowingPage = (page) => {
  const target = Math.min(Math.max(1, page), followingTotalPages())
  if (target === followingPage.value) return
  fetchTimeline(target)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const changeTab = (tab, fromRoute = false) => {
  if (currentSubTab.value === tab) return
  currentSubTab.value = tab
  if (tab === 'following') {
    posts.value = []
    fetchTimeline(1)
  } else {
    const meta = TAB_META[tab]
    if (meta && lists[meta.key].items.length === 0) loadPage(tab, 1)
  }
  // 同步到路由 query，保证底部导航高亮（首页 / 热榜）正确
  if (!fromRoute) {
    const query = tab === 'cn' ? {} : { tab }
    router.replace({ path: '/home', query }).catch(() => {})
  }
}

// 底部导航切换（如点「热榜」/「首页」）时，路由 query 变化 -> 同步频道
watch(
  () => route.query.tab,
  (t) => {
    const target = ['rank', 'rank_intl', 'following', 'intl'].includes(t) ? t : 'cn'
    if (target !== currentSubTab.value) changeTab(target, true)
  },
)

const onNewMoments = (event) => {
  newPostsCount.value += Number(event && event.detail) || 1
}

const checkNewPosts = async () => {
  if (!lastFetchedTime) return
  if (typeof document !== 'undefined' && document.hidden) return
  if (chatStore.connected) return
  try {
    const res = await apiFetch(`/moments/count?since=${encodeURIComponent(lastFetchedTime)}`)
    const data = await res.json()
    if (res.ok) {
      newPostsCount.value = data.count
    }
  } catch (err) {
    console.error('增量探测异常:', err)
  }
}

const applyNewPosts = () => {
  fetchTimeline(1)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const openUserProfile = async (targetUsername) => {
  try {
    activeProfile.value = await fetchUserProfile(targetUsername)
  } catch {
    alert('无法加载该用户的主页')
  }
}
</script>

<style scoped>
.feed-container {
  width: 100%;
  position: relative;
  background: #fff;
}

/* 频道切换 */
.feed-tabs {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 26px;
  height: 46px;
  position: sticky;
  top: var(--app-top);
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--xhs-line);
  z-index: 20;
}
.feed-tab-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
  height: 100%;
  display: flex;
  align-items: center;
  position: relative;
}
.tab-text {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--xhs-text-3);
  transition: color 0.15s;
}
.feed-tab-btn.active .tab-text {
  color: var(--xhs-text);
  font-weight: 800;
}
.feed-tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: 7px;
  left: 50%;
  transform: translateX(-50%);
  width: 18px;
  height: 3px;
  border-radius: 3px;
  background: var(--xhs-red);
}

/* 新笔记提示 */
.new-posts-banner {
  position: sticky;
  top: calc(var(--app-top) + 54px);
  width: fit-content;
  margin: 12px auto 0;
  background: var(--xhs-red);
  color: #fff;
  font-weight: 700;
  font-size: 0.82rem;
  padding: 8px 18px;
  border-radius: var(--xhs-radius-pill);
  box-shadow: 0 6px 16px rgba(255, 36, 66, 0.3);
  cursor: pointer;
  z-index: 15;
  animation: xhs-fade-up 0.2s ease;
}

.feed-section {
  padding-top: 4px;
}

/* 分区标题条 */
.section-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px 6px;
}
.section-title-text {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--xhs-text);
}
.section-count {
  font-size: 0.7rem;
  color: var(--xhs-text-3);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.section-refresh {
  flex: none;
  background: var(--xhs-red-soft);
  border: none;
  color: var(--xhs-red);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 5px 13px;
  border-radius: var(--xhs-radius-pill);
  cursor: pointer;
  transition: background 0.15s;
}
.section-refresh:hover:not(:disabled) {
  background: #ffe1e6;
}
.section-refresh:disabled {
  opacity: 0.6;
  cursor: default;
}

/* ===== 瀑布流 ===== */
.waterfall {
  column-count: 2;
  column-gap: 10px;
  padding: 6px 10px 10px;
}
.note-card {
  break-inside: avoid;
  -webkit-column-break-inside: avoid;
  margin: 0 0 10px;
  background: #fff;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid #f2f2f4;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  animation: xhs-fade-up 0.3s ease both;
}
.note-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.09);
}
.note-cover {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.note-cover::before,
.note-cover::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.35);
}
.note-cover.has-image::before,
.note-cover.has-image::after {
  display: none;
}
.cover-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
}
.note-cover::before {
  width: 68px;
  height: 68px;
  top: -22px;
  right: -18px;
}
.note-cover::after {
  width: 44px;
  height: 44px;
  bottom: -14px;
  left: -10px;
  background: rgba(255, 255, 255, 0.28);
}
.cover-emoji {
  font-size: 2.4rem;
  filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.12));
  z-index: 1;
}
/* 无图笔记：文字即封面 */
.cover-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 13px;
  z-index: 1;
  overflow: hidden;
}
.cover-text-inner {
  font-size: 0.84rem;
  font-weight: 800;
  line-height: 1.52;
  color: #3a2b30;
  text-align: center;
  word-break: break-word;
  letter-spacing: 0.2px;
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.cover-watermark {
  position: absolute;
  right: 10px;
  bottom: 8px;
  font-size: 1.05rem;
  opacity: 0.5;
}
.cover-chip {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  background: rgba(255, 255, 255, 0.82);
  color: #5b5b63;
  font-size: 0.62rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--xhs-radius-pill);
  backdrop-filter: blur(4px);
}
.cover-rank {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--xhs-red);
  font-size: 0.75rem;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cover-jump {
  position: absolute;
  bottom: 8px;
  right: 9px;
  z-index: 2;
  color: rgba(0, 0, 0, 0.28);
  font-size: 0.85rem;
  font-weight: 700;
  transition: opacity 0.15s, transform 0.15s;
  opacity: 0;
}
.note-card:hover .cover-jump {
  opacity: 1;
  transform: translate(1px, -1px);
}

.note-body {
  padding: 9px 10px 11px;
}
.note-title {
  margin: 0;
  font-size: 0.86rem;
  font-weight: 700;
  line-height: 1.42;
  color: var(--xhs-text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}
.note-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: 9px;
}
.note-src {
  font-size: 0.68rem;
  color: var(--xhs-text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.note-src-icon {
  margin-right: 2px;
}
.note-author {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
}
.mini-avatar {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #f2f2f4;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  overflow: hidden;
  flex-shrink: 0;
}
.note-author-name {
  font-size: 0.7rem;
  color: var(--xhs-text-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 76px;
}
.note-like {
  font-size: 0.7rem;
  color: var(--xhs-text-3);
  white-space: nowrap;
  flex-shrink: 0;
}

/* 骨架屏 */
.skeleton-note {
  animation: xhs-pulse 1.4s infinite;
}
.skeleton-cover {
  width: 100%;
  background: #f0f1f3;
}
.skeleton-body {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.skeleton-line {
  height: 9px;
  border-radius: 5px;
  background: #f0f1f3;
}
.skeleton-line.long { width: 92%; }
.skeleton-line.mid { width: 55%; }

/* 分页 */
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 16px 0 6px;
}
.pager-btn {
  border: 1px solid var(--xhs-line);
  background: #fff;
  color: var(--xhs-text);
  font-size: 0.8rem;
  font-weight: 600;
  padding: 6px 15px;
  border-radius: var(--xhs-radius-pill);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.pager-btn:hover:not(:disabled) {
  background: #fafafa;
  border-color: #e6e6e9;
}
.pager-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.pager-info {
  font-size: 0.8rem;
  color: var(--xhs-text-3);
  font-weight: 600;
  min-width: 52px;
  text-align: center;
}
.feed-hint {
  margin-top: 8px;
  font-size: 0.68rem;
  color: var(--xhs-text-3);
  text-align: center;
  padding-bottom: 8px;
}

/* 个人主页弹窗 */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}
.modal-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 22px;
  max-height: 82vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}
.profile-cover {
  height: 92px;
  background: linear-gradient(135deg, #ffd9e1, #ffeef2 60%, #fff);
}
.modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 3;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.28);
  color: #fff;
  border: none;
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.profile-modal-head {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  padding: 0 22px 16px;
  margin-top: -30px;
}
.modal-avatar-big {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 3px #fff, 0 4px 14px rgba(0, 0, 0, 0.12);
  font-size: 2.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}
.profile-modal-meta {
  padding-bottom: 4px;
}
.modal-nickname {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 800;
}
.modal-handle {
  margin: 3px 0 0;
  color: var(--xhs-text-3);
  font-size: 0.82rem;
}
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 4px 22px 22px;
}
.modal-tab-title {
  font-size: 0.92rem;
  font-weight: 800;
  margin: 6px 0 12px;
  color: var(--xhs-text);
}
.modal-note {
  padding: 12px 0;
  border-bottom: 1px solid var(--xhs-line);
  text-align: left;
}
.modal-note-img {
  width: 100%;
  max-height: 220px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 8px;
  display: block;
}
.modal-note-time {
  font-size: 0.72rem;
  color: var(--xhs-text-3);
  margin-bottom: 5px;
}
.modal-note-content {
  font-size: 0.92rem;
  line-height: 1.55;
  word-wrap: break-word;
  color: var(--xhs-text);
}
</style>
