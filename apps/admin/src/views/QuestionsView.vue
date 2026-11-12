<!-- src/views/QuestionsView.vue (全量覆盖无错版) -->
<template>
  <div class="questions-container">
    <!-- 顶部状态标题栏与动作面板 -->
    <div class="page-title-bar">
      <div class="title-text">
        <h2>📚 系统公共题库管理</h2>
        <p>创建、管理和批量维护全网用户在 DRIVE 默契大挑战中使用的系统级恋爱选择题</p>
      </div>
      <div class="header-actions">
        <button @click="showBulkModal = true" class="x-btn-pill-dark">📂 批量导入</button>
        <button @click="openAddModal" class="x-btn-pill-blue">+ 新增系统题目</button>
      </div>
    </div>

    <!-- 题目卡片列表流 -->
    <div class="questions-list">
      <div v-if="questions.length === 0" class="empty-hint">
        <div style="font-size: 3rem; margin-bottom: 12px;">📭</div>
        <h3>系统公共题库为空</h3>
        <p>点击右上角的按钮，开始发布您的第一道公共选择题吧！</p>
      </div>

      <div v-else v-for="(q, idx) in questions" :key="q.id" class="question-card">
        <div class="q-header">
          <span class="q-index">系统题目 {{ questions.length - idx }}</span>
          <button @click="deleteQuestion(q.id)" class="btn-delete">删除此题</button>
        </div>
        <p class="q-text">{{ q.text }}</p>
        <div class="options-grid">
          <span v-for="opt in q.options" :key="opt" class="opt-item">{{ opt }}</span>
        </div>
      </div>
    </div>

    <!-- 💡 弹窗一：批量导入大文本弹窗 (彻底解决高度压缩和样式怪异问题) -->
    <div v-if="showBulkModal" class="modal-backdrop" @click.self="showBulkModal = false">
      <div class="modal-card" style="max-width: 520px; padding: 20px;">
        <button class="modal-close" @click="showBulkModal = false">✕</button>
        <h3 class="modal-title">📂 批量导入公共题库</h3>
        <p style="font-size: 0.8rem; color: #6b7280; margin: 6px 0 16px 0; text-align: center;">请在下方大输入框中，直接贴入符合 JSON 规范的任意数量题目数组：</p>
        
        <div class="modal-body" style="padding: 0;">
          <!-- 💡 核心修复：应用专属的 .bulk-textarea 样式，拥有完美的高度和滚动体验 -->
          <textarea v-model="bulkJsonInput" class="bulk-textarea" placeholder='格式示范 (可输入10道、50道甚至上百道题目):
[
  {
    "question_text": "下雨天你更喜欢哪种约会方式？",
    "options": ["A. 看电影", "B. 雨中散步", "C. 喝咖啡"]
  },
  {
    "question_text": "你心目中最能接受的解压方式是？",
    "options": ["A. 安静独处", "B. 找对方倾诉", "C. 大吃一顿"]
  }
]'></textarea>
          <button @click="handleBulkImport" class="btn-confirm-add" style="margin-top: 15px; background: #111827;">确认解析并导入</button>
        </div>
      </div>
    </div>

    <!-- 💡 弹窗二：新建系统题目（支持 2~4 个弹性选项增删） -->
    <div v-if="showAddModal" class="modal-backdrop" @click.self="showAddModal = false">
      <div class="modal-card" style="max-width: 440px; padding: 20px;">
        <button class="modal-close" @click="showAddModal = false">✕</button>
        <h3 class="modal-title" style="color: #2563eb; padding-top: 10px;">✏️ 新建系统公共问题</h3>
        
        <div class="modal-body" style="padding: 10px 0 0 0;">
          <div class="form-group">
            <label class="form-label">问题题干</label>
            <input type="text" v-model="form.text" placeholder="例如：你心目中最能接受的解压方式是？" required class="form-input">
          </div>
          
          <div class="form-group">
            <div class="dynamic-opt-header">
              <label class="form-label" style="margin: 0;">配置选项 (2~4个)</label>
              <button v-if="form.options.length < 4" @click="addCustomOption" class="btn-add-opt">+ 增加选项</button>
            </div>
            
            <div v-for="(opt, oIdx) in form.options" :key="oIdx" class="dynamic-opt-row">
              <span class="opt-prefix">{{ ['A', 'B', 'C', 'D'][oIdx] }}.</span>
              <input type="text" v-model="form.options[oIdx]" :placeholder="'请输入选项 ' + ['A', 'B', 'C', 'D'][oIdx] + ' 的内容'" required class="form-input flex-1">
              <button v-if="form.options.length > 2" @click="removeCustomOption(oIdx)" class="btn-delete-opt">✕</button>
            </div>
          </div>
          <button @click="createQuestion" class="btn-confirm-add" style="background: var(--x-blue); margin-top: 15px;">保存并发布入库</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { apiFetch } from '../utils/api'

