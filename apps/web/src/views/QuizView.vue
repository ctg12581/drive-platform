<!-- src/views/QuizView.vue (全量覆盖无错版) -->
<template>
  <div class="quiz-container">
    <!-- 顶端吸顶标题栏 -->
    <div class="quiz-header">
      <h2 style="margin: 0; font-size: 1.25rem; font-weight: 800; color: #db2777;">💖 默契挑战中心</h2>
    </div>

    <!-- 1. 我的出题卡片区 (💡 引入 SWR，实现 0ms 瞬间无闪烁渲染) -->
    <div class="quiz-owner-section">
      <div v-if="!myQuiz" class="owner-card no-quiz">
        <div style="font-size: 2.2rem; margin-bottom: 8px;">💌</div>
        <h4>您尚未配置您的专属默契测验</h4>
        <p style="font-size: 0.8rem; color: #f43f5e; margin: 4px 0 16px 0;">配置后，其他好友点击您的头像即可在线测试与您的灵犀契合度！</p>
        <button @click="router.push('/quiz/design')" class="x-btn-pill-pink">立即出题配对</button>
      </div>

      <div v-else class="owner-card has-quiz">
        <div class="has-quiz-left">
          <div class="heart-avatar">💘</div>
          <div class="quiz-meta-info">
            <h4 style="margin: 0; font-size: 1rem; color: #db2777;">{{ myQuiz.title }}</h4>
            <p style="margin: 4px 0 0 0; font-size: 0.8rem; color: var(--x-text-gray);">已发布 · 恋爱默契挑战名片已上线</p>
          </div>
        </div>
        <button @click="router.push('/quiz/design')" class="x-btn-pill-light">修改答案/重新出题</button>
      </div>
    </div>

    <!-- 2. 互粉好友的挑战时间轴大厅 (💡 0ms 秒开) -->
    <div class="quiz-friends-section">
      <h3 class="section-title">好友的默契考验 ({{ friendQuizzes.length }})</h3>
      
      <div v-if="friendQuizzes.length === 0" class="no-quizzes">
        👋 暂无任何互粉好友发布默契测验。<br/>
        <span style="font-size: 0.8rem; opacity: 0.8;">去【搜索】添加或在【通知】里同意好友请求吧！</span>
      </div>

      <div v-else-if="friendQuizzes.length > 0" class="friend-quiz-list-box">
        <div v-for="q in friendQuizzes" :key="q.quiz_id" class="friend-quiz-card">
          <div class="friend-card-left">
            <div class="friend-avatar">
              <img v-if="isUrl(q.avatar)" :src="q.avatar" class="avatar-img" />
              <span v-else>{{ q.avatar }}</span>
            </div>
            <div class="friend-info">
              <div class="friend-name-row">
                <span class="friend-nickname">{{ q.nickname }}</span>
                <span class="friend-handle">@{{ q.username }}</span>
              </div>
              <div class="friend-quiz-title">{{ q.title }}</div>
            </div>
          </div>
          
          <div class="friend-card-right">
            <button v-if="!q.already_challenged" @click="startChallenge(q)" class="x-btn-pill-pink btn-sm">
              开始挑战
            </button>
            <button v-else @click="startChallenge(q)" class="x-btn-pill-light btn-sm" style="color: #ff5c5c; border-color: #ffd8d8; background: #fff5f5;">
              灵犀值: {{ q.score }}% (重测)
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 💡 弹出模态：挑战好友答题弹窗 -->
    <div v-if="showChallengeModal" class="modal-backdrop" @click.self="showChallengeModal = false">
      <div class="modal-card" style="max-width: 480px; max-height: 85vh; padding: 20px; text-align: left;">
        <button class="modal-close" @click="showChallengeModal = false">✕</button>
        <h3 style="margin-top: 0; font-size: 1.2rem; font-weight: 800; text-align: center; color: #db2777;">💘 {{ activeChallengeQuiz.title }}</h3>
        <p style="font-size: 0.8rem; color: var(--x-text-gray); text-align: center; margin-bottom: 20px;">答题完毕后点击提交，由服务器计算你们的灵魂契合度！</p>
        
        <div class="modal-body" style="flex: 1; overflow-y: auto;">
          <div v-for="(q, idx) in activeChallengeQuiz.questions" :key="q.id" class="quiz-setup-item" style="margin-bottom: 20px; border-bottom: 1px solid var(--x-border); padding-bottom: 12px;">
            <p class="quiz-q-title">Q{{ idx + 1 }}. {{ q.text }}</p>
            <div style="display: flex; flex-direction: column; gap: 6px;">
              <label v-for="opt in q.options" :key="opt" class="opt-label">
                <input type="radio" :name="'challenge_q_' + q.id" :value="opt[0]" v-model="challengeAnswers[q.id]" style="width: auto;">
                {{ opt }}
              </label>
            </div>
          </div>
          <button @click="submitChallenge" class="x-btn-dark-pink">提交我的答题卡</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { useQuizStore } from '../store/quiz'  // 💡 导入新状态缓存库
