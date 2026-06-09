// vite.config.js - Vite build configuration.
// Proxies /api calls to the FastAPI backend during development.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Forward all /api requests to the backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: '../backend/static',  // Build directly into backend/static for production serving
    emptyOutDir: true,
  }
})
