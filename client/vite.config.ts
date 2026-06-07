import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// API_TARGET is injected by docker-compose; falls back to localhost for local dev
const API_TARGET = process.env.API_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/chat': { target: API_TARGET, changeOrigin: true },
      '/health': { target: API_TARGET, changeOrigin: true },
    },
  },
})
