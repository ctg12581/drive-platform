<!-- src/views/HomeView.vue -->
<template>
  <div class="feed-container">
    <!-- 顶部三分流切换（热点 / 榜单 / 关注） -->
    <div class="feed-header-tabs">
      <button @click="changeTab('hot')" :class="['feed-tab-btn', { active: currentSubTab === 'hot' }]">
        <span class="tab-text">热点</span>
      </button>
      <button @click="changeTab('rank')" :class="['feed-tab-btn', { active: currentSubTab === 'rank' }]">
        <span class="tab-text">榜单</span>
      </button>
      <button @click="changeTab('following')" :class="['feed-tab-btn', { active: currentSubTab === 'following' }]">
        <span class="tab-text">关注</span>
      </button>
    </div>

    <!-- 💡 X 风格：有新动态时自上方优雅滑出的蓝色气泡（仅关注流） -->
    <div v-if="currentSubTab === 'following' && newPostsCount > 0" class="new-posts-banner" @click="applyNewPosts">
      显示 {{ newPostsCount }} 条新动态
    </div>

    <!-- ============ 热点：热点新闻 ============ -->
    <section v-if="currentSubTab === 'hot'" class="hot-news-section">
      <div class="hot-news-header">
        <div class="hot-news-title">
          <span class="hot-news-flame">🔥</span>
          <span>热点新闻</span>
        </div>
        <button class="hot-news-refresh" @click="refreshList('hot')" :disabled="hotLoading">
          {{ hotLoading ? '刷新中…' : '换一批' }}
        </button>
      </div>

      <div v-if="hotLoading && hotItems.length === 0" class="hot-news-loading">
        正在加载热点新闻…
      </div>
      <ul v-else-if="hotItems.length" class="hot-news-list">
        <li
          v-for="(n, idx) in hotItems"
          :key="n.id"
          class="hot-news-item"
          title="在新标签页打开原文"
          @click="openSource(n)"
        >
          <span class="hot-news-rank" :class="'hot-rank-' + (idx + 1)">{{ idx + 1 }}</span>
          <div class="hot-news-body">
            <div class="hot-news-item-title">{{ n.title }}</div>
            <div class="hot-news-meta">
              <span class="hot-news-cat" :style="catStyle(n.category)">{{ n.category }}</span>
              <span class="hot-news-source">
                <span class="hot-news-src-icon">{{ sourceIcon(n.source) }}</span>{{ n.source }}
              </span>
            </div>
          </div>
          <span class="hot-news-jump">↗</span>
        </li>
      </ul>
      <div v-else class="hot-news-empty">暂无热点，稍后再来看看~</div>
    </section>

    <!-- ============ 榜单：多源热榜总榜 ============ -->
    <section v-else-if="currentSubTab === 'rank'" class="hot-news-section">
      <div class="hot-news-header">
        <div class="hot-news-title">
          <span class="hot-news-flame">🏆</span>
          <span>热榜总榜</span>
        </div>
        <button class="hot-news-refresh" @click="refreshList('rank')" :disabled="rankLoading">
          {{ rankLoading ? '刷新中…' : '换一批' }}
        </button>
      </div>

      <div v-if="rankLoading && rankItems.length === 0" class="hot-news-loading">
        正在加载热榜…
      </div>
      <ul v-else-if="rankItems.length" class="hot-news-list">
        <li
          v-for="(n, idx) in rankItems"
          :key="n.id"
          class="hot-news-item"
          title="在新标签页打开原文"
          @click="openSource(n)"
        >
          <span class="hot-news-rank" :class="'hot-rank-' + (idx + 1)">{{ idx + 1 }}</span>
          <div class="hot-news-body">
            <div class="hot-news-item-title">{{ n.title }}</div>
            <div class="hot-news-meta">
              <span class="hot-news-source">
                <span class="hot-news-src-icon">{{ sourceIcon(n.source) }}</span>{{ n.source }}
              </span>
              <span v-if="n.hot" class="hot-news-hot">🔥 {{ formatHot(n.hot) }}</span>
            </div>
          </div>
          <span class="hot-news-jump">↗</span>
        </li>
      </ul>
      <div v-else class="hot-news-empty">暂无榜单数据，稍后再来看看~</div>
    </section>

    <!-- ============ 关注：好友动态流 ============ -->
    <template v-else>
      <!-- 骨架屏占位（仅在没有任何历史缓存时展示） -->
      <div v-if="loading && posts.length === 0" class="skeleton-container">
        <div v-for="i in 3" :key="i" class="skeleton-card">
          <div class="skeleton-avatar"></div>
          <div class="skeleton-info">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line long"></div>
            <div class="skeleton-line mid"></div>
          </div>
        </div>
      </div>

      <!-- 动态时间线主体 -->
      <div v-else class="timeline">
        <div v-if="posts.length === 0" class="no-posts-hint">
          👋 还没有任何动态。<br/>关注一些新朋友，他们的动态会出现在这里。
        </div>

        <div v-for="post in posts" :key="post.id" class="tweet-card">
          <!-- 头像区域（点击打开个人主页） -->
          <div class="tweet-avatar" @click="openUserProfile(post.username)">
            <img v-if="isUrl(post.avatar)" :src="post.avatar" class="avatar-img-el" />
            <span v-else-if="post.avatar && post.avatar !== '👤'">{{ post.avatar }}</span>
            <span v-else>{{ post.username[0].toUpperCase() }}</span>
          </div>

          <!-- 内容区域 -->
          <div class="tweet-main">
            <div class="tweet-header">
              <span class="tweet-author" @click="openUserProfile(post.username)">{{ post.nickname }}</span>
              <span class="tweet-handle">@{{ post.username }} · {{ formatLocalTime(post.time) }}</span>
            </div>
            <div class="tweet-content">{{ post.content }}</div>
          </div>
        </div>
      </div>
    </template>

    <!-- 🌟 个人主页弹窗 (Profile Modal) -->
    <div v-if="activeProfile" class="modal-backdrop" @click.self="activeProfile = null">
      <div class="modal-card">
        <button class="modal-close" @click="activeProfile = null">✕</button>
        
        <div class="modal-header">
          <div class="modal-avatar-big">
            <img v-if="isUrl(activeProfile.user.avatar)" :src="activeProfile.user.avatar" class="avatar-img-el" />
            <span v-else-if="activeProfile.user.avatar && activeProfile.user.avatar !== '👤'">{{ activeProfile.user.avatar }}</span>
            <span v-else>{{ activeProfile.user.username[0].toUpperCase() }}</span>
          </div>
          <h2 class="modal-nickname">{{ activeProfile.user.nickname }}</h2>
          <p class="modal-handle">@{{ activeProfile.user.username }}</p>
        </div>

        <div class="modal-body">
          <h3 class="modal-tab-title">TA 的动态 ({{ activeProfile.posts.length }})</h3>
          <div v-if="activeProfile.posts.length === 0" class="no-posts-hint-modal">TA 还没有发布过任何动态。</div>
          <div v-for="p in activeProfile.posts" :key="p.id" class="modal-tweet">
            <div class="modal-tweet-time">{{ formatLocalTime(p.time) }}</div>
            <div class="modal-tweet-content">{{ p.content }}</div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { isUrl } from '@drive/shared'
