<script setup>
// U2 岗位浏览（A07/A08 生产组件）。
// 交互规格：design/ui/interaction-U2.md；契约：jobs-list.response / jobs-search.request / jobs-favorite.{request,response}。
// U11 基线：加载(Skeleton) / 错误(重试) / 空态(引导放宽筛选) / Toast(含撤销) / 无障碍(aria) / 响应式 375/768/1280。
// 诚实边界：忽略(ignore)契约响应只回 status=ignored，不在 jobStub 显式标 ignored 字段→本组件维护 ignoredSet（前端态，
//   撤销忽略即从 set 移除；与 U3 已有的本地态处理对齐，不臆造后端字段）。
import { ref, computed, watch } from 'vue'
import { Card, Button, Skeleton, EmptyState, ErrorState, Toast } from '../components/UI.js'
import { api } from '../lib/api.js'

const PLAT = { boss: 'Boss直聘', liepin: '猎聘', zhaopin: '智联', '51job': '前程无忧', lagou: '拉勾' }
const PLAT_LIST = ['boss', 'liepin', 'zhaopin', '51job', 'lagou']

function bandOf(score) {
  if (score == null) return null
  if (score >= 80) return 'green'
  if (score >= 60) return 'blue'
  return 'gray'
}
function bandStyle(b) {
  if (b === 'green') return { bg: 'var(--c-ok-soft, #ECFDF3)', bd: 'var(--c-ok-bd, #ABEFC6)', fg: 'var(--c-ok, #16A34A)' }
  if (b === 'blue')  return { bg: 'var(--c-info-soft, #EFF6FF)', bd: 'var(--c-info-bd, #BFDBFE)', fg: 'var(--c-info, #2563EB)' }
  if (b === 'gray')  return { bg: 'var(--c-bg, #F1F5F9)', bd: 'var(--c-border)', fg: 'var(--c-muted)' }
  return { bg: 'var(--c-bg, #F1F5F9)', bd: 'var(--c-border)', fg: 'var(--c-faint)' }
}
function bandStyleOf(j) {
  const s = bandStyle(j.matchBand || bandOf(j.matchScore))
  return {
    flexShrink: 0, width: 56, height: 56, borderRadius: 12,
    background: s.bg, border: '1px solid ' + s.bd, color: s.fg,
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontWeight: 700,
  }
}
const fmtSalary = (j) => (j.salaryMin == null ? '薪资面议' : `${Math.round(j.salaryMin / 1000)}-${Math.round(j.salaryMax / 1000)}K`)

const items = ref(null)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const error = ref(null)
const form = ref({ keyword: '', location: '', salaryMin: '', platform: '' })
const applied = ref({ keyword: '', location: '', salaryMin: '', platform: '' })
const ignoredSet = ref(new Set())
const toast = ref({ show: false, message: '', onUndo: null })
let searchRef = 0

function flash(message, onUndo) {
  toast.value = { show: true, message, onUndo: onUndo || null }
  setTimeout(() => { toast.value = { ...toast.value, show: false } }, 2600)
}

function load(params) {
  const myReq = ++searchRef
  error.value = null
  items.value = null
  const q = {}
  if (params.keyword) q.keyword = params.keyword
  if (params.location) q.location = params.location
  if (params.platform) q.platform = params.platform
  if (params.salaryMin !== '' && params.salaryMin != null) {
    const n = parseInt(params.salaryMin, 10)
    if (!Number.isNaN(n) && n >= 0) q.salaryMin = n
  }
  api.jobsList(q).then((res) => {
    if (myReq !== searchRef) return // 过期请求丢弃
    items.value = res.items
    total.value = res.total
    page.value = res.page
  }).catch(() => { if (myReq !== searchRef) return; error.value = '岗位列表加载失败' })
}
watch(applied, (v) => load(v), { immediate: true })

const onSearch = () => {
  if (form.value.salaryMin !== '' && form.value.salaryMin != null) {
    const n = parseInt(form.value.salaryMin, 10)
    if (Number.isNaN(n) || n < 0) { flash('请输入数字（K 或元/月）'); return }
  }
  page.value = 1
  applied.value = { ...form.value }
}
const onPlatform = (pl) => {
  const next = { ...form.value, platform: pl }
  form.value = next
  page.value = 1
  applied.value = next
}
const onClear = () => {
  const empty = { keyword: '', location: '', salaryMin: '', platform: '' }
  form.value = empty
  page.value = 1
  applied.value = empty
}

