// src/store/home.js
// 主页动态流的本地缓存，保证刷新后先秒开旧数据（SWR）。
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { readJSON, writeJSON } from '@drive/shared'

export const useMomentsStore = defineStore('moments', () => {
  const cachedPosts = ref(readJSON('cached_posts', []))

  // 发布新动态后自增，供 HomeView 监听并静默刷新时间线。
  const refreshTick = ref(0)

  function setPosts(posts) {
    cachedPosts.value = posts
    writeJSON('cached_posts', posts)
  }

  function requestRefresh() {
    refreshTick.value += 1
  }

  return { cachedPosts, refreshTick, setPosts, requestRefresh }
})