const questions = ref([])
const showAddModal = ref(false)
const showBulkModal = ref(false)
const bulkJsonInput = ref('')
const form = reactive({ text: '', options: ['', ''] })

onMounted(() => {
  fetchQuestions()
})

const fetchQuestions = async () => {
  try {
    const res = await apiFetch('/admin/quiz/questions')
    const data = await res.json()
    if (res.ok) {
      questions.value = data.questions
    }
  } catch {
    console.error('拉取公共题库失败')
  }
}

// 动态选项增加
const addCustomOption = () => {
  if (form.options.length < 4) {
    form.options.push('')
  }
}

// 动态选项删除
const removeCustomOption = (index) => {
  if (form.options.length > 2) {
    form.options.splice(index, 1)
  }
}

// 动态初始化选项
const openAddModal = () => {
  form.text = ''
  form.options = ['', '']
  showAddModal.value = true
}

const createQuestion = async () => {
  const text = form.text.trim()
  if (!text) {
    alert('请填写问题题干')
    return
  }
  
  const hasEmptyOption = form.options.some(opt => !opt.trim())
  if (hasEmptyOption) {
    alert('请将所有配置的选项内容填写完整')
    return
  }

  // 自适应映射前缀
  const prefix = ['A', 'B', 'C', 'D']
  const formattedOptions = form.options.map((opt, idx) => `${prefix[idx]}. ${opt.trim()}`)

  const payload = {
    question_text: text,
    options: formattedOptions
  }

  try {
    const res = await apiFetch('/admin/quiz/questions', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
    if (res.ok) {
      showAddModal.value = false
      fetchQuestions()
    } else {
      const data = await res.json()
      alert(data.detail || '创建失败')
    }
  } catch (err) {
    console.error(err)
    alert('创建失败，网络故障')
  }
}

const deleteQuestion = async (id) => {
  if (!window.confirm('确定要永久将此题从系统公共题库中删除吗？这不会影响用户已出完题的本地数据。')) return
  try {
    const res = await apiFetch(`/admin/quiz/questions/${id}`, { method: 'DELETE' })
    if (res.ok) {
      fetchQuestions()
    }
  } catch {
    alert('删除失败')
  }
}

// 💡 升级版：带 F12 控制台深度诊断的批量导入处理函数
const handleBulkImport = async () => {
  const input = bulkJsonInput.value.trim()
  if (!input) {
    alert('请贴入有效的 JSON 数组数据')
    return
  }
  
  let parsedData = null
  try {
    parsedData = JSON.parse(input)
    if (!Array.isArray(parsedData)) {
      alert('数据必须是一个数组（Array）格式，确保开头有 [ 且结尾有 ]')
      return
    }
  } catch (err) {
    // 💡 打印深度错误至控制台，帮助调试格式错误
    console.error('❌ JSON 语法解析失败具体报错:', err)
    alert('💡 JSON 格式解析失败！请检查标点符号或双引号。详情可按 F12 打开开发者工具控制台(Console)查看精准的错误行号。')
    return
  }

  // 基础格式校验
  const isValid = parsedData.every((q, idx) => {
    const hasText = !!q.question_text
    const isOptionsArray = Array.isArray(q.options)
    if (!hasText || !isOptionsArray) {
      console.warn(`⚠️ 校验失败：第 ${idx + 1} 道题目缺少 "question_text" 属性，或 "options" 不是数组格式。`)
    }
    return hasText && isOptionsArray
  })

  if (!isValid) {
    alert('批量导入失败：部分题目格式不规范。详情请按 F12 进入控制台查看。')
    return
  }

  try {
    const res = await apiFetch('/admin/quiz/questions/bulk', {
      method: 'POST',
      body: JSON.stringify({ questions: parsedData })
    })
    const data = await res.json()
    if (res.ok) {
      alert(data.message || '批量导入成功！')
      bulkJsonInput.value = ''
      showBulkModal.value = false
      fetchQuestions()
    } else {
      console.error('❌ 后端校验失败报错:', data)
      alert(data.detail || '导入失败，后端验证拦截。可按 F12 打开控制台查看详情')
    }
  } catch (err) {
    console.error(err)
    alert('请求故障')
  }
}
</script>

<style scoped>
.questions-container {
  padding: 30px;
}

/* 顶部状态标题栏 */
.page-title-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}
.title-text { text-align: left; }
.title-text h2 { margin: 0 0 6px 0; font-size: 1.5rem; font-weight: 800; }
.title-text p { margin: 0; color: #6b7280; font-size: 0.95rem; }

.header-actions { display: flex; gap: 12px; }

/* 按钮组 */
.x-btn-pill-blue {
  background: #2563eb; color: white; border: none; font-weight: bold;
  font-size: 0.85rem; padding: 0 16px; height: 34px; border-radius: 9999px; cursor: pointer; transition: background 0.15s;
}
.x-btn-pill-blue:hover { background: #1d4ed8; }

.x-btn-pill-dark {
  background: #111827; color: white; border: 1px solid #374151; font-weight: bold;
  font-size: 0.85rem; padding: 0 16px; height: 34px; border-radius: 9999px; cursor: pointer; transition: background 0.15s;
}
.x-btn-pill-dark:hover { background: #1f2937; }

/* 空提示 */
.empty-hint { text-align: center; color: #9ca3af; padding: 80px 20px; }
.empty-hint h3 { margin: 12px 0 8px 0; color: #111827; }

/* 问题列表卡片 */
.question-card {
  background: white; border-radius: 12px; padding: 16px;
  border: 1px solid #e5e7eb; margin-bottom: 16px; text-align: left;
}
.q-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.q-index { font-weight: bold; font-size: 0.85rem; color: #2563eb; }
.btn-delete { background: transparent; border: none; color: #ef4444; font-size: 0.8rem; font-weight: bold; cursor: pointer; }
.btn-delete:hover { text-decoration: underline; }
.q-text { font-weight: bold; font-size: 1rem; margin: 0 0 12px 0; color: #111827; }

/* 选项展示网格 */
.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}
.opt-item { background: #f9fafb; padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; border: 1px solid #f3f4f6; }

/* 💡 新增：批量导入大文本输入框专属样式，彻底消灭高度压缩和 weird 视觉 */
.bulk-textarea {
  width: 100%;
  height: 220px !important; /* 强制锁定完美高度 */
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-sizing: border-box;
  background: #f9fafb;
  color: #111827;
  outline: none;
  font-family: monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  resize: none;
  transition: all 0.15s;
}
.bulk-textarea:focus {
  border-color: #2563eb;
  background: #ffffff;
}

/* 新增自定义选项动态行 */
.dynamic-opt-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.btn-add-opt { background: transparent; border: none; color: #2563eb; font-size: 0.8rem; font-weight: bold; cursor: pointer; }
.btn-add-opt:hover { text-decoration: underline; }

.dynamic-opt-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.opt-prefix { font-weight: bold; color: #9ca3af; width: 16px; }
.btn-delete-opt { background: transparent; border: none; color: #ef4444; font-size: 1rem; cursor: pointer; padding: 4px; }
</style>