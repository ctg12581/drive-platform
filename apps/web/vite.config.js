import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  // 相对 base：同时兼容 GitHub Pages 子路径与 Vercel 根路径部署
  base: './',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@drive/shared': fileURLToPath(new URL('../../packages/shared/src/index.js', import.meta.url)),
    },
  },
})
