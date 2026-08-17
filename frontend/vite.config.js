import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// V 阶段前端工程配置（Vue 3 栈，遵守 ADR-010）。
// 本地开发：VITE_API_BASE 指向 scaffold 后端（或 mock 网关）；生产由 CI 注入。
// 注意：本文件不硬编码任何密钥/凭据；令牌仅存 localStorage（本机），符合 PRD §1012。
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // 开发期将 /api 代理到本地 scaffold 服务（若存在），避免跨域与硬编码后端地址。
      '/api': { target: process.env.VITE_API_TARGET || 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: { outDir: 'dist', sourcemap: true },
  test: { environment: 'jsdom', globals: true },
});
