import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { existsSync, readFileSync } from 'fs'
import { join } from 'path'

const DOC_FILES = [
  'quickstart.md',
  'cloud-init.md',
  'api-permissions.md',
  'api-coverage.md',
  'coding-agents.md',
  'production-automation.md',
]

// Canonical source for docs: docs/*.md (two levels up from docs/website/)
const CANONICAL_DOCS = join(__dirname, '..', '..')

// Dev: serve canonical docs at /docs/*.md for fetch() calls
function serveDocsPlugin() {
  return {
    name: 'serve-docs',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.url && req.url.startsWith('/docs/') && req.url.endsWith('.md')) {
          const filename = req.url.replace('/docs/', '')
          if (DOC_FILES.includes(filename)) {
            const src = join(CANONICAL_DOCS, filename)
            if (existsSync(src)) {
              res.setHeader('Content-Type', 'text/markdown; charset=utf-8')
              res.end(readFileSync(src, 'utf-8'))
              return
            }
          }
        }
        next()
      })
    }
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), serveDocsPlugin()],
  base: './',
  build: {
    outDir: '..',
    emptyOutDir: false,
  },
})
