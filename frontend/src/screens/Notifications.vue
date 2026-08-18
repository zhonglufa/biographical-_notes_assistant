<script setup>
// U8 通知中心（V 阶段生产组件，接入真实 A22/A23）。
// 范式：api.notifications(A22) 拉取 → 加载(Skeleton)/数据/错误(ErrorState+重试)；
//       api.notificationWs(A23) 取得 wsUrl → 建连 → 新通知插顶 + 未读+1；断线降级轮询。
import { ref, onMounted, onUnmounted } from 'vue'
import { Card, Badge, Skeleton, EmptyState, ErrorState, Modal, Toast } from '../components/UI.js'
import { api } from '../lib/api.js'

const LV = { L0: '重要', L1: '重要', L2: '普通', L3: '营销' }
const FILTERS = ['all', 'L0', 'L1', 'L2', 'L3']
const rel = (ms) => {
  const m = Math.floor((Date.now() - ms) / 60000)
  if (m < 1) return '刚刚'
  if (m < 60) return `${m} 分钟前`
  const h = Math.floor(m / 60)
  return h < 24 ? `${h} 小时前` : `${Math.floor(h / 24)} 天前`
}
const lvColor = (lv) => `var(--c-${lv.toLowerCase()})`

const items = ref([])
const unread = ref(0)
const loading = ref(true)
const err = ref(null)
const filter = ref('all')
const confirm = ref(false)
const toast = ref({ show: false, msg: '', undo: null })
const conn = ref('live')
const lastDeleted = ref(null)
let undoTimer = null
let pollTimer = null

async function load() {
  loading.value = true; err.value = null
  try {
    const d = await api.notifications(filter.value === 'all' ? undefined : filter.value)
    items.value = d.items; unread.value = d.unread
  } catch (e) { err.value = e.message || '加载失败' }
  finally { loading.value = false }
}

function connectWs() {
  api.notificationWs().then(({ wsUrl }) => {
    const ws = new WebSocket(wsUrl)
    ws.onmessage = () => load()
    ws.onclose = () => { conn.value = 'offline'; startPoll() }
    conn.value = 'live'
  }).catch(() => { conn.value = 'offline'; startPoll() })
}
function startPoll() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(load, 30000)
}

function markRead(id) {
  items.value = items.value.map((i) => (i.id === id ? { ...i, read: true } : i))
  unread.value = Math.max(0, unread.value - 1)
}
function markAll() {
  items.value = items.value.map((i) => ({ ...i, read: true }))
  unread.value = 0; confirm.value = false
  toast.value = { show: true, msg: '已全部标记为已读' }
}
function del(id) {
  const i = items.value.findIndex((x) => x.id === id)
  if (i < 0) return
  lastDeleted.value = { item: items.value[i], index: i }
  items.value = items.value.filter((x) => x.id !== id)
  toast.value = { show: true, msg: '通知已删除', undo: () => undo() }
  clearTimeout(undoTimer)
  undoTimer = setTimeout(() => { toast.value = { ...toast.value, show: false } }, 5000)
}
function undo() {
  if (lastDeleted.value) {
    const c = [...items.value]
    c.splice(Math.min(lastDeleted.value.index, c.length), 0, lastDeleted.value.item)
    items.value = c
    lastDeleted.value = null
  }
  toast.value = { ...toast.value, show: false }
}

onMounted(() => { load(); connectWs() })
onUnmounted(() => { if (undoTimer) clearTimeout(undoTimer); if (pollTimer) clearInterval(pollTimer) })
</script>

<template>
  <div style="max-width: 760px; margin: 0 auto; padding: 24px 16px 60px">
    <div class="rui-card" style="display: flex; align-items: center; gap: 12px; margin-bottom: 14px">
      <h1 style="font-size: 18px; margin: 0; flex: 1">通知中心</h1>
      <span style="font-size: 12px; color: var(--c-muted)">{{ conn === 'live' ? '实时' : '离线(轮询)' }}</span>
      <Badge :count="unread" />
      <button class="btn" @click="confirm = true" style="min-height: 40px">全部已读</button>
    </div>

    <div style="display: flex; gap: 8px; overflow-x: auto; padding: 4px 0 12px">
      <button
        v-for="lv in FILTERS"
        :key="lv"
        @click="filter = lv"
        :style="{
          border: '1px solid var(--c-border)', background: filter === lv ? 'var(--c-accent-weak)' : 'var(--c-surface)',
          color: filter === lv ? 'var(--c-accent)' : 'var(--c-muted)', borderRadius: 'var(--r-full)',
          padding: '7px 14px', fontSize: 13, whiteSpace: 'nowrap', cursor: 'pointer', minHeight: 36,
        }"
      >{{ lv === 'all' ? '全部' : lv }}</button>
    </div>

    <Skeleton v-if="loading" :lines="3" />
    <ErrorState v-else-if="err" :message="err" :on-retry="load" />
    <EmptyState v-else-if="items.length === 0" hint="暂无通知" />
    <div v-else style="display: flex; flex-direction: column; gap: 10px">
      <div
        v-for="n in items"
        :key="n.id"
        class="rui-card"
        :style="{ position: 'relative', display: 'flex', gap: '12px', padding: '14px 14px 14px 18px', opacity: n.read ? 0.72 : 1 }"
      >
        <div :style="{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, background: lvColor(n.level) }"></div>
        <div style="flex: 1; min-width: 0">
          <div :style="{ fontWeight: n.read ? 500 : 600, display: 'flex', alignItems: 'center', gap: 8 }">
            {{ n.title }}
            <span :style="{ fontSize: 11, padding: '1px 7px', borderRadius: 'var(--r-full)', color: '#fff', background: lvColor(n.level) }">{{ LV[n.level] }}</span>
          </div>
          <div style="color: var(--c-muted); font-size: 13px; margin-top: 4px">{{ n.body }}</div>
          <div style="font-size: 12px; color: var(--c-faint); margin-top: 8px">{{ rel(n.createdAt) }} · {{ n.channel === '站内' ? '站内信' : n.channel }}</div>
        </div>
        <div style="display: flex; flex-direction: column; gap: 6px; align-items: flex-end">
          <button v-if="!n.read" class="mini" @click="markRead(n.id)" style="border: none; background: transparent; color: var(--c-muted); cursor: pointer">标已读</button>
          <button class="mini" @click="del(n.id)" style="border: none; background: transparent; color: var(--c-muted); cursor: pointer">删除</button>
        </div>
      </div>
    </div>

    <Modal
      :open="confirm"
      title="全部标记为已读？"
      body="将把未读通知设为已读，多端会同步。"
      @cancel="confirm = false"
      @confirm="markAll"
    />
    <Toast :show="toast.show" :message="toast.msg" :on-undo="toast.undo" />
  </div>
</template>
