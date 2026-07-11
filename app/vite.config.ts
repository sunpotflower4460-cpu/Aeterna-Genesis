import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' -> self-contained static build (no CDN, deployable offline)
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { outDir: 'dist', chunkSizeWarningLimit: 1400 },
})