import { useAuthStore } from '../store/auth'
import { useMomentsStore } from '../store/home'
import { useChatStore } from '../store/chat'
import { formatLocalTime } from '../utils/date'
import { apiFetch } from '../utils/api'

const authStore = useAuthStore()
const momentsStore = useMomentsStore()
const chatStore = useChatStore()

const currentSubTab = ref('hot') // 'hot' 热点, 'rank' 榜单, 'following' 关注
const posts = ref(momentsStore.cachedPosts) // 读取 Pinia 物理缓存，实现 0ms 瞬间还原
const loading = ref(posts.value.length === 0)
const activeProfile = ref(null)

// 热点 / 榜单两个列表的状态（结构对称，用 listState 统一处理）
const NEWS_PAGE_SIZE = 8
const hotPool = ref([])
const hotItems = ref([])
const hotLoading = ref(false)
const hotOffset = ref(0)

const rankPool = ref([])
const rankItems = ref([])
const rankLoading = ref(false)
const rankOffset = ref(0)

// 分类配色（用于标签小圆角）
const CAT_COLORS = {
  科技: { color: '#1d9bf0', backgroundColor: '#e8f5fe' },
  财经: { color: '#d97706', backgroundColor: '#fef3c7' },
  体育: { color: '#16a34a', backgroundColor: '#dcfce7' },
  娱乐: { color: '#db2777', backgroundColor: '#fce7f3' },
  社会: { color: '#7c3aed', backgroundColor: '#ede9fe' },
  国际: { color: '#0d9488', backgroundColor: '#ccfbf1' },
  健康: { color: '#ef4444', backgroundColor: '#fee2e2' },
  教育: { color: '#2563eb', backgroundColor: '#dbeafe' },
  热点: { color: '#ff6a2b', backgroundColor: '#fff1e7' },
}
const catStyle = (category) => CAT_COLORS[category] || { color: '#536471', backgroundColor: '#eff3f4' }

