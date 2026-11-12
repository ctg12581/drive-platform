<!-- src/views/QuizDesignView.vue (全量覆盖无错版) -->
<template>
  <div class="design-container">
    <!-- 吸顶返回栏 -->
    <div class="design-header">
      <button @click="router.push('/quiz')" class="btn-back">
        <svg viewBox="0 0 24 24" class="svg-inline"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
      </button>
      <h2 style="margin: 0; font-size: 1.2rem; font-weight: 800;">配置我的默契测验</h2>
    </div>

    <!-- 选项操作台 -->
    <div class="design-actions-bar">
      <button @click="openBankModal" class="action-btn-pill font-pink">➕ 从题库中选题</button>
      <button @click="openCreateModal" class="action-btn-pill">✏️ 新建自定义问题</button>
    </div>

    <!-- 当前出题清单时间线 (不固定数量) -->
    <div class="design-list">
      <div v-if="selectedQuestions.length === 0" class="empty-list-hint">
        <div style="font-size: 2.2rem; margin-bottom: 8px;">🧐</div>
        <p>您的出题清单中还没有题目</p>
        <p style="font-size: 0.8rem; color: var(--x-text-gray);">点击上方按钮，从题库选题或自主写新题吧！</p>
      </div>

      <div v-else class="timeline-box">
        <div v-for="(q, idx) in selectedQuestions" :key="q.id" class="design-q-card">
          <div class="q-card-header">
            <span class="q-card-index">Q{{ idx + 1 }}.</span>
            <button @click="removeQuestion(idx)" class="btn-remove-q">移出</button>
          </div>
          <p class="q-card-text">{{ q.text }}</p>
          
          <!-- 设定正确答案选项（自动支持2~4个） -->
          <div class="options-grid">
            <span class="set-answer-hint">🎯 请设定正确选项：</span>
            <label v-for="opt in q.options" :key="opt" :class="['opt-pill', { active: q.answer === opt[0] }]">
              <input type="radio" :name="'design_q_' + q.id" :value="opt[0]" v-model="q.answer">
              {{ opt }}
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- 悬浮固定底部发布栏 -->
    <div class="design-footer">
      <button @click="publishMyQuiz" class="btn-publish" :disabled="selectedQuestions.length === 0">
        确认并发布测验 ({{ selectedQuestions.length }}题)
      </button>
    </div>

    <!-- 💡 弹窗一：公共题库选题器 (带海量数据实时搜索 ＋ 类别过滤页签) -->
    <div v-if="showBankModal" class="modal-backdrop" @click.self="showBankModal = false">
      <div class="modal-card">
        <button class="modal-close" @click="showBankModal = false">✕</button>
        <h3 class="modal-title">从题库中添加问题</h3>
        
        <!-- 💡 搜索与过滤器面板 -->
        <div class="modal-filter-bar">
          <div class="modal-search-pill">
            <svg viewBox="0 0 24 24" class="search-icon-svg"><path d="M21.53 20.47l-3.66-3.66C19.195 15.24 20 13.214 20 11c0-4.97-4.03-9-9-9s-9 4.03-9 9 4.03 9 9 9c2.215 0 4.24-.804 5.808-2.13l3.66 3.66c.147.146.34.22.53.22s.385-.073.53-.22c.295-.293.295-.767.002-1.06zM3.5 11c0-4.135 3.365-7.5 7.5-7.5s7.5 3.365 7.5 7.5-3.365 7.5-7.5 7.5-7.5-3.365-7.5-7.5z"/></svg>
            <input type="text" v-model="bankSearchQuery" placeholder="快速模糊检索上百道题库...">
          </div>
          <!-- 筛选切换标签 -->
          <div class="filter-tabs">
            <button @click="bankFilterType = 'all'" :class="['filter-tab-btn', { active: bankFilterType === 'all' }]">全部</button>
            <button @click="bankFilterType = 'system'" :class="['filter-tab-btn', { active: bankFilterType === 'system' }]">系统推荐</button>
            <button @click="bankFilterType = 'mine'" :class="['filter-tab-btn', { active: bankFilterType === 'mine' }]">我创建的</button>
          </div>
        </div>

        <!-- 列表视口 -->
        <div class="modal-body">
          <div v-if="filteredBankQuestions.length === 0" class="no-results-hint">
            没有找到与过滤条件匹配的问题
          </div>
          <div v-else v-for="q in filteredBankQuestions" :key="q.id" class="bank-item">
            <label class="bank-label">
              <input type="checkbox" :value="q" v-model="checkedBankQuestions" :disabled="isAlreadyAdded(q.id)">
              <span :class="{ 'added-text': isAlreadyAdded(q.id) }">
                {{ q.text }} <span v-if="isAlreadyAdded(q.id)" class="tag-added">已加入清单</span>
              </span>
            </label>
          </div>
        </div>
        <!-- 底部固定动作条 -->
        <div class="modal-footer-bar">
          <button @click="addSelectedFromBank" class="btn-confirm-add" :disabled="checkedBankQuestions.length === 0">
            确认导入 (已选{{ checkedBankQuestions.length }}题)
          </button>
        </div>
      </div>
    </div>

    <!-- 💡 弹窗二：新建自定义多选题表单 (支持2~4个弹性选项增删) -->
    <div v-if="showCreateModal" class="modal-backdrop" @click.self="showCreateModal = false">
      <div class="modal-card" style="max-width: 440px; padding: 20px;">
        <button class="modal-close" @click="showCreateModal = false">✕</button>
        <h3 class="modal-title" style="color: var(--x-blue); padding-top: 10px;">✏️ 新建自定义问题</h3>
        <div class="modal-body" style="padding-top: 10px;">
          <div class="form-group">
            <label class="form-label">问题题干</label>
            <input type="text" v-model="customForm.text" placeholder="例如：周末下午你更想干什么？" required class="form-input">
          </div>
          
          <div class="form-group">
            <!-- 动态选项增删头部 -->
            <div class="dynamic-opt-header">
              <label class="form-label" style="margin: 0;">配置选项 (2~4个)</label>
              <button v-if="customForm.options.length < 4" @click="addCustomOption" class="btn-add-opt">+ 增加选项</button>
            </div>
            
            <!-- 动态循环渲染选项输入框 -->
            <div v-for="(opt, oIdx) in customForm.options" :key="oIdx" class="dynamic-opt-row">
              <span class="opt-prefix">{{ ['A', 'B', 'C', 'D'][oIdx] }}.</span>
              <input type="text" v-model="customForm.options[oIdx]" :placeholder="'请输入选项 ' + ['A', 'B', 'C', 'D'][oIdx] + ' 的内容'" required class="form-input flex-1">
              <!-- 最少保留2个选项 -->
              <button v-if="customForm.options.length > 2" @click="removeCustomOption(oIdx)" class="btn-delete-opt">✕</button>
            </div>
          </div>
          <button @click="createCustomQuestion" class="btn-confirm-add" style="background: var(--x-blue); margin-top: 15px;">保存并加入清单</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { apiFetch } from '../utils/api'
