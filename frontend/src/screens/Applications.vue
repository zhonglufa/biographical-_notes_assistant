<script setup>
// U3 投递管理（V 阶段生产组件，接入真实 A09/A10/A11）。
// 产品核心：半自动确认闸门 —— 无静默自动投递；批量/单条确认均经二次确认 + 10s 撤销窗口 + 今日限额可见。
// 契约对齐：A10 applications-list.response（权威，additionalProperties:false）仅含
//   {applicationId,jobId,platformId,status,appliedAt}；A09/A11 为 pending 契约，本组件按
//   interaction-U3.md §4/§5 半自动闸门语义建模（A09 支持 confirm/revert 动作）。
//   ⚠️ 合同缺口登记：A10 列表响应当前不含 jobTitle/company，列表标题/公司由本地 mock 补全；
//     真实后端路径回退显示 jobId/platformId。该缺口见 TASK-LOG，非本组件偏离契约。
import { ref, computed, watch, onUnmounted } from 'vue'
import { Card, Button, Modal, Toast, Skeleton, EmptyState, ErrorState } from '../components/index.js'
import { api } from '../lib/api.js'

const DAILY_LIMIT = 20

// 10 态线性流（interaction-U3.md §4）；rejected/closed 为终态分支。
const FLOW = ['pending_confirm', 'autofilling', 'submitted', 'viewed', 'contacting', 'interview_invited', 'interview_done', 'offer']
const STATUS_LABEL = {
  pending_confirm: '待确认', autofilling: '填写中', submitted: '已投递', viewed: '已查看',
  contacting: '沟通中', interview_invited: '面试邀约', interview_done: '面试完成',
  offer: 'Offer', rejected: '未通过', closed: '已关闭',
}
const STATUS_COLOR = {
  pending_confirm: 'neutral', autofilling: 'neutral', submitted: 'ok', viewed: 'ok',
  contacting: 'info', interview_invited: 'accent', interview_done: 'accent',
  offer: 'ok', rejected: 'bad', closed: 'muted',
}
const CHIPS = [
  { key: 'all', label: '全部', status: null },
  { key: 'pending_confirm', label: '待确认', status: 'pending_confirm' },
  { key: 'submitted', label: '已投递', status: 'submitted' },
  { key: 'interview_invited', label: '面试邀约', status: 'interview_invited' },
  { key: 'offer', label: 'Offer', status: 'offer' },
  { key: 'rejected', label: '未通过', status: 'rejected' },
]