// 来源小图标（emoji，避免依赖外部 favicon 服务）
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

// 热度格式化：超过一万显示为 x.x万
const formatHot = (value) => {
  const num = Number(value) || 0
  return num >= 10000 ? `${(num / 10000).toFixed(1)}万` : `${num}`
}

// 按当前标签页取对应的列表状态
const listState = (kind) => (kind === 'rank'
  ? { pool: rankPool, items: rankItems, loading: rankLoading, offset: rankOffset }
  : { pool: hotPool, items: hotItems, loading: hotLoading, offset: hotOffset })

const pickFromPool = (pool, offset) => {
  if (pool.length === 0) return []
  const size = Math.min(NEWS_PAGE_SIZE, pool.length)
  const result = []
  for (let i = 0; i < size; i++) {
    result.push(pool[(offset + i) % pool.length])
  }
  return result
}

// kind: 'hot' -> 后端 kind=news；'rank' -> 后端 kind=rank
const fetchList = async (kind) => {
  const st = listState(kind)
  st.loading.value = true
  try {
    const apiKind = kind === 'rank' ? 'rank' : 'news'
    const res = await apiFetch(`/news/hot?limit=50&kind=${apiKind}`)
    const data = await res.json()
    if (res.ok && data.success) {
      st.pool.value = data.news || []
      st.offset.value = 0
      st.items.value = pickFromPool(st.pool.value, 0)
    }
  } catch (err) {
    console.error('获取列表异常:', err)
  } finally {
    st.loading.value = false
  }
}

// 「换一批」：先拉取服务端最新快照，再按池子轮换展示下一组
const refreshList = async (kind) => {
  const st = listState(kind)
  if (st.pool.value.length <= NEWS_PAGE_SIZE) {
    await fetchList(kind)
    return
  }
  st.offset.value = (st.offset.value + NEWS_PAGE_SIZE) % st.pool.value.length
  st.items.value = pickFromPool(st.pool.value, st.offset.value)
}

const openSource = (item) => {
  if (!item || !item.url) return
  window.open(item.url, '_blank', 'noopener,noreferrer')
}

// 💡 实时动态探针变量
const newPostsCount = ref(0)
let lastFetchedTime = "" 
let checkInterval = null

onMounted(() => {
  fetchList('hot')

  // 新动态优先走 WebSocket 推送；下面的轮询仅作“断线/推送不可用”时的低频兜底
  window.addEventListener('moments:new', onNewMoments)
  checkInterval = setInterval(checkNewPosts, 60000)
})

