<!-- src/views/QuizView.vue · 小红书风格默契挑战 -->
<template>
  <div class="quiz-container">
    <div class="quiz-header">
      <h2 class="quiz-title">💖 默契挑战</h2>
    </div>

    <!-- 我的出题卡片 -->
    <div class="quiz-owner-section">
      <div v-if="!myQuiz" class="owner-card no-quiz">
        <div class="owner-emoji">💌</div>
        <h4 class="owner-h4">还没有你的专属默契测验</h4>
        <p class="owner-p">出题后，好友点开你的主页就能测出和你的默契值</p>
        <button @click="router.push('/quiz/design')" class="xhs-btn-primary">立即出题</button>
      </div>

      <div v-else class="owner-card has-quiz">
        <div class="has-quiz-left">
          <div class="heart-avatar">💘</div>
          <div class="quiz-meta-info">
            <h4 class="has-quiz-title">{{ myQuiz.title }}</h4>
            <p class="has-quiz-sub">已发布 · 默契挑战已上线</p>
          </div>
        </div>
        <button @click="router.push('/quiz/design')" class="xhs-btn-ghost btn-sm">修改 / 重新出题</button>
      </div>
    </div>

    <!-- 好友的挑战 -->
    <div class="quiz-friends-section">
      <h3 class="section-title">好友的默契考验 ({{ friendQuizzes.length }})</h3>

      <div v-if="friendQuizzes.length === 0" class="xhs-empty">
        👋 暂无好友发布默契测验<br />
        <span style="font-size:0.82rem;">去「搜索」添加好友，或在「通知」里同意申请吧</span>
      </div>

      <div v-else class="friend-quiz-list-box">
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
            <button v-if="!q.already_challenged" @click="startChallenge(q)" class="xhs-btn-primary btn-sm">
              开始挑战
            </button>
            <button v-else @click="startChallenge(q)" class="score-btn btn-sm">
              灵犀 {{ q.score }}%
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 挑战答题弹窗 -->
    <div v-if="showChallengeModal" class="modal-backdrop" @click.self="showChallengeModal = false">
      <div class="modal-card challenge-modal">
        <button class="modal-close" @click="showChallengeModal = false">✕</button>
        <h3 class="challenge-title">💘 {{ activeChallengeQuiz.title }}</h3>
        <p class="challenge-sub">答完题提交，计算你们的灵魂契合度</p>

        <div class="modal-body">
          <div v-for="(q, idx) in activeChallengeQuiz.questions" :key="q.id" class="quiz-setup-item">
            <p class="quiz-q-title">Q{{ idx + 1 }}. {{ q.text }}</p>
            <div class="options-group">
              <label v-for="opt in q.options" :key="opt" :class="['opt-label', { checked: challengeAnswers[q.id] === opt[0] }]">
                <input type="radio" :name="'challenge_q_' + q.id" :value="opt[0]" v-model="challengeAnswers[q.id]">
                {{ opt }}
              </label>
            </div>
          </div>
          <button @click="submitChallenge" class="xhs-btn-primary challenge-submit">提交我的答题卡</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { isUrl } from '@drive/shared'
import { useAuthStore } from '../store/auth'
import { useQuizStore } from '../store/quiz'
import { apiFetch } from '../utils/api'

