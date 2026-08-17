<script setup>
// 应用壳 + 路由守卫（AuthGuard）：未登录 → Auth；已登录 → 业务路由。
// PRD §797 红线：未登录不暴露任何业务数据（仅 Auth 引导页）。
import { ref } from 'vue'
import Auth from './screens/Auth.vue'

const token = ref(localStorage.getItem('rat_access_token'))
function onLogin() {
  token.value = localStorage.getItem('rat_access_token')
}
</script>

<template>
  <Auth v-if="!token" @login="onLogin" />

  <div v-else class="app-shell" style="display: grid; grid-template-columns: 232px 1fr; min-height: 100vh">
    <aside
      class="app-side"
      style="background: var(--c-surface); border-right: 1px solid var(--c-border); padding: 16px; display: flex; flex-direction: column; gap: 6px"
    >
      <strong style="padding: 8px 10px">简历投递助手</strong>
      <router-link to="/applications" class="nav">投递管理</router-link>
      <router-link to="/resume" class="nav">简历工作台</router-link>
      <router-link to="/jobs" class="nav">岗位浏览</router-link>
      <router-link to="/strategy" class="nav">策略配置</router-link>
      <router-link to="/adapters" class="nav">平台管理</router-link>
      <router-link to="/notifications" class="nav">通知中心</router-link>
      <router-link to="/daily" class="nav">每日日报</router-link>
      <router-link to="/account" class="nav">我的</router-link>
    </aside>
    <main style="padding: 8px">
      <router-view />
    </main>
  </div>
</template>

<style>
.nav {
  padding: 9px 10px;
  border-radius: var(--r-sm);
  color: var(--c-muted);
  text-decoration: none;
  font-size: 14px;
}
.nav.router-link-exact-active,
.nav.router-link-active {
  background: var(--c-accent-weak);
  color: var(--c-accent);
  font-weight: 600;
}
</style>