import { formatLocalTime } from '../utils/date'
import { apiFetch } from '../utils/api'

const router = useRouter()
const authStore = useAuthStore()
const quizStore = useQuizStore() // 激活状态

// 💡 核心修改：出题状态和好友列表，直接绑定全局缓存！进入时 0ms 瞬间还原！
const myQuiz = ref(quizStore.cachedMyQuiz)
const friendQuizzes = ref(quizStore.cachedFriendQuizzes)

const showChallengeModal = ref(false)
const activeChallengeQuiz = ref(null)
const challengeAnswers = reactive({})

onMounted(() => {
  fetchMyQuizStatus()
  fetchFriendsQuizzes()
})

const fetchMyQuizStatus = async () => {
  try {
    const res = await apiFetch(`/quiz/user/${authStore.username}`)
    const data = await res.json()
    if (res.ok && data.has_quiz) {
      myQuiz.value = data
      quizStore.setMyQuiz(data) // 写入缓存银行
    } else {
      myQuiz.value = null
      quizStore.setMyQuiz(null)
    }
  } catch {
    console.error('获取我的测验异常')
  }
}

const fetchFriendsQuizzes = async () => {
  try {
    const res = await apiFetch('/quiz/friends-list')
    const data = await res.json()
    if (res.ok) {
      friendQuizzes.value = data.quizzes
      quizStore.setFriendQuizzes(data.quizzes) // 写入缓存银行
    }
  } catch {
    console.error('拉取好友挑战列表失败')
  }
}

const startChallenge = async (quizInfo) => {
  try {
    const res = await apiFetch(`/quiz/user/${quizInfo.username}`)
    const data = await res.json()
    if (res.ok && data.has_quiz) {
      activeChallengeQuiz.value = data
      data.questions.forEach(q => {
        challengeAnswers[q.id] = null // 强制不默认选中
      })
      showChallengeModal.value = true
    }
  } catch {
    alert('加载答题卡失败')
  }
}