const router = useRouter()
const authStore = useAuthStore()
const quizStore = useQuizStore()

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
      quizStore.setMyQuiz(data)
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
      friendQuizzes.value = data.quizzes || []
      quizStore.setFriendQuizzes(data.quizzes || [])
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
      Object.keys(challengeAnswers).forEach((key) => delete challengeAnswers[key])
      data.questions.forEach(q => {
        challengeAnswers[q.id] = null
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
</script>

<style scoped>
.quiz-container { width: 100%; background: #fff; min-height: calc(100vh - var(--app-top) - var(--app-bottom)); }
.quiz-header {
  position: sticky;
  top: var(--app-top);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--xhs-line);
  padding: 16px;
  z-index: 20;
}
.quiz-title { margin: 0; font-size: 1.2rem; font-weight: 800; }

.quiz-owner-section { padding: 16px; border-bottom: 1px solid var(--xhs-line); }
.owner-card { border-radius: 18px; padding: 22px; text-align: center; box-sizing: border-box; }
.owner-card.no-quiz { background: var(--xhs-red-soft); border: 1px dashed var(--xhs-red-line); }
.owner-emoji { font-size: 2.2rem; margin-bottom: 8px; }
.owner-h4 { margin: 0 0 6px; font-size: 1rem; font-weight: 800; color: var(--xhs-text); }
.owner-p { font-size: 0.8rem; color: var(--xhs-text-2); margin: 0 0 16px; }
.owner-card.has-quiz {
  background: #fff;
  border: 1px solid var(--xhs-line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  text-align: left;
  box-shadow: var(--xhs-shadow);
}
.has-quiz-left { display: flex; align-items: center; gap: 12px; }
.heart-avatar {
  width: 48px;
  height: 48px;
  background: var(--xhs-red-soft);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}
.quiz-meta-info { display: flex; flex-direction: column; }
.has-quiz-title { margin: 0; font-size: 0.98rem; font-weight: 800; color: var(--xhs-text); }
.has-quiz-sub { margin: 4px 0 0; font-size: 0.76rem; color: var(--xhs-text-3); }
.btn-sm { height: 32px; padding: 0 14px; font-size: 0.8rem; flex-shrink: 0; }

.quiz-friends-section { width: 100%; }
.section-title { font-size: 0.98rem; font-weight: 800; padding: 16px 16px 8px; margin: 0; text-align: left; }

.friend-quiz-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--xhs-line);
  gap: 12px;
}
.friend-quiz-card:active { background: #fafafa; }
.friend-card-left { display: flex; align-items: center; gap: 12px; text-align: left; overflow: hidden; }
.friend-avatar {
  width: 46px;
  height: 46px;
  background: #f4f4f6;
  border-radius: 50%;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.friend-info { display: flex; flex-direction: column; overflow: hidden; }
.friend-name-row { display: flex; align-items: center; gap: 6px; }
.friend-nickname { font-weight: 700; font-size: 0.94rem; color: var(--xhs-text); }
.friend-handle { font-size: 0.8rem; color: var(--xhs-text-3); }
.friend-quiz-title {
  font-size: 0.8rem;
  color: var(--xhs-red);
  font-weight: 700;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.friend-card-right { display: flex; align-items: center; flex-shrink: 0; }
.score-btn {
  background: var(--xhs-red-soft);
  color: var(--xhs-red);
  border: 1px solid var(--xhs-red-line);
  border-radius: var(--xhs-radius-pill);
  font-weight: 700;
  cursor: pointer;
}

/* 弹窗 */
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
  max-width: 460px;
  max-height: 86vh;
  background: #fff;
  border-radius: 22px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}
.modal-close {
  position: absolute;
  top: 14px;
  right: 16px;
  background: transparent;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  color: var(--xhs-text-3);
}
.challenge-title { margin: 22px 22px 4px; font-size: 1.15rem; font-weight: 800; text-align: center; color: var(--xhs-text); }
.challenge-sub { margin: 0 22px 8px; font-size: 0.78rem; color: var(--xhs-text-3); text-align: center; }
.modal-body { flex: 1; overflow-y: auto; padding: 12px 22px 22px; }
.quiz-setup-item { margin-bottom: 18px; text-align: left; }
.quiz-q-title { font-weight: 700; font-size: 0.92rem; margin: 0 0 10px; color: var(--xhs-text); }
.options-group { display: flex; flex-direction: column; gap: 8px; }
.opt-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.86rem;
  padding: 10px 14px;
  border: 1.5px solid var(--xhs-line);
  border-radius: 12px;
  cursor: pointer;
  color: var(--xhs-text);
  transition: all 0.14s;
}
.opt-label input { display: none; }
.opt-label.checked {
  border-color: var(--xhs-red);
  background: var(--xhs-red-soft);
  color: var(--xhs-red);
  font-weight: 700;
}
.challenge-submit { width: 100%; margin-top: 8px; }
</style>
