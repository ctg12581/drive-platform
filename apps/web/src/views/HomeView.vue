<!-- src/views/HomeView.vue -->
<template>
  <div class="feed-container">
    <!-- 𝕏 经典双分流顶部切换卡 (推荐 vs 关注) -->
    <div class="feed-header-tabs">
      <button @click="changeTab('recommended')" :class="['feed-tab-btn', { active: currentSubTab === 'recommended' }]">
        <span class="tab-text">推荐</span>
      </button>
      <button @click="changeTab('following')" :class="['feed-tab-btn', { active: currentSubTab === 'following' }]">
        <span class="tab-text">关注</span>
      </button>
    </div>

    <!-- 💡 X 风格：有新动态时自上方优雅滑出的蓝色气泡 -->
    <div v-if="newPostsCount > 0" class="new-posts-banner" @click="applyNewPosts">
      显示 {{ newPostsCount }} 条新动态
    </div>

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
        👋 还没有任何动态。
        <span v-if="currentSubTab === 'following'"><br/>关注一些新朋友，或者点击上方“推荐”发现新鲜事吧！</span>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../store/auth'
import { useMomentsStore } from '../store/home'
import { formatLocalTime } from '../utils/date'
import { apiFetch } from '../utils/api'

const authStore = useAuthStore()
const momentsStore = useMomentsStore()

const currentSubTab = ref('recommended') // 'recommended' 推荐, 'following' 关注
const posts = ref(momentsStore.cachedPosts) // 读取 Pinia 物理缓存，实现 0ms 瞬间还原
const loading = ref(posts.value.length === 0)
const activeProfile = ref(null)

// 💡 实时动态探针变量
const newPostsCount = ref(0)
let lastFetchedTime = "" 
let checkInterval = null

onMounted(() => {
  fetchTimeline()
  
  // 💡 每 15 秒静默检测一次是否有新推文，不打扰用户当前浏览
  checkInterval = setInterval(checkNewPosts, 15000)
})

onUnmounted(() => {
  if (checkInterval) clearInterval(checkInterval)
})

// 加载时间线数据
const fetchTimeline = async (silent = false) => {
  if (!silent) loading.value = true
  const endpoint = currentSubTab.value === 'recommended' ? '/moments' : '/moments/following'
  try {
    const res = await apiFetch(endpoint)
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

// 切换“推荐”和“关注”选项卡
const changeTab = (tab) => {
  if (currentSubTab.value === tab) return
  currentSubTab.value = tab
  posts.value = []
  fetchTimeline()
}

// 💡 后台静默检测新发布的帖子数量
const checkNewPosts = async () => {
  if (!lastFetchedTime) return
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

const isUrl = (text) => {
  if (!text) return false
  return text.startsWith('http://') || text.startsWith('https://') || text.startsWith('/')
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
</style>