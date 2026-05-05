import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    host: true, // 允许局域网访问
    proxy: {
      // AI相关接口代理到8001端口（FastAPI后端）
      '/api/agent': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        ws: true
      },
      '/api/rag': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true
      },
      '/api/session': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true
      },
      '/api/vector': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true
      },
      // 用户相关接口代理到8000端口
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