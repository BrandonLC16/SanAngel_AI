import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'

const certFile = process.env.ADMIN_DEV_TLS_CERT_FILE
const keyFile = process.env.ADMIN_DEV_TLS_KEY_FILE
if (Boolean(certFile) !== Boolean(keyFile)) {
  throw new Error('Both local TLS certificate paths are required')
}
const https = certFile && keyFile
  ? { cert: readFileSync(certFile), key: readFileSync(keyFile) }
  : undefined

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    https,
    proxy: {
      '/api': {
        target: 'https://127.0.0.1:8000',
        changeOrigin: true,
        secure: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    environmentOptions: { jsdom: { url: 'https://localhost/' } },
  },
})
