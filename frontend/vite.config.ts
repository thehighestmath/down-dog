import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  // npm test: компоненты рендерятся в jsdom - браузерный DOM внутри Node
  test: {
    environment: 'jsdom',
  },
})
