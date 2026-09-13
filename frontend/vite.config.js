import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Sin esto Vite escucha solo en [::1] (IPv6), y el reenvío de puertos
    // de Codespaces/devcontainers va por IPv4: el navegador no alcanza el
    // servidor aunque la terminal diga que está corriendo.
    host: true,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
