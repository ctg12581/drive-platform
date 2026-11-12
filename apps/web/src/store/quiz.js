// src/store/quiz.js
// 默契挑战的本地缓存，保证切换/刷新页面后 0ms 还原出题名片。
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { readJSON, writeJSON } from '@drive/shared'

export const useQuizStore = defineStore('quiz', () => {
  const cachedMyQuiz = ref(readJSON('cached_my_quiz', null))
  const cachedFriendQuizzes = ref(readJSON('cached_friend_quizzes', []))

  function setMyQuiz(quiz) {
    cachedMyQuiz.value = quiz
    if (quiz) {
      writeJSON('cached_my_quiz', quiz)
    } else {
      localStorage.removeItem('cached_my_quiz')
    }
  }

  function setFriendQuizzes(quizzes) {
    cachedFriendQuizzes.value = quizzes
    writeJSON('cached_friend_quizzes', quizzes)
  }

  return { cachedMyQuiz, cachedFriendQuizzes, setMyQuiz, setFriendQuizzes }
})
