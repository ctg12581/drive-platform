import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    // 仅在开发模式启用 devtools，避免生产构建引入任何调试开销
    mode === 'development' ? vueDevTools() : null,
  ].filter(Boolean),
  // 相对 base：部署到 GitHub Pages 的 /admin/ 子路径时资源仍可正确解析
  base: './',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@drive/shared': fileURLToPath(new URL('../../packages/shared/src/index.js', import.meta.url)),
    },
  },
}))