const onFavorite = (job) => {
  if (ignoredSet.value.has(job.jobId)) return
  api.favoriteJob(job.jobId, 'favorite').then((res) => {
    if (res && res.ok) {
      items.value = items.value.map((j) => (j.jobId === job.jobId ? { ...j, favorited: true } : j))
      flash('已收藏，已送入「待确认投递」')
    } else flash('收藏失败，请重试')
  }).catch(() => flash('收藏失败，请重试'))
}
const onUnfavorite = (job) => {
  api.favoriteJob(job.jobId, 'favorite').then(() => {
    items.value = items.value.map((j) => (j.jobId === job.jobId ? { ...j, favorited: false } : j))
    flash('已取消收藏')
  }).catch(() => flash('操作失败，请重试'))
}
const onIgnore = (job) => {
  api.favoriteJob(job.jobId, 'ignore').then((res) => {
    if (res && res.ok) {
      const next = new Set(ignoredSet.value); next.add(job.jobId)
      ignoredSet.value = next
      flash('已忽略，不再推送该岗位', () => {
        const r = new Set(next); r.delete(job.jobId)
        ignoredSet.value = r
        flash('已撤销忽略')
      })
    } else flash('忽略失败，请重试')
  }).catch(() => flash('忽略失败，请重试'))
}
const undoIgnore = (jobId) => {
  const next = new Set(ignoredSet.value); next.delete(jobId)
  ignoredSet.value = next
  flash('已撤销忽略')
}
const onDetail = (job) => { flash(`打开岗位详情：${job.title}（mock）`) }

const maxPage = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const goto = (p) => { if (p < 1 || p > maxPage.value) return; page.value = p; load({ ...applied.value, page: p, pageSize }) }

const inputStyle = {
  minWidth: '180px', padding: '9px 12px', borderRadius: 'var(--r-md)', border: '1px solid var(--c-border)', fontSize: 14, background: 'var(--c-surface)',
}
function chipStyle(on) {
  return {
    fontSize: 13, padding: '6px 12px', borderRadius: 'var(--r-full)',
    border: '1px solid ' + (on ? 'var(--c-accent)' : 'var(--c-border)'),
    background: on ? 'var(--c-accent-weak, #EEF2FF)' : 'var(--c-surface)',
    color: on ? 'var(--c-accent)' : 'var(--c-body)',
    fontWeight: on ? 600 : 400, cursor: 'pointer', minHeight: 32,
  }
}
</script>

