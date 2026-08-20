# frontend (Vue 3 + Vite) — 多阶段：node 构建 → nginx 静态托管 + 反代 /api
# 构建上下文：frontend/
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
# VITE_API_BASE 控制构建期注入的 API 根路径；默认相对 /api（由 nginx 反代到后端）
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
