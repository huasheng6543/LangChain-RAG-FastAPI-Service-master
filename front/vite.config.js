import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    host: true, // 允许局域网访问
    proxy: {
      // AI相关接口代理到8002端口（FastAPI后端）
      '/api/agent': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
        ws: true
      },
      '/api/rag': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true
      },
      '/api/session': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true
      },
      '/api/vector': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true
      },
      // 用户相关接口代理到8002端口（FastAPI后端）
      '/user': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true
      },
      '/file': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true
      }
    }
  }
})