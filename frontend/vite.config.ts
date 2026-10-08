import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// Cross-origin isolation: habilita WASM multihilo en el worker de inferencia.
// "credentialless" permite seguir cargando fuentes e imágenes de otros orígenes.
// Mantener en sincronía con vercel.json.
const aislamiento = {
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Embedder-Policy': 'credentialless',
};

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // onnxruntime-web carga sus .wasm con import.meta.url: no debe pre-empaquetarse.
  optimizeDeps: {
    exclude: ['onnxruntime-web'],
  },
  // El worker de inferencia importa onnxruntime-web (con imports dinámicos).
  worker: {
    format: 'es',
  },
  server: {
    port: 5173,
    headers: aislamiento,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    headers: aislamiento,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    target: 'es2022',
  },
});