const fmtTime = (ts) => {
  if (!ts) return '—'
  const d = new Date(ts)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

const filter = ref('all')
const items = ref([])
const loading = ref(true)
const err = ref(null)
const selected = ref(new Set())
const detailId = ref(null)
const detail = ref(null)
const detailLoading = ref(false)
const confirmOpen = ref(false)
const pendingIds = ref([])
const toast = ref({ show: false, msg: '', undo: false })
const undoIds = ref(null)
let undoTimer = null

const chip = computed(() => CHIPS.find((c) => c.key === filter.value))

async function load() {
  loading.value = true; err.value = null
  try {
    const d = await api.applicationsList(chip.value ? chip.value.status : null)
    items.value = d.items || []
  } catch (e) { err.value = e.message || '加载失败' }
  finally { loading.value = false }
}
watch(filter, () => { selected.value = new Set(); load() }, { immediate: true })

// 今日已投递计数（appliedAt 当天且非待确认/终态）—— 限额可见红线。
const todayCount = computed(() => {
  const t0 = new Date(); t0.setHours(0, 0, 0, 0)
  return items.value.filter((it) => it.appliedAt >= t0.getTime() && !['pending_confirm', 'rejected', 'closed'].includes(it.status)).length
})
const limitReached = computed(() => todayCount.value >= DAILY_LIMIT)

function toggle(id, status) {
  if (status !== 'pending_confirm') return
  const n = new Set(selected.value)
  if (n.has(id)) n.delete(id); else n.add(id)
  selected.value = n
}

function openBatchConfirm() {
  if (selected.value.size === 0 || limitReached.value) return
  pendingIds.value = [...selected.value]
  confirmOpen.value = true
}
function openSingleConfirm(app) {
  if (app.status !== 'pending_confirm' || limitReached.value) return
  detailId.value = null; detail.value = null
  pendingIds.value = [app.applicationId]
  confirmOpen.value = true
}

async function doConfirm() {
  const ids = pendingIds.value
  confirmOpen.value = false
  try {
    await api.batchApplications(ids, 'confirm') // A09 confirm：pending_confirm → submitted
    items.value = items.value.map((it) => (ids.includes(it.applicationId) ? { ...it, status: 'submitted' } : it))
    selected.value = new Set()
    undoIds.value = ids
    toast.value = { show: true, msg: `已提交 ${ids.length} 份，本机 Agent 将在你的浏览器中执行投递`, undo: true }
    if (undoTimer) clearTimeout(undoTimer)
    undoTimer = setTimeout(() => { undoIds.value = null; toast.value = { ...toast.value, show: false } }, 10000)
  } catch (e) {
    toast.value = { show: true, msg: e.message || '提交失败', undo: false }
  }
}
async function doUndo() {
  const ids = undoIds.value
  if (undoTimer) clearTimeout(undoTimer)
  undoIds.value = null; toast.value = { ...toast.value, show: false }
  try {
    await api.batchApplications(ids, 'revert') // A09 revert：submitted → pending_confirm（10s 窗口内）
    items.value = items.value.map((it) => (ids.includes(it.applicationId) ? { ...it, status: 'pending_confirm' } : it))
  } catch (e) {
    toast.value = { show: true, msg: e.message || '撤销失败，请稍后重试', undo: false }
  }
}

function loadDetail() {
  if (!detailId.value) return
  detailLoading.value = true
  api.applicationDetail(detailId.value)
    .then((d) => { detail.value = d })
    .catch(() => { detail.value = { error: true } })
    .finally(() => { detailLoading.value = false })
}
watch(detailId, () => {
  if (!detailId.value) { detail.value = null; return }
  loadDetail()
})

const pendingApps = computed(() => items.value.filter((it) => pendingIds.value.includes(it.applicationId)))
const dist = computed(() => {
  const d = {}
  pendingApps.value.forEach((it) => { d[it.platformId] = (d[it.platformId] || 0) + 1 })
  return d
})

// 详情面板状态机可视化
const detailSteps = computed(() => {
  if (!detail.value) return []
  const st = detail.value.status
  const terminal = st === 'rejected' || st === 'closed'
  const steps = terminal ? [st] : FLOW
  const idx = FLOW.indexOf(st)
  return steps.map((s) => {
    let cls = ''
    if (terminal) cls = STATUS_COLOR[s]
    else if (s === st) cls = 'cur ' + STATUS_COLOR[s]
    else if (FLOW.indexOf(s) < idx) cls = 'done'
    const mark = cls.startsWith('done') || cls.startsWith('cur') ? '✓' : ''
    return { key: s, cls, mark, label: STATUS_LABEL[s] }
  })
})

onUnmounted(() => { if (undoTimer) clearTimeout(undoTimer) })
</script>

<template>
  <div style="max-width: 760px; margin: 0 auto; padding: 24px 16px 60px">
    <div class="u3-head">
      <h1 style="font-size: 18px; margin: 0">投递管理</h1>
      <span class="u3-limit" aria-live="polite">今日 <b>{{ todayCount }}</b> / 限额 {{ DAILY_LIMIT }}</span>
    </div>

    <div class="u3-chips" role="tablist" aria-label="投递状态筛选">
      <button
        v-for="c in CHIPS"
        :key="c.key"
        type="button"
        class="u3-chip"
        :class="{ on: filter === c.key }"
        role="tab"
        :aria-selected="filter === c.key"
        @click="filter = c.key"
      >{{ c.label }}</button>
    </div>

    <div class="u3-bar">
      <span class="u3-limit">已选 {{ selected.size }} 项</span>
      <Button variant="primary" :disabled="selected.size === 0 || limitReached" @click="openBatchConfirm">
        {{ limitReached ? '已达今日限额' : `确认选中并投递（${selected.size}）` }}
      </Button>
    </div>
    <div v-if="limitReached" class="u3-confirm-note">已达今日投递限额（{{ DAILY_LIMIT }}），明日 0 点重置。</div>

    <Skeleton v-if="loading" :lines="4" />
    <ErrorState v-else-if="err" :message="err" :on-retry="load" />
    <EmptyState v-else-if="items.length === 0" hint="该状态下暂无投递记录">
      <template #action><Button @click="filter = 'all'">查看全部</Button></template>
    </EmptyState>
    <div v-else class="u3-list">
      <div v-for="app in items" :key="app.applicationId" class="u3-row">
        <input
          class="cb"
          type="checkbox"
          :disabled="app.status !== 'pending_confirm'"
          :checked="selected.has(app.applicationId)"
          :aria-label="`选择 ${app.jobTitle || app.jobId}`"
          @change="toggle(app.applicationId, app.status)"
        />
        <div class="u3-main">
          <div class="u3-title">{{ app.jobTitle || app.jobId }}</div>
          <div class="u3-sub">{{ app.company || app.platformId }} · {{ app.platformId }}</div>
          <div class="u3-meta">{{ fmtTime(app.appliedAt) }}{{ app.status === 'pending_confirm' ? ' · 待你确认' : '' }}</div>
        </div>
        <div class="u3-right">
          <span class="u3-badge" :class="STATUS_COLOR[app.status]">{{ STATUS_LABEL[app.status] }}</span>
          <span class="u3-link" role="button" tabindex="0" @click="detailId = app.applicationId" @keydown.enter="detailId = app.applicationId">查看详情</span>
        </div>
      </div>
    </div>

    <!-- 二次确认闸门（半自动投递红线） -->
    <Modal :open="confirmOpen" title="确认投递（半自动闸门）" @cancel="confirmOpen = false" @confirm="doConfirm">
      <div>
        <p style="margin: 0 0 8px">即将提交 <b>{{ pendingIds.length }}</b> 份投递，由本机 Agent 在你的浏览器实例中执行。请确认：</p>
        <div class="u3-sm" aria-label="平台分布">
          <div class="row" v-for="([p, c], i) in Object.entries(dist)" :key="p + i"><span>{{ p }}</span><span>{{ c }} 份</span></div>
        </div>
        <p class="u3-confirm-note">提交后 10 秒内可一键撤销。</p>
      </div>
    </Modal>

    <!-- 详情面板（A11 状态机可视化） -->
    <Modal :open="!!detailId" title="投递详情" confirm-label="关闭" :hide-confirm="true" @cancel="detailId = null" @confirm="detailId = null">
      <Skeleton v-if="detailLoading" :lines="3" />
      <ErrorState v-else-if="detail && detail.error" message="详情加载失败" :on-retry="loadDetail" />
      <div v-else-if="detail">
        <div class="u3-sm">
          <div class="row"><span>岗位</span><span>{{ detail.jobTitle || detail.jobId }}</span></div>
          <div class="row"><span>公司</span><span>{{ detail.company || '—' }}</span></div>
          <div class="row"><span>平台</span><span>{{ detail.platformId }}</span></div>
          <div class="row"><span>当前状态</span><span class="u3-badge" :class="STATUS_COLOR[detail.status]">{{ STATUS_LABEL[detail.status] }}</span></div>
          <div class="row"><span>投递时间</span><span>{{ fmtTime(detail.appliedAt) }}</span></div>
        </div>
        <div class="u3-flow" aria-label="投递状态机进度">
          <div v-for="s in detailSteps" :key="s.key" class="u3-step" :class="s.cls">
            <span class="u3-dot">{{ s.mark }}</span>
            <span>{{ s.label }}</span>
          </div>
        </div>
        <div v-if="detail.status === 'pending_confirm'" style="display: flex; justify-content: flex-end">
          <Button variant="primary" @click="openSingleConfirm(detail)">确认并投递这一个</Button>
        </div>
      </div>
    </Modal>

    <Toast :show="toast.show" :message="toast.msg" :on-undo="toast.undo ? doUndo : undefined" />
  </div>
</template>

<style>
.u3-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.u3-chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.u3-chip{border:1px solid var(--c-border);background:var(--c-surface);border-radius:var(--r-full);padding:7px 14px;font-size:13px;cursor:pointer;color:var(--c-muted);min-height:36px}
.u3-chip.on{background:var(--c-accent);border-color:var(--c-accent);color:#fff;font-weight:600}
.u3-limit{font-size:13px;color:var(--c-muted)}
.u3-limit b{color:var(--c-accent)}
.u3-bar{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap}
.u3-list{display:flex;flex-direction:column;gap:10px}
.u3-row{display:flex;align-items:center;gap:12px;padding:12px;border:1px solid var(--c-border);border-radius:var(--r-md);background:var(--c-surface)}
.u3-row .cb{flex:0 0 auto;width:20px;height:20px;cursor:pointer}
.u3-main{flex:1;min-width:0}
.u3-title{font-size:15px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.u3-sub{font-size:12px;color:var(--c-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.u3-meta{font-size:12px;color:var(--c-faint);margin-top:2px}
.u3-right{flex:0 0 auto;display:flex;flex-direction:column;align-items:flex-end;gap:6px}
.u3-link{font-size:13px;color:var(--c-accent);cursor:pointer}
.u3-badge{font-size:12px;padding:3px 9px;border-radius:var(--r-full);font-weight:600;white-space:nowrap}
.u3-badge.neutral{background:var(--c-border);color:var(--c-muted)}
.u3-badge.ok{background:var(--c-ok);color:#fff}
.u3-badge.info{background:#2f80ed;color:#fff}
.u3-badge.accent{background:var(--c-accent);color:#fff}
.u3-badge.bad{background:var(--c-bad);color:#fff}
.u3-badge.muted{background:var(--c-bg);color:var(--c-faint);border:1px solid var(--c-border)}
.u3-confirm-note{font-size:12px;color:var(--c-faint);margin-top:8px}
.u3-sm{display:flex;flex-direction:column;gap:6px;font-size:13px;color:var(--c-muted);margin:6px 0}
.u3-sm .row{display:flex;justify-content:space-between;gap:12px}
.u3-flow{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
.u3-step{display:flex;flex-direction:column;align-items:center;gap:4px;font-size:11px;color:var(--c-faint);min-width:56px}
.u3-dot{width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;border:2px solid var(--c-border);background:var(--c-surface);color:var(--c-faint)}
.u3-step.done .u3-dot{background:var(--c-ok);border-color:var(--c-ok);color:#fff}
.u3-step.done{color:var(--c-ok)}
.u3-step.cur .u3-dot{border-color:var(--c-accent);box-shadow:0 0 0 3px var(--c-accent-weak);color:var(--c-accent);font-weight:700}
.u3-step.cur{color:var(--c-accent)}
.u3-step.ok .u3-dot{background:var(--c-ok);border-color:var(--c-ok);color:#fff}
.u3-step.info .u3-dot{background:#2f80ed;border-color:#2f80ed;color:#fff}
.u3-step.accent .u3-dot{background:var(--c-accent);border-color:var(--c-accent);color:#fff}
.u3-step.accent{color:var(--c-accent)}
.u3-step.bad .u3-dot{background:var(--c-bad);border-color:var(--c-bad);color:#fff}
.u3-step.bad{color:var(--c-bad)}
.u3-step.muted .u3-dot{background:var(--c-bg);border-color:var(--c-border);color:var(--c-faint)}
@media (max-width:768px){.u3-row{flex-wrap:wrap}.u3-right{flex-direction:row;width:100%;justify-content:space-between;align-items:center}}
@media (max-width:480px){.u3-title{font-size:14px}.u3-chip{padding:6px 11px;font-size:12px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
