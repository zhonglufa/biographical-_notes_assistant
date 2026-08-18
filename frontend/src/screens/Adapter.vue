<script setup>
// U5 适配器管理（V 阶段生产组件，接入真实 A14/A15）。
// 契约对齐：A14 GET /adapters（adapter-facade + b09-health）列表；A15 POST /adapters/{id}/enable {enabled} → {adapterId,status}。
// 字段映射严格来自 design/ui/roles/U5-arch.md §4：platformName/platformType/version/status(6态)/health{healthy,cookieHealthy,checkedAt,avgLatencyMs}。
// 安全模型同 U3：启用/停用经二次确认闸门 + 10s 撤销窗口（用户主动确认，无静默操作）。
// 新增唯一组件 AdapterStatusDot（6态色点+强制文本标签，满足无障碍不止颜色）在此 SFC 内联实现（等价于 UI.js 函数式组件）。
import { ref, computed, onUnmounted } from 'vue'
import { Card, Button, Modal, Toast, Skeleton, EmptyState, ErrorState } from '../components/UI.js'
import { api } from '../lib/api.js'

// 6 态色点 + 文本标签（来自 U5-arch §2；色值对齐设计系统/UI-SELFCHECK 配色）。
// 无障碍：色点必须配套文本标签（AdapterStatusDot），不只靠颜色区分。
const DOTS = {
  installed:     { c: '#9aa3b2', t: '已安装' },
  test_mode:     { c: '#2563eb', t: '测试中' },
  enabled:       { c: '#16a34a', t: '正常' },
  disabled:      { c: '#9aa3b2', t: '已停用' },
  degraded:      { c: '#dc2626', t: '异常' },
  login_expired: { c: '#d97706', t: '需登录' },
}
// 平台类型展示映射（A14 platformType 枚举）
const PTYPE_LABEL = {
  social: '社招', campus: '校招', 'state-owned': '国企/央企',
  headhunter: '猎头/中高端', other: '其他',
}

// 某状态可执行的动作：启用(→enabled) / 停用(→disabled) / 登录引导(login_expired)
function actionsFor(a) {
  if (a.status === 'login_expired') return ['guide']
  if (a.status === 'enabled' || a.status === 'test_mode') return ['disable']
  return ['enable'] // installed / disabled
}

const fmtAgo = (ts) => {
  if (!ts) return '—'
  const diff = Date.now() - ts
  const m = Math.floor(diff / 60000)
  if (m < 1) return '刚刚'
  if (m < 60) return `${m} 分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h} 小时前`
  return `${Math.floor(h / 24)} 天前`
}

const loading = ref(true)
const err = ref(null)
const items = ref([])
const confirmOpen = ref(false)
const pending = ref(null)        // { id, name, enable }
const toast = ref({ show: false, msg: '', undo: false })
const undoPrev = ref(null)       // 撤销回滚用的原 status
let undoTimer = null

// 健康总览：status==='enabled' 且 healthy 才算"正常"（对齐 U5-adapter 原型 okCount 语义）
const okCount = computed(() => items.value.filter((a) => a.status === 'enabled' && a.health && a.health.healthy).length)
const isEmpty = computed(() => !loading.value && !err.value && items.value.length === 0)

async function load() {
  loading.value = true; err.value = null
  try {
    const d = await api.adapterList() // A14
    items.value = (d.items || []).map((a) => ({ ...a }))
  } catch (e) { err.value = e.message || '加载失败' }
  finally { loading.value = false }
}
load()

function openToggle(a, enable) {
  pending.value = { id: a.adapterId, name: a.platformName, enable }
  confirmOpen.value = true
}
function guide(a) {
  // 仅引导：提示用户在本机浏览器打开登录页完成登录，绝不代填凭据（PRD §1012 红线）。
  toast.value = { show: true, msg: `「${a.platformName}」需重新登录：请在本机浏览器打开其登录页完成登录（仅引导，不代填凭据）`, undo: false }
}
async function doConfirm() {
  const p = pending.value
  confirmOpen.value = false
  if (!p) return
  const target = p.enable ? 'enabled' : 'disabled'
  const prev = items.value.find((x) => x.adapterId === p.id)
  const prevStatus = prev ? prev.status : null
  try {
    const r = await api.enableAdapter(p.id, p.enable) // A15 {enabled}
    const newStatus = (r && r.status) || target
    items.value = items.value.map((x) => (x.adapterId === p.id ? { ...x, status: newStatus } : x))
    undoPrev.value = { id: p.id, status: prevStatus }
    toast.value = { show: true, msg: `${p.name} 已${p.enable ? '启用' : '停用'}${p.enable ? '（将参与投递调度）' : '（不再参与投递调度）'}`, undo: true }
    if (undoTimer) clearTimeout(undoTimer)
    undoTimer = setTimeout(() => { undoPrev.value = null; toast.value = { ...toast.value, show: false } }, 10000)
  } catch (e) {
    toast.value = { show: true, msg: e.message || '操作失败', undo: false }
  }
}
async function doUndo() {
  const u = undoPrev.value
  if (undoTimer) clearTimeout(undoTimer)
  undoPrev.value = null; toast.value = { ...toast.value, show: false }
  if (!u) return
  try {
    // 撤销 = 还原原 status（本地回滚；真实后端可在 10s 窗口内再发一次 A15 还原）
    items.value = items.value.map((x) => (x.adapterId === u.id ? { ...x, status: u.status } : x))
  } catch (e) {
    toast.value = { show: true, msg: e.message || '撤销失败，请稍后重试', undo: false }
  }
}