import { useQuizStore } from '../store/quiz'


const router = useRouter()
const authStore = useAuthStore()
const quizStore = useQuizStore()

// 出题清单
const selectedQuestions = ref([])

// 题库选择相关变量
const showBankModal = ref(false)
const bankQuestions = ref([])
const checkedBankQuestions = ref([]) 
const bankSearchQuery = ref('') // 实时搜索关键字
const bankFilterType = ref('all') // 过滤器状态: 'all' 全部, 'system' 系统推荐, 'mine' 我创建的

// 新建问题表单变量 (💡 初始化为 2 个空选项，即最简选项数)
const showCreateModal = ref(false)
const customForm = reactive({
  text: '',
  options: ['', ''] 
})

onMounted(() => {
  fetchMyQuizConfig()
})

const fetchMyQuizConfig = async () => {
  try {
    const res = await apiFetch('/quiz/my-config')
    const data = await res.json()
    if (res.ok && data.has_quiz) {
      selectedQuestions.value = data.questions
    }
  } catch (err) {
    console.error('获取我的测验失败:', err)
  }
}

// 💡 题库搜索 ＋ 类别过滤核心计算流
const filteredBankQuestions = computed(() => {
  return bankQuestions.value.filter(q => {
    // 1. 模糊匹配
    const matchesSearch = q.text.toLowerCase().includes(bankSearchQuery.value.trim().toLowerCase())
    
    // 2. 类别过滤
    let matchesCategory = true
    if (bankFilterType.value === 'system') {
      matchesCategory = (q.creator === 'admin' || q.creator === 'system')
    } else if (bankFilterType.value === 'mine') {
      matchesCategory = (q.creator === authStore.username)
    }

    return matchesSearch && matchesCategory
  })
})

