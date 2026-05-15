import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/admin/',
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://147.139.134.10',
        changeOrigin: true,
      },
    },
  },
})
