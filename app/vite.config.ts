import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' -> self-contained static build (no CDN, deployable offline)
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { outDir: 'dist', chunkSizeWarningLimit: 1400 },
  // `npm run dev` + `python -m tools.lab.server`: the live lab API lives on the lab server
  server: { proxy: { '/api': { target: 'http://127.0.0.1:8765', changeOrigin: false } } },
})
