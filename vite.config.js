import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'node:url'

export default defineConfig({
    plugins: [
        tailwindcss(),
    ],
    build: {
        rollupOptions: {
            input: Object.fromEntries([
                'index', 'home', 'forgot-password', 'usuarios', 'inventario',
                'tarefa', 'tarefas', 'localizacoes',
            ].map(pagina => [pagina, fileURLToPath(new URL(`./${pagina}.html`, import.meta.url))])),
        },
    },
    server: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, ''),
            },
        },
    },
})