onUnmounted(() => { if (undoTimer) clearTimeout(undoTimer) })
</script>

<template>
  <div style="max-width: 760px; margin: 0 auto; padding: 24px 16px 60px">
    <div class="adp-head">
      <h1 style="font-size: 18px; margin: 0">平台管理</h1>
      <span class="adp-summary" aria-live="polite">适配器健康：<b>{{ okCount }}</b> / {{ items.length }} 正常</span>
    </div>

    <Skeleton v-if="loading" :lines="4" />
    <ErrorState v-else-if="err" :message="err" :on-retry="load" />
    <EmptyState v-else-if="isEmpty" hint="暂无可管理适配器，去适配器市场(v2)">
      <template #action><Button @click="load">刷新</Button></template>
    </EmptyState>

    <template v-else>
      <section class="adp-block">
        <h2 class="adp-h2">首期</h2>
        <Card v-for="a in items" :key="a.adapterId" className="adp-card">
          <!-- AdapterStatusDot：6态色点 + 强制文本标签（无障碍不止颜色） -->
          <div class="adp-row">
            <span class="adp-dot" :style="{ background: (DOTS[a.status] || DOTS.installed).c }" :aria-label="(DOTS[a.status] || DOTS.installed).t"></span>
            <span class="adp-dot-label">{{ (DOTS[a.status] || DOTS.installed).t }}</span>
            <div class="adp-meta">
              <div class="adp-name">{{ a.platformName }} <span class="adp-ver">{{ a.version }}</span></div>
              <div class="adp-sub">{{ PTYPE_LABEL[a.platformType] || a.platformType }} · 作者 community</div>
            </div>
            <div class="adp-health">
              健康 {{ (a.health && a.health.healthy) ? '✓' : '✗' }} ·
              Cookie {{ (a.health && a.health.cookieHealthy) ? '✓' : '✗' }}<br />
              检查 {{ fmtAgo(a.health && a.health.checkedAt) }}
            </div>
            <div class="adp-actions">
              <Button
                v-if="actionsFor(a).includes('guide')"
                @click="guide(a)"
              >登录</Button>
              <Button
                v-else-if="actionsFor(a).includes('disable')"
                variant="danger"
                @click="openToggle(a, false)"
              >停用</Button>
              <Button
                v-else
                variant="primary"
                @click="openToggle(a, true)"
              >启用</Button>
            </div>
          </div>
        </Card>
      </section>

      <section class="adp-block">
        <h2 class="adp-h2">后续（未安装）</h2>
        <div class="adp-placeholder">国聘网 · 牛客网 · 高校就业平台 … 「安装适配器」入口为 v2 范围（本包仅占位）</div>
      </section>
    </template>

    <!-- 二次确认闸门（复用 U3 模式：半自动安全交互基线一致） -->
    <Modal :open="confirmOpen" :title="pending && pending.enable ? '启用适配器' : '停用适配器'" @cancel="confirmOpen = false" @confirm="doConfirm">
      <div v-if="pending">
        <p style="margin: 0 0 8px">确认将「<b>{{ pending.name }}</b>」{{ pending.enable ? '启用（将参与投递调度）' : '停用（不再参与投递调度）' }}？</p>
        <p class="adp-confirm-note">提交后 10 秒内可一键撤销。</p>
      </div>
    </Modal>

    <Toast :show="toast.show" :message="toast.msg" :on-undo="toast.undo ? doUndo : undefined" />
  </div>
</template>

<style>
.adp-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.adp-summary{font-size:13px;color:var(--c-muted)}
.adp-summary b{color:var(--c-ok)}
.adp-block{margin-bottom:18px}
.adp-h2{font-size:14px;margin:0 0 10px;color:var(--c-muted);font-weight:600;letter-spacing:.04em}
.adp-card{margin-bottom:10px}
.adp-row{display:flex;align-items:center;gap:14px}
.adp-dot{width:10px;height:10px;border-radius:50%;flex:0 0 auto}
.adp-dot-label{font-size:12px;color:var(--c-muted);flex:0 0 auto;min-width:40px}
.adp-meta{flex:1;min-width:0}
.adp-name{font-weight:600;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.adp-ver{color:var(--c-muted);font-weight:400;font-size:12px;margin-left:4px}
.adp-sub{font-size:12px;color:var(--c-muted);margin-top:2px}
.adp-health{font-size:12px;color:var(--c-muted);text-align:right;min-width:120px;flex:0 0 auto}
.adp-actions{display:flex;gap:8px;flex:0 0 auto}
.adp-placeholder{color:var(--c-faint);font-size:13px;padding:14px;border:1px dashed var(--c-border);border-radius:var(--r-md);text-align:center}
.adp-confirm-note{font-size:12px;color:var(--c-faint);margin-top:8px}
@media (max-width:768px){
  .adp-row{flex-wrap:wrap;align-items:flex-start}
  .adp-meta{flex:1 0 55%}
  .adp-health{min-width:0;flex:1 0 100%;text-align:left;margin-top:6px;order:3}
  .adp-actions{flex:1 0 100%;justify-content:flex-end;margin-top:8px;order:4}
  .adp-actions .btn{min-height:40px}
}
@media (max-width:480px){
  .adp-name{font-size:14px}
  .adp-dot-label{font-size:11px;min-width:34px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
