import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { cpSync, mkdirSync, readFileSync, existsSync } from 'fs'
import { join, dirname } from 'path'

// Copy markdown docs from parent docs/ into output docs/ after build
function copyDocsPlugin() {
  const docsDir = join(__dirname, '../..')

  return {
    name: 'copy-docs',
    closeBundle() {
      const outDocsDir = join(__dirname, '..', 'docs')
      mkdirSync(outDocsDir, { recursive: true })
      const files = [
        'cloud-init.md',
        'api-permissions.md',
        'api-coverage.md',
        'coding-agents.md',
        'production-automation.md',
      ]
      for (const f of files) {
        const src = join(docsDir, f)
        if (existsSync(src)) {
          cpSync(src, join(outDocsDir, f))
        }
      }
    }
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), copyDocsPlugin()],
  base: './',
  build: {
    outDir: '..',
    emptyOutDir: false,
  },
})
