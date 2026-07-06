import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    host: true, // 允许局域网访问
    proxy: {
      '/api/agent': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true
      },
      '/api/rag': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/api/session': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/api/vector': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/user': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/file': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})