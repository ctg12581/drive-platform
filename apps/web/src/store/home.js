// src/store/home.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useMomentsStore = defineStore('moments', () => {
  // 💡 核心：初始化时，先尝试从本地物理缓存里提取上一次加载成功的帖子。
  // 这保证了即使刷新浏览器，也能实现 0ms 瞬间秒开！
  const cachedPosts = ref(JSON.parse(localStorage.getItem('cached_posts') || '[]'))

  function setPosts(posts) {
    cachedPosts.value = posts
    // 写入物理缓存
    localStorage.setItem('cached_posts', JSON.stringify(posts))
  }

  return { cachedPosts, setPosts }
})