onUnmounted(() => {
  if (checkInterval) clearInterval(checkInterval)
  window.removeEventListener('moments:new', onNewMoments)
})

// 全局发帖成功后由 App.vue 触发刷新，无需整页 reload
watch(() => momentsStore.refreshTick, () => fetchTimeline(true))

// 加载关注流时间线数据
const fetchTimeline = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const res = await apiFetch('/moments/following')
    const data = await res.json()
    if (res.ok) {
      posts.value = data.moments
      
      // 更新最新时间戳和 Pinia 缓存
      if (data.moments.length > 0) {
        lastFetchedTime = data.moments[0].time
        momentsStore.setPosts(data.moments)
      } else {
        lastFetchedTime = new Date().toISOString()
      }
      newPostsCount.value = 0 // 清空漂浮气泡
    }
  } catch (err) {
    console.error('获取时间线异常:', err)
  } finally {
    loading.value = false
  }
}

// 切换「热点 / 榜单 / 关注」
const changeTab = (tab) => {
  if (currentSubTab.value === tab) return
  currentSubTab.value = tab
  if (tab === 'following') {
    posts.value = []
    fetchTimeline()
  } else if (tab === 'hot' && hotPool.value.length === 0) {
    fetchList('hot')
  } else if (tab === 'rank' && rankPool.value.length === 0) {
    fetchList('rank')
  }
}

// 收到服务端“有新动态”推送时更新气泡（替代 15s 轮询）
const onNewMoments = (event) => {
  newPostsCount.value += Number(event && event.detail) || 1
}

