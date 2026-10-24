import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Em dev, o Vite (porta 5173) repassa /api para o FastAPI (porta 8000).
// O build vai direto para api/estaticos, que o FastAPI serve em produção.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  build: {
    outDir: '../api/estaticos',
    emptyOutDir: true,
  },
})