const isAlreadyAdded = (questionId) => {
  return selectedQuestions.value.some(q => q.id === questionId)
}

const openBankModal = async () => {
  try {
    const res = await apiFetch('/quiz/questions')
    const data = await res.json()
    if (res.ok) {
      bankQuestions.value = data.questions
      checkedBankQuestions.value = [] 
      bankSearchQuery.value = '' // 打开时重置搜索框
      bankFilterType.value = 'all' // 重置筛选器
      showBankModal.value = true
    }
  } catch {
    alert('获取题库失败')
  }
}

// 💡 从题库导入：正确答案初始化为 null，不进行诱导性默认选中
const addSelectedFromBank = () => {
  checkedBankQuestions.value.forEach((q) => {
    if (!isAlreadyAdded(q.id)) {
      selectedQuestions.value.push({
        id: q.id,
        text: q.text,
        options: q.options,
        answer: null,
      })
    }
  })
  showBankModal.value = false
}

const removeQuestion = (index) => {
  selectedQuestions.value.splice(index, 1)
}

// 打开自定义问题表单时，重置表单为最简 2 个空选项
const openCreateModal = () => {
  customForm.text = ''
  customForm.options = ['', '']
  showCreateModal.value = true
}

// 💡 动态选项处理：增加选项 (最多 4 个)
const addCustomOption = () => {
  if (customForm.options.length < 4) {
    customForm.options.push('')
  }
}

// 💡 动态选项处理：移除选项 (最少 2 个)
const removeCustomOption = (index) => {
  if (customForm.options.length > 2) {
    customForm.options.splice(index, 1)
  }
}

