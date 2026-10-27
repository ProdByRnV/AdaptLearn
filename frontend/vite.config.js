import path from 'node:path'
import { fileURLToPath } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const root = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(root, 'src'),
    },
  },
  build: {
    rolldownOptions: {
      output: {
        // React and the router change far less often than app code, so they get their own
        // long-cached chunk. Other libraries share a second one. The knowledge graph's canvas
        // library and its d3 dependencies get a third, only loaded by the graph page; it ranks
        // below React so that React (a dependency of the graph library) isn't pulled into it.
        codeSplitting: {
          groups: [
            { name: 'react', test: /node_modules[\\/](react|react-dom|react-router|scheduler)[\\/]/, priority: 3 },
            {
              name: 'graph',
              test: /node_modules[\\/](react-force-graph-2d|force-graph|react-kapsule|kapsule|d3-[^\\/]+|@tweenjs|accessor-fn|bezier-js|canvas-color-tracker|float-tooltip|index-array-by|internmap|jerrypick|lodash-es|preact|tinycolor2)[\\/]/,
              priority: 2,
            },
            { name: 'vendor', test: /node_modules[\\/]/, priority: 1 },
          ],
        },
      },
    },
  },
  server: {
    // The backend's CORS allow-list contains http://localhost:5173 (FRONTEND_URL).
    port: 5173,
    strictPort: true,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    // Reset vi.fn() implementations and restore spies between tests.
    mockReset: true,
    restoreMocks: true,
  },
})
