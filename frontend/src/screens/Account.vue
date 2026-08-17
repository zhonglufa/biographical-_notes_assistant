<script setup>
// U10 我的（账户）页：套餐/额度/本机登录态展示 + 退出清本机凭据。
// 红线：令牌仅存本机 localStorage（PRD §1012），退出即清除并重载。
import { ref, onMounted } from 'vue'
import { api } from '../lib/api.js'
import { Card, Toggle } from '../components/index.js'

const me = ref(null)
onMounted(() => {
  api.me().then((m) => { me.value = m }).catch(() => {})
})

function logout() {
  localStorage.removeItem('rat_access_token')
  localStorage.removeItem('rat_refresh_token')
  window.location.reload()
}
</script>

<template>
  <div v-if="!me" style="padding: 24px">加载账户…</div>
  <div v-else style="max-width: 480px; margin: 0 auto; padding: 24px 16px">
    <Card>
      <div style="display: flex; justify-content: space-between; background: var(--c-accent-weak); border-radius: var(--r-md); padding: 14px; margin-bottom: 14px">
        <div>
          <div style="font-weight: 700; color: var(--c-accent)">{{ me.plan }} 版</div>
          <div style="font-size: 12px; color: var(--c-muted)">解锁 100 份/天</div>
        </div>
        <span style="font-size: 12px; background: var(--c-accent); color: #fff; border-radius: var(--r-full); padding: 2px 10px">当前套餐</span>
      </div>

      <div style="margin-bottom: 14px">
        <div style="display: flex; justify-content: space-between; font-size: 13px; color: var(--c-muted); margin-bottom: 6px">
          <span>今日套餐额度</span>
          <span>{{ me.quotaUsed }} / {{ me.quotaLimit || '不限' }}</span>
        </div>
        <div style="height: 10px; background: var(--c-bg); border-radius: var(--r-full); overflow: hidden">
          <div :style="{ height: '100%', width: me.quotaLimit ? (me.quotaUsed / me.quotaLimit * 100) + '%' : '0%', background: 'var(--c-accent)' }"></div>
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; padding: 13px 0; border-bottom: 1px solid var(--c-border); font-size: 14px">
        邮箱 <span style="color: var(--c-muted)">{{ me.email || '—' }}</span>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; padding: 13px 0; font-size: 14px">
        本机 Agent 登录态（Cookie 仅存本机）
        <Toggle :on="true" @change="() => {}" />
      </div>

      <div style="margin-top: 18px; color: var(--c-bad); cursor: pointer; text-align: right" @click="logout">
        退出并清除本机凭据 ›
      </div>
    </Card>
  </div>
</template>