// 💡 新增自定义题目：自动根据位置追加 A. B. C. D. 字母前缀
const createCustomQuestion = async () => {
  const text = customForm.text.trim()
  if (!text) {
    alert('请填写问题题干')
    return
  }
  
  // 校验是否每个选项都有内容
  const hasEmptyOption = customForm.options.some(opt => !opt.trim())
  if (hasEmptyOption) {
    alert('请将所有选项内容填写完整')
    return
  }

  // 格式化：自适应前缀映射 ['A', 'B', 'C', 'D']
  const prefix = ['A', 'B', 'C', 'D']
  const formattedOptions = customForm.options.map((opt, idx) => `${prefix[idx]}. ${opt.trim()}`)

  const payload = {
    question_text: text,
    options: formattedOptions
  }

  try {
    const res = await apiFetch('/quiz/questions', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (res.ok) {
      // 成功后，自动将新创的弹性问题推入本期清单，且预设答案为 null
      selectedQuestions.value.push({
        id: data.question_id,
        text: text,
        options: payload.options,
        answer: null 
      })
      showCreateModal.value = false
    } else {
      alert(data.detail)
    }
  } catch {
    alert('创建自定义题目失败')
  }
}

// 💡 发布我的测验：加入已选检验和答案未设阻断拦截
const publishMyQuiz = async () => {
  if (selectedQuestions.value.length === 0) {
    alert('出题清单不能为空')
    return
  }

  const unAnsweredIndex = selectedQuestions.value.findIndex(q => !q.answer)
  if (unAnsweredIndex !== -1) {
    alert(`💡 请为清单中的所有题目预设正确选项！\n第 ${unAnsweredIndex + 1} 题尚未指定答案。`)
    return
  }

  const payload = {
    title: '我的大考验',
    questions: selectedQuestions.value.map(q => ({
      question_id: q.id,
      answer: q.answer
    }))
  }
  try {
    const res = await apiFetch('/quiz/create', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
    if (res.ok) {
      // 💡 核心升级：成功发布后，立即在本地预载缓存。
      // 这能保证一跳转回 /quiz 页面时，顶层卡片瞬间、100% 变身为已发布状态，毫无多余闪烁！
      quizStore.setMyQuiz({
        has_quiz: true,
        title: '我的大考验',
        questions_count: selectedQuestions.value.length
      })
      
      router.push('/quiz')
    }
  } catch {
    alert('保存测验失败')
  }
}
</script>

<style scoped>
.design-container { width: 100%; position: relative; padding-bottom: 80px; background: #fff; min-height: calc(100vh - var(--app-top) - var(--app-bottom)); }

/* 吸顶头部 */
.design-header {
  position: sticky; top: var(--app-top); background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--xhs-line); padding: 12px 16px; z-index: 20;
  display: flex; align-items: center; gap: 14px;
}
.btn-back { background: transparent; border: none; cursor: pointer; color: var(--xhs-text); display: flex; align-items: center; }
.svg-inline { width: 22px; height: 22px; fill: currentColor; }

/* 选项操作栏 */
.design-actions-bar { display: flex; gap: 12px; padding: 16px; border-bottom: 1px solid var(--xhs-line); }
.action-btn-pill {
  flex: 1; background: #fafafa; color: var(--xhs-text); border: 1px solid var(--xhs-line);
  height: 40px; border-radius: var(--xhs-radius-pill); font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.15s;
}
.action-btn-pill:hover { background: #f2f2f4; }
.action-btn-pill.font-pink { border-color: var(--xhs-red-line); color: var(--xhs-red); background: var(--xhs-red-soft); }
.action-btn-pill.font-pink:hover { background: #ffe1e6; }

/* 出题清单 */
.design-list { padding: 8px 0; }
.empty-list-hint { text-align: center; color: var(--xhs-text-3); font-size: 0.9rem; padding: 60px 20px; line-height: 1.7; }

.design-q-card { padding: 16px; border-bottom: 1px solid var(--xhs-line); text-align: left; }
.q-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.q-card-index { font-weight: 800; font-size: 1.05rem; color: var(--xhs-red); }
.btn-remove-q { background: transparent; border: none; color: var(--xhs-red); font-size: 0.8rem; font-weight: 700; cursor: pointer; }
.btn-remove-q:hover { text-decoration: underline; }
.q-card-text { font-weight: 700; font-size: 0.95rem; margin: 0 0 12px 0; color: var(--xhs-text); }
.set-answer-hint { display: block; font-size: 0.78rem; color: var(--xhs-text-3); margin-bottom: 6px; font-weight: 700; }

/* 正确答案选择 */
.options-grid { display: flex; flex-direction: column; gap: 8px; }
.opt-pill {
  display: block; padding: 10px 14px; border: 1.5px solid var(--xhs-line); border-radius: 12px;
  font-size: 0.85rem; color: var(--xhs-text); cursor: pointer; transition: all 0.15s;
}
.opt-pill input { display: none; }
.opt-pill.active {
  background: var(--xhs-red-soft); border-color: var(--xhs-red); color: var(--xhs-red); font-weight: 700;
}

/* 底部悬浮栏 */
.design-footer {
  position: fixed; bottom: var(--app-bottom); left: 0; right: 0;
  background: rgba(255, 255, 255, 0.94); backdrop-filter: blur(14px);
  border-top: 1px solid var(--xhs-line); padding: 12px 16px; z-index: 20;
  max-width: 640px; margin: 0 auto;
}
.btn-publish {
  width: 100%; height: 46px; background: var(--xhs-red); color: #fff; border: none;
  border-radius: var(--xhs-radius-pill); font-weight: 800; font-size: 1rem; cursor: pointer;
  transition: background 0.2s; box-shadow: 0 6px 18px rgba(255, 36, 66, 0.28);
}
.btn-publish:hover { background: #ef1b38; }
.btn-publish:disabled { background: #ffc2cb; box-shadow: none; cursor: not-allowed; }

/* 模态弹窗 */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.45); backdrop-filter: blur(2px); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.modal-card { width: 100%; max-width: 460px; background: #fff; border-radius: 22px; max-height: 84vh; display: flex; flex-direction: column; overflow: hidden; position: relative; box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24); }
.modal-close { position: absolute; top: 14px; right: 16px; background: transparent; border: none; font-size: 1.1rem; cursor: pointer; color: var(--xhs-text-3); z-index: 5; }
.modal-title { margin-top: 0; font-size: 1.15rem; font-weight: 800; text-align: center; color: var(--xhs-text); padding: 24px 24px 0; }

/* 题库模态搜索与筛选栏 */
.modal-filter-bar { display: flex; flex-direction: column; gap: 10px; padding: 12px 22px; border-bottom: 1px solid var(--xhs-line); }
.modal-search-pill { display: flex; align-items: center; gap: 10px; background: #f4f4f6; border-radius: var(--xhs-radius-pill); padding: 7px 14px; }
.modal-search-pill input { flex: 1; border: none; background: transparent; outline: none; font-size: 0.85rem; color: var(--xhs-text); }
.search-icon-svg { width: 16px; height: 16px; fill: var(--xhs-text-3); }

.filter-tabs { display: flex; gap: 8px; }
.filter-tab-btn {
  background: transparent; border: 1px solid var(--xhs-line); color: var(--xhs-text-2);
  font-size: 0.75rem; font-weight: 700; padding: 5px 14px; border-radius: var(--xhs-radius-pill); cursor: pointer; transition: all 0.15s;
}
.filter-tab-btn:hover { background: #fafafa; }
.filter-tab-btn.active { background: var(--xhs-red); color: #fff; border-color: var(--xhs-red); }

.modal-body { flex: 1; overflow-y: auto; padding: 16px 22px; }
.modal-footer-bar { padding: 12px 22px; border-top: 1px solid var(--xhs-line); }

/* 题库列表项目 */
.bank-item { padding: 12px 0; border-bottom: 1px solid var(--xhs-line); text-align: left; }
.bank-label { display: flex; align-items: center; gap: 10px; font-size: 0.92rem; font-weight: 600; cursor: pointer; color: var(--xhs-text); }
.bank-label input { width: auto; accent-color: var(--xhs-red); }
.added-text { color: var(--xhs-text-3); text-decoration: line-through; }
.tag-added { background: var(--xhs-red-soft); color: var(--xhs-red); font-size: 0.72rem; padding: 2px 8px; border-radius: 6px; font-weight: 600; margin-left: 6px; }
.btn-confirm-add { width: 100%; height: 46px; background: var(--xhs-red); color: #fff; border: none; border-radius: var(--xhs-radius-pill); font-weight: 800; font-size: 0.95rem; cursor: pointer; transition: background 0.15s; box-shadow: 0 6px 18px rgba(255, 36, 66, 0.24); }
.btn-confirm-add:disabled { background: #ffc2cb; box-shadow: none; cursor: not-allowed; }
.no-results-hint { text-align: center; color: var(--xhs-text-3); font-size: 0.9rem; padding: 24px 0; }

/* 自定义问题表单 */
.form-group { margin-bottom: 16px; text-align: left; }
.form-label { display: block; font-size: 0.78rem; color: var(--xhs-text-3); font-weight: 700; margin-bottom: 8px; }
.form-input { width: 100%; height: 42px; padding: 0 14px; border: 1.5px solid transparent; border-radius: 12px; box-sizing: border-box; background: #f4f4f6; color: var(--xhs-text); outline: none; font-size: 0.9rem; }
.form-input:focus { border-color: var(--xhs-red); background: #fff; }

.dynamic-opt-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.btn-add-opt { background: transparent; border: none; color: var(--xhs-red); font-size: 0.8rem; font-weight: 700; cursor: pointer; }
.btn-add-opt:hover { text-decoration: underline; }

.dynamic-opt-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.opt-prefix { font-weight: 700; color: var(--xhs-text-3); width: 16px; }
.btn-delete-opt { background: transparent; border: none; color: var(--xhs-red); font-size: 1rem; cursor: pointer; padding: 4px; }
</style>