// 💡 后台静默检测新发布的帖子数量（仅作断线兜底）
const checkNewPosts = async () => {
  if (!lastFetchedTime) return
  // 页面不可见时跳过轮询，减少后台请求
  if (typeof document !== 'undefined' && document.hidden) return
  // WS 连接正常时由服务端推送，不再轮询
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

// 用户点击提示泡：自动拉取最新动态并滑回顶部
const applyNewPosts = () => {
  fetchTimeline()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 获取他人主页名片卡和TA的帖子
const openUserProfile = async (targetUsername) => {
  try {
    const [profileRes, postsRes] = await Promise.all([
      apiFetch(`/auth/profile/${targetUsername}`),
      apiFetch(`/moments/user/${targetUsername}`)
    ])
    if (profileRes.ok && postsRes.ok) {
      const user = await profileRes.json()
      const userPosts = await postsRes.json()
      activeProfile.value = {
        user: user,
        posts: userPosts.moments
      }
    }
  } catch {
    alert('无法加载该用户的主页')
  }
}
</script>

<style scoped>
.feed-container {
  width: 100%;
  position: relative;
}

/* 𝕏 经典版：顶端常驻“推荐 vs 关注”选项卡 */
.feed-header-tabs {
  display: flex;
  border-bottom: 1px solid var(--x-border);
  position: sticky;
  top: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  z-index: 10;
}
.feed-tab-btn {
  flex: 1;
  height: 53px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.feed-tab-btn:hover {
  background: var(--x-bg-hover);
}
.tab-text {
  font-size: 0.95rem;
  font-weight: bold;
  color: var(--x-text-gray);
  height: 100%;
  display: flex;
  align-items: center;
  box-sizing: border-box;
}
.feed-tab-btn.active .tab-text {
  color: var(--x-text-main);
  border-bottom: 4px solid var(--x-blue); /* 💡 𝕏 标志蓝底线条 */
}

/* 💡 自顶部滑出的炫酷蓝色新推文提示泡 */
.new-posts-banner {
  background: var(--x-blue);
  color: white;
  font-weight: bold;
  text-align: center;
  padding: 8px 16px;
  border-radius: 9999px;
  width: fit-content;
  margin: 12px auto;
  cursor: pointer;
  font-size: 0.85rem;
  box-shadow: 0 4px 12px rgba(29, 155, 240, 0.3);
  position: absolute;
  left: 0; right: 0;
  z-index: 15;
  animation: slide-down 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes slide-down {
  0% { transform: translateY(-20px); opacity: 0; }
  100% { transform: translateY(0); opacity: 1; }
}

/* 骨架屏占位 */
@keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
.skeleton-container { display: flex; flex-direction: column; }
.skeleton-card { display: flex; gap: 12px; padding: 16px; border-bottom: 1px solid var(--x-border); animation: pulse 1.5s infinite; }
.skeleton-avatar { width: 40px; height: 40px; border-radius: 50%; background: #eff3f4; }
.skeleton-info { flex: 1; display: flex; flex-direction: column; gap: 8px; justify-content: center; }
.skeleton-line { height: 11px; background: #eff3f4; border-radius: 4px; }
.skeleton-line.short { width: 25%; }
.skeleton-line.mid { width: 45%; }
.skeleton-line.long { width: 85%; }

/* 动态列表列表 */
.tweet-card {
  display: flex;
  padding: 16px;
  border-bottom: 1px solid var(--x-border);
  gap: 12px;
}
.tweet-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ffffff;
  border: 1px solid var(--x-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  cursor: pointer;
  overflow: hidden;
}
.avatar-img-el {
  width: 100%; height: 100%; object-fit: cover; border-radius: 50%;
}
.tweet-main {
  flex: 1;
  text-align: left;
}
.tweet-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.tweet-author {
  font-weight: bold;
  font-size: 0.95rem;
  cursor: pointer;
  color: var(--x-text-main);
}
.tweet-author:hover {
  text-decoration: underline;
}
.tweet-handle {
  color: var(--x-text-gray);
  font-size: 0.85rem;
}
.tweet-content {
  font-size: 0.95rem;
  line-height: 1.5;
  word-wrap: break-word;
  color: var(--x-text-main);
}
.no-posts-hint {
  text-align: center;
  padding: 60px 40px;
  color: var(--x-text-gray);
  font-size: 0.95rem;
  line-height: 1.6;
}

/* 🌟 个人主页弹窗样式 */
.modal-backdrop {
  position: fixed; top: 0; bottom: 0; left: 0; right: 0;
  background: rgba(0, 0, 0, 0.4); display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-card {
  width: 90%; max-width: 450px; background: white; border-radius: 20px;
  max-height: 80vh; display: flex; flex-direction: column; overflow: hidden; position: relative;
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}
.modal-close {
  position: absolute; top: 16px; right: 16px; background: transparent; border: none; font-size: 1.25rem; font-weight: bold; cursor: pointer; color: var(--x-text-gray);
}
.modal-header { padding: 30px 24px 16px 24px; text-align: center; border-bottom: 1px solid var(--x-border); }
.modal-avatar-big {
  width: 70px; height: 70px; background: #ffffff; border: 1px solid var(--x-border); border-radius: 50%; font-size: 2.5rem; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px auto; overflow: hidden;
}
.modal-nickname { margin: 0; font-size: 1.25rem; font-weight: 800; }
.modal-handle { margin: 4px 0 0 0; color: var(--x-text-gray); font-size: 0.9rem; }

.modal-body { flex: 1; overflow-y: auto; padding: 16px 24px; }
.modal-tab-title { font-size: 1rem; font-weight: 800; border-bottom: 2px solid var(--x-blue); padding-bottom: 6px; margin: 0 0 12px 0; display: inline-block;}
.no-posts-hint-modal { text-align: center; color: var(--x-text-gray); font-size: 0.9rem; padding: 24px 0; }
.modal-tweet { padding: 12px 0; border-bottom: 1px solid var(--x-border); text-align: left; }
.modal-tweet-time { font-size: 0.8rem; color: var(--x-text-gray); margin-bottom: 4px; }
.modal-tweet-content { font-size: 0.95rem; line-height: 1.4; word-wrap: break-word;}

/* 🔥 热点新闻模块 */
.hot-news-section {
  margin: 12px 12px 4px;
  padding: 12px 14px;
  background: linear-gradient(180deg, #fff8f2 0%, #ffffff 70%);
  border: 1px solid #ffe3d1;
  border-radius: 16px;
  box-shadow: 0 2px 10px rgba(255, 138, 0, 0.06);
}
.hot-news-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.hot-news-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 1rem;
  font-weight: 800;
  color: var(--x-text-main);
}
.hot-news-flame { font-size: 1.05rem; }
.hot-news-live {
  font-size: 0.66rem;
  font-weight: 700;
  color: #fff;
  background: #ff5c39;
  padding: 1px 6px;
  border-radius: 9999px;
  letter-spacing: 0.5px;
}
.hot-news-refresh {
  background: transparent;
  border: 1px solid #ffd0b3;
  color: #ff6a2b;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 9999px;
  cursor: pointer;
  transition: background 0.15s;
}
.hot-news-refresh:hover:not(:disabled) { background: #fff1e7; }
.hot-news-refresh:disabled { opacity: 0.6; cursor: default; }
.hot-news-loading,
.hot-news-empty {
  text-align: center;
  color: var(--x-text-gray);
  font-size: 0.85rem;
  padding: 18px 0;
}
.hot-news-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.hot-news-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 9px 4px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}
.hot-news-item:hover { background: #fff4ee; }
.hot-news-item + .hot-news-item { border-top: 1px solid #fdeee4; }
.hot-news-rank {
  flex: none;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: #f0f1f3;
  color: var(--x-text-gray);
  font-size: 0.78rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1px;
}
.hot-news-rank.hot-rank-1 { background: #ff5c39; color: #fff; }
.hot-news-rank.hot-rank-2 { background: #ff8a4c; color: #fff; }
.hot-news-rank.hot-rank-3 { background: #ffb020; color: #fff; }
.hot-news-body { flex: 1; min-width: 0; }
.hot-news-item-title {
  font-size: 0.92rem;
  font-weight: 600;
  line-height: 1.4;
  color: var(--x-text-main);
  word-break: break-word;
}
.hot-news-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 0.72rem;
  color: var(--x-text-gray);
}
.hot-news-cat {
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 9999px;
  font-size: 0.68rem;
  line-height: 1.5;
}
.hot-news-source { color: var(--x-text-gray); }
.hot-news-src-icon { margin-right: 3px; font-size: 0.8rem; }
.hot-news-hot { color: #ff6a2b; font-weight: 600; }
.hot-news-jump {
  flex: none;
  align-self: center;
  color: var(--x-text-gray);
  opacity: 0.4;
  font-size: 0.9rem;
  transition: opacity 0.15s, transform 0.15s;
}
.hot-news-item:hover .hot-news-jump { opacity: 1; transform: translate(1px, -1px); }

/* 热点详情弹窗 */
.news-modal-card { max-width: 480px !important; }
.news-modal-body { padding: 26px 22px 22px; text-align: left; max-height: 74vh; overflow-y: auto; }
.news-modal-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.75rem;
  color: var(--x-text-gray);
  margin-bottom: 12px;
}
.news-modal-time { color: var(--x-text-gray); }
.news-modal-title {
  margin: 0 0 14px 0;
  font-size: 1.2rem;
  font-weight: 800;
  line-height: 1.45;
  color: var(--x-text-main);
}
.news-modal-summary {
  margin: 0 0 20px 0;
  font-size: 0.95rem;
  line-height: 1.75;
  color: #333;
}
.news-modal-link {
  display: inline-block;
  color: var(--x-blue);
  font-weight: 700;
  font-size: 0.9rem;
  text-decoration: none;
}
.news-modal-link:hover { text-decoration: underline; }
</style>