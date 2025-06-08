import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['acarelia.com', '.acarelia.com'],
    proxy: {
      '/api': {
        target: 'http://31.58.91.32:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});