<template>
  <div style="max-width: 1080px; margin: 0 auto; padding: 12px 8px">
    <div style="margin-bottom: 10px">
      <h2 style="margin: 0; font-size: 18px">岗位浏览</h2>
      <div style="font-size: 12px; color: var(--c-muted); margin-top: 2px">搜索 / 筛选招聘平台岗位，按 AI 匹配度排序；收藏送入待确认投递，忽略后不再推送。</div>
    </div>

    <!-- 筛选条（A07 查询参数：keyword/location/salaryMin） -->
    <Card style="padding: 12px; margin-bottom: 10px">
      <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center">
        <input aria-label="关键词" placeholder="关键词：Java / 后端 / 微服务" v-model="form.keyword" @keydown.enter="onSearch" :style="inputStyle" />
        <input aria-label="城市" placeholder="城市：上海" v-model="form.location" @keydown.enter="onSearch" :style="{ ...inputStyle, minWidth: 120 }" />
        <input aria-label="月薪下限" placeholder="月薪下限(元)" inputmode="numeric" v-model="form.salaryMin" @keydown.enter="onSearch" :style="{ ...inputStyle, width: 130 }" />
        <Button variant="primary" @click="onSearch">搜索</Button>
        <Button @click="onClear">清空</Button>
        <span style="margin-left: auto; color: var(--c-muted); font-size: 13px">共 {{ total }} 个岗位</span>
      </div>
      <div style="margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; align-items: center">
        <span style="font-size: 13px; color: var(--c-muted)">平台：</span>
        <button :style="chipStyle(form.platform === '')" @click="onPlatform('')">全部</button>
        <button v-for="pl in PLAT_LIST" :key="pl" :style="chipStyle(form.platform === pl)" @click="onPlatform(pl)">{{ PLAT[pl] }}</button>
      </div>
    </Card>

    <!-- 岗位列表 -->
    <ErrorState v-if="error" :message="error" :on-retry="() => load(applied)" />
    <div v-else-if="items === null" style="padding: 16px"><Skeleton :lines="4" /></div>
    <EmptyState v-else-if="items.length === 0" hint="没有匹配的岗位。试试放宽筛选条件，或去「简历工作台」更新偏好。" />
    <div v-else style="display: flex; flex-direction: column; gap: 10px">
      <Card v-for="j in items" :key="j.jobId" :style="{ padding: 14, opacity: ignoredSet.has(j.jobId) ? 0.55 : 1 }">
        <div style="display: flex; gap: 14px; align-items: flex-start; flex-wrap: wrap">
          <!-- 匹配度环（matchBand 着色） -->
          <div aria-label="AI 匹配度" :style="bandStyleOf(j)">
            <div style="font-size: 16px; line-height: 1">{{ j.matchScore == null ? '—' : j.matchScore }}</div>
            <div style="font-size: 10px; font-weight: 500; color: var(--c-muted)">匹配</div>
          </div>
          <!-- 信息 -->
          <div style="flex: 1; min-width: 200px">
            <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap">
              <strong style="font-size: 15px; color: var(--c-strong)">{{ j.title }}</strong>
              <span v-if="j.favorited" style="font-size: 11px; background: var(--c-accent); color: #fff; border-radius: var(--r-full); padding: 1px 8px">已收藏</span>
              <span v-if="ignoredSet.has(j.jobId)" :style="{ fontSize: '11px', background: 'var(--c-bg)', color: 'var(--c-muted)', border: '1px solid var(--c-border)', borderRadius: 'var(--r-full)', padding: '1px 8px' }">已忽略</span>
            </div>
            <div style="font-size: 13px; color: var(--c-muted); margin: 4px 0">
              {{ j.company }} · {{ PLAT[j.platformId] || j.platformId }} · {{ j.location || '—' }} · {{ fmtSalary(j) }} · {{ j.source === 'detail' ? '详情采集' : '搜索采集' }}
            </div>
            <div :style="{ fontSize: '13px', color: 'var(--c-body)', background: 'var(--c-bg)', borderRadius: 'var(--r-sm)', padding: '8px 10px' }">
              匹配理由：<b style="color: var(--c-accent)">{{ j.matchReason || '—' }}</b>
            </div>
          </div>
          <!-- 操作 -->
          <div style="display: flex; flex-direction: column; gap: 6px; align-items: flex-end; flex-shrink: 0; min-width: 100px">
            <template v-if="ignoredSet.has(j.jobId)">
              <Button style="font-size: 13px; padding: 6px 12px; min-height: 32px" @click="undoIgnore(j.jobId)">撤销忽略</Button>
            </template>
            <template v-else-if="j.favorited">
              <Button style="font-size: 13px; padding: 6px 12px; min-height: 32px" @click="onUnfavorite(j)">取消收藏</Button>
            </template>
            <template v-else>
              <Button variant="primary" style="font-size: 13px; padding: 6px 12px; min-height: 32px" @click="onFavorite(j)">收藏 →</Button>
            </template>
            <Button v-if="!ignoredSet.has(j.jobId)" style="font-size: 13px; padding: 6px 12px; min-height: 32px" @click="onIgnore(j)">忽略</Button>
            <Button style="font-size: 13px; padding: 6px 12px; min-height: 32px" @click="onDetail(j)">详情</Button>
          </div>
        </div>
      </Card>
    </div>

    <!-- 分页器 -->
    <div v-if="total > pageSize" style="display: flex; gap: 8px; align-items: center; justify-content: center; margin: 16px 0; color: var(--c-muted); font-size: 13px">
      <span>第 {{ page }} / {{ maxPage }} 页</span>
      <Button :disabled="page <= 1" @click="goto(page - 1)" style="font-size: 13px; padding: 6px 12px; min-height: 32px">上一页</Button>
      <Button :disabled="page >= maxPage" @click="goto(page + 1)" style="font-size: 13px; padding: 6px 12px; min-height: 32px">下一页</Button>
    </div>

    <Toast :show="toast.show" :message="toast.msg" :on-undo="toast.onUndo" />
  </div>
</template>
