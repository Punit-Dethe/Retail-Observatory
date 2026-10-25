import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'retail-fixed-presets',
      transformIndexHtml() {
        const source = readFileSync(new URL('./src/data/retail-presets.json', import.meta.url), 'utf8')
        // Keep the fixed values as inert JSON, not a large JavaScript source literal.
        // Escaping every "<" prevents any source description closing this script tag.
        const serialized = JSON.stringify(JSON.parse(source)).replace(/</g, '\\u003c')
        return [{ tag: 'script', attrs: { type: 'application/json', id: 'retail-presets' }, children: serialized, injectTo: 'head' }]
      },
    },
  ],
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:8000' } },
  preview: { port: 4173, proxy: { '/api': 'http://127.0.0.1:8000' } },
})
