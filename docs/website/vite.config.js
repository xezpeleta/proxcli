import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { cpSync, existsSync } from 'fs'

// After build, copy demos from public/demos to output (they're static assets)
function copyDemosPlugin() {
  return {
    name: 'copy-demos',
    closeBundle() {
      // nothing needed — Vite copies public/ automatically
    }
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: './',
  build: {
    outDir: '..',
    emptyOutDir: false,
  },
})
