import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(() => {
  const repo = process.env.GITHUB_REPOSITORY?.split('/')[1] ?? '';
  const isGhPagesBuild = Boolean(process.env.GITHUB_REPOSITORY);

  return {
    plugins: [react()],
    base: isGhPagesBuild && repo ? `/${repo}/` : '/',
    server: {
      port: 5173,
    },
  };
});