const submitChallenge = async () => {
  const totalQuestions = activeChallengeQuiz.value.questions.length
  const answeredCount = Object.keys(challengeAnswers).filter(
    qId => challengeAnswers[qId] !== null && challengeAnswers[qId] !== undefined
  ).length

  if (answeredCount < totalQuestions) {
    alert(`💡 请先答完所有问题再提交！\n当前进度: ${answeredCount}/${totalQuestions}`)
    return
  }

  const payload = {
    quiz_id: activeChallengeQuiz.value.quiz_id,
    answers: challengeAnswers
  }
  try {
    const res = await apiFetch('/quiz/submit', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (res.ok) {
      showChallengeModal.value = false
      fetchFriendsQuizzes() 
      alert(`🎉 答题成功！你们的默契度高达: ${data.score}%！\n答对题数: ${data.correct_count}/${data.total_questions}`)
    }
  } catch {
    alert('提交答题卡失败')
  }
}

const isUrl = (text) => {
  if (!text) return false
  return text.startsWith('http://') || text.startsWith('https://') || text.startsWith('/')
}
</script>

<style scoped>
/* 保持您原有完美的 CSS 样式不变 */
.quiz-container { width: 100%; position: relative; }
.quiz-header { position: sticky; top: 0; background: rgba(255,255,255,0.85); backdrop-filter: blur(12px); border-bottom: 1px solid var(--x-border); padding: 16px; z-index: 10; text-align: left; }
.quiz-owner-section { padding: 16px; border-bottom: 1px solid var(--x-border); }
.owner-card { border-radius: 16px; padding: 20px; text-align: center; box-sizing: border-box; }
.owner-card.no-quiz { background: #fff5f5; border: 1px dashed #fda4af; }
.owner-card.has-quiz { background: #ffffff; border: 1px solid var(--x-border); display: flex; flex-direction: column; align-items: center; justify-content: space-between; gap: 12px; }
@media (min-width: 500px) { .owner-card.has-quiz { flex-direction: row; text-align: left; } }
.has-quiz-left { display: flex; align-items: center; gap: 12px; }
.heart-avatar { width: 44px; height: 44px; background: #fff5f5; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
.quiz-meta-info { display: flex; flex-direction: column; text-align: left; }
.x-btn-pill-pink { background: #db2777; color: white; border: none; font-weight: bold; font-size: 0.85rem; padding: 0 16px; height: 34px; border-radius: 9999px; cursor: pointer; transition: background 0.15s; }
.x-btn-pill-pink:hover { background: #be185d; }
.x-btn-pill-light { background: transparent; color: var(--x-text-main); border: 1px solid var(--x-border); font-weight: bold; font-size: 0.85rem; padding: 0 16px; height: 34px; border-radius: 9999px; cursor: pointer; transition: background 0.15s; }
.x-btn-pill-light:hover { background: var(--x-bg-hover); }
.quiz-friends-section { width: 100%; }
.section-title { font-size: 1.1rem; font-weight: 800; padding: 16px 16px 8px 16px; margin: 0; text-align: left; }
.no-quizzes { text-align: center; color: var(--x-text-gray); font-size: 0.95rem; padding: 60px 20px; line-height: 1.6; }
.friend-quiz-card { display: flex; align-items: center; justify-content: space-between; padding: 16px; border-bottom: 1px solid var(--x-border); gap: 12px; }
.friend-card-left { display: flex; align-items: center; gap: 12px; text-align: left; overflow: hidden; }
.friend-avatar { width: 40px; height: 40px; background: #ffffff; border: 1px solid var(--x-border); border-radius: 50%; font-size: 1.5rem; display: flex; align-items: center; justify-content: center; overflow: hidden; flex-shrink: 0; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.friend-info { display: flex; flex-direction: column; overflow: hidden; }
.friend-name-row { display: flex; align-items: center; gap: 6px; }
.friend-nickname { font-weight: bold; font-size: 0.95rem; color: var(--x-text-main); }
.friend-handle { font-size: 0.85rem; color: var(--x-text-gray); }
.friend-quiz-title { font-size: 0.85rem; color: #db2777; font-weight: bold; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.friend-card-right { display: flex; align-items: center; }
.modal-backdrop { position: fixed; top: 0; bottom: 0; left: 0; right: 0; background: rgba(0, 0, 0, 0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { width: 90%; max-width: 450px; background: white; border-radius: 20px; max-height: 80vh; display: flex; flex-direction: column; overflow: hidden; position: relative; box-shadow: 0 8px 30px rgba(0,0,0,0.15); }
.modal-close { position: absolute; top: 16px; right: 16px; background: transparent; border: none; font-size: 1.25rem; font-weight: bold; cursor: pointer; color: var(--x-text-gray); }
.modal-body { flex: 1; overflow-y: auto; padding: 16px 24px; }
.quiz-setup-item { text-align: left; }
.quiz-q-title { font-weight: bold; font-size: 0.95rem; margin: 0 0 10px 0; color: var(--x-text-main); }
.options-group { display: flex; flex-direction: column; gap: 6px; }
.opt-label { font-size: 0.85rem; display: flex; align-items: center; gap: 8px; cursor: pointer; color: var(--x-text-main); }
.x-btn-dark-pink { width: 100%; height: 44px; background: #db2777; color: white; border: none; border-radius: 9999px; font-weight: bold; font-size: 1rem; cursor: pointer; transition: background 0.15s; margin-top: 20px; }
.x-btn-dark-pink:hover { background: #be185d; }
</style>