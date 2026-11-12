// src/store/quiz.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useQuizStore = defineStore('quiz', () => {
  // 💡 核心：初始化时，先尝试从本地物理缓存里提取我自己的出题名片状态。
  // 这保证了切换页面甚至是刷新浏览器，也能实现 0ms 瞬间显示“我的大考验”！
  const cachedMyQuiz = ref(JSON.parse(localStorage.getItem('cached_my_quiz') || 'null'))
  
  // 💡 顺带缓存好友的测验卡片列表，让整个大厅也实现 0ms 秒开！
  const cachedFriendQuizzes = ref(JSON.parse(localStorage.getItem('cached_friend_quizzes') || '[]'))

  function setMyQuiz(quiz) {
    cachedMyQuiz.value = quiz
    if (quiz) {
      localStorage.setItem('cached_my_quiz', JSON.stringify(quiz))
    } else {
      localStorage.removeItem('cached_my_quiz')
    }
  }

  function setFriendQuizzes(quizzes) {
    cachedFriendQuizzes.value = quizzes
    localStorage.setItem('cached_friend_quizzes', JSON.stringify(quizzes))
  }

  return { cachedMyQuiz, cachedFriendQuizzes, setMyQuiz, setFriendQuizzes }
})