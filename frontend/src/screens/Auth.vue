<script setup>
// U10 用户与登录（V 阶段生产组件，接入真实 A01/A02/A03）。
// 红线：未登录仅展示引导页，不暴露业务数据（PRD §797）；令牌仅存本机 localStorage（§1012）。
import { ref } from 'vue'
import { Card, Button } from '../components/UI.js'
import { api } from '../lib/api.js'

const emit = defineEmits(['login'])

const channel = ref('email')
const email = ref('')
const pwd = ref('')
const code = ref('')
const err = ref('')

const channels = [
  { key: 'email', label: '邮箱密码' },
  { key: 'sms', label: '邮箱验证码' },
  { key: 'wechat', label: '微信扫码' },
]

const inp = {
  width: '100%', border: '1px solid var(--c-border)', borderRadius: 'var(--r-md)',
  padding: '11px 12px', fontSize: '15px', minHeight: '44px',
}

async function submit() {
  err.value = ''
  try {
    const creds = channel.value === 'email'
      ? { email: email.value, password: pwd.value }
      : { email: email.value, code: code.value }
    const d = await api.login(channel.value, creds, 'dev-' + Math.random().toString(36).slice(2, 10))
    localStorage.setItem('rat_access_token', d.accessToken)
    localStorage.setItem('rat_refresh_token', d.refreshToken)
    emit('login', d)
  } catch (e) {
    err.value = e.message || '登录失败'
  }
}
</script>

<template>
  <div style="max-width: 480px; margin: 0 auto; padding: 24px 16px 60px">
    <div style="text-align: center; padding: 24px 0 8px">
      <div style="width: 56px; height: 56px; border-radius: 16px; background: linear-gradient(135deg, var(--c-accent), #7aa2ff); margin: 0 auto 12px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 24px; font-weight: 700">投</div>
      <h1 style="font-size: 20px; margin: 0 0 6px">简历投递助手</h1>
      <p style="color: var(--c-muted); font-size: 14px; margin: 0">AI 匹配岗位 · 半自动投递 · 每日日报</p>
    </div>
    <Card>
      <div style="display: flex; gap: 6px; background: var(--c-bg); border-radius: var(--r-md); padding: 4px; margin-bottom: 16px">
        <button
          v-for="ch in channels"
          :key="ch.key"
          @click="channel = ch.key; err = ''"
          :style="{
            flex: 1, textAlign: 'center', padding: 9, borderRadius: 'var(--r-sm)', fontSize: 13, cursor: 'pointer',
            border: 'none', background: channel === ch.key ? 'var(--c-surface)' : 'transparent',
            color: channel === ch.key ? 'var(--c-accent)' : 'var(--c-muted)', fontWeight: channel === ch.key ? 600 : 400,
          }"
        >{{ ch.label }}</button>
      </div>

      <div style="margin-bottom: 12px">
        <label style="display: block; font-size: 13px; color: var(--c-muted); margin-bottom: 6px">邮箱</label>
        <input class="input" v-model="email" placeholder="you@example.com" :style="inp" />
      </div>

      <div v-if="channel === 'email'" style="margin-bottom: 12px">
        <label style="display: block; font-size: 13px; color: var(--c-muted); margin-bottom: 6px">密码</label>
        <input class="input" type="password" v-model="pwd" placeholder="••••••••" :style="inp" />
      </div>
      <div v-else-if="channel === 'sms'" style="margin-bottom: 12px">
        <label style="display: block; font-size: 13px; color: var(--c-muted); margin-bottom: 6px">验证码</label>
        <input class="input" v-model="code" placeholder="6 位验证码" :style="inp" />
      </div>
      <div v-else style="border: 1px solid var(--c-border); border-radius: var(--r-md); padding: 24px; text-align: center; color: var(--c-faint); margin-bottom: 12px">微信扫码登录（失败时回退邮箱）</div>

      <div class="err" role="alert" aria-live="polite" style="color: var(--c-bad); font-size: 13px; margin-bottom: 8px">{{ err }}</div>
      <Button variant="primary" @click="submit" style="width: 100%">登录</Button>
      <div style="font-size: 12px; color: var(--c-faint); margin-top: 10px; text-align: center">未登录时仅展示本引导页，不暴露任何业务数据</div>
    </Card>
  </div>
</template>
