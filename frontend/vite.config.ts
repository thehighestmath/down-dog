import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // npm run dev: /api/* уходит на бэкенд, как nginx делает в Docker
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
