<script setup>
// U9 每日日报（V 阶段生产组件，接入真实 A24/A25）。
// 范式：api.dailyReport(A24) 拉取 → 加载(Skeleton)/数据/错误(ErrorState+重试)/空态(无活动)；
//       api.saveDailyPref(A25) 保存偏好 → loading + Toast 反馈；非法时间前端拦截不请求。
// 交互基线遵循 U11 总纲（加载/错误/空态/无障碍）；响应式 375/768/1280 见下方 <style>。
import { ref, computed, onMounted } from 'vue'
import { Card, Button, Toggle, Skeleton, EmptyState, ErrorState, Toast } from '../components/index.js'
import { api } from '../lib/api.js'

const report = ref(null)
const pref = ref({ pushTime: '20:00', enabled: true })
const loading = ref(true)
const err = ref(null)
const saving = ref(false)
const toast = ref({ show: false, msg: '' })

async function load() {
  loading.value = true; err.value = null
  try {
    const d = await api.dailyReport() // A24
    report.value = d
  } catch (e) { err.value = e.message || '加载失败' }
  finally { loading.value = false }
}
onMounted(load)

const stats = computed(() => report.value && report.value.stats)
const total = computed(() => (stats.value && stats.value.byPlatform) ? stats.value.byPlatform.reduce((s, p) => s + p.count, 0) : 0)
const maxTrend = computed(() => (stats.value && stats.value.trend7d && stats.value.trend7d.length) ? Math.max(...stats.value.trend7d.map((t) => t.count)) : 0)
const noActivity = computed(() => report.value && ((stats.value && stats.value.appliedTotal) || 0) === 0 && (!stats.value || !stats.value.byPlatform || stats.value.byPlatform.length === 0))

const statCards = computed(() => {
  if (!stats.value) return []
  return [
    { n: stats.value.appliedTotal, l: '今日投递总数', cls: 'acc' },
    { n: stats.value.success, l: '成功', cls: 'ok' },
    { n: stats.value.failed, l: '失败', cls: 'bad' },
    { n: stats.value.hrViews, l: 'HR 查看', cls: '' },
    { n: stats.value.interviewInvites, l: '面试邀请', cls: '' },
    { n: stats.value.newQuestions, l: '新增面试题', cls: '' },
  ]
})

async function save() {
  if (!/^\d{2}:\d{2}$/.test(pref.value.pushTime)) { toast.value = { show: true, msg: '时间格式不正确' }; return }
  saving.value = true
  try {
    await api.saveDailyPref(pref.value.pushTime, pref.value.enabled) // A25
    toast.value = { show: true, msg: `已保存：推送 ${pref.value.pushTime}，${pref.value.enabled ? '开启' : '关闭'}` }
  } catch (e) { toast.value = { show: true, msg: e.message || '保存失败' } }
  finally {
    saving.value = false
    setTimeout(() => { toast.value = { ...toast.value, show: false } }, 2400)
  }
}
</script>

<template>
  <div style="max-width: 760px; margin: 0 auto; padding: 24px 16px 60px">
    <h1 style="font-size: 18px; margin: 0 0 14px">每日日报</h1>

    <Skeleton v-if="loading" :lines="3" />
    <ErrorState v-else-if="err" :message="err" :on-retry="load" />
    <EmptyState v-else-if="noActivity" hint="今日无投递活动 · 系统不会发送空日报" />
    <template v-else>
      <Card>
        <div style="font-size: 14px; color: var(--c-muted); margin-bottom: 10px">{{ report.summary }}</div>
        <div class="u9-grid">
          <div v-for="(s, i) in statCards" :key="i" class="u9-stat" :class="s.cls" :aria-label="`${s.l}：${s.n}`">
            <div class="n">{{ s.n }}</div><div class="l">{{ s.l }}</div>
          </div>
        </div>
      </Card>

      <Card>
        <h2 style="font-size: 16px; margin: 0 0 12px">各平台投递分布</h2>
        <div class="u9-bars">
          <div v-for="p in stats.byPlatform" :key="p.platformId" class="u9-bar-row">
            <span class="nm">{{ p.platformId }}</span>
            <span class="track"><span class="fill" :style="{ width: `${total ? Math.round(p.count / total * 100) : 0}%` }"></span></span>
            <span class="ct">{{ p.count }}</span>
          </div>
        </div>
      </Card>

      <Card>
        <h2 style="font-size: 16px; margin: 0 0 12px">近 7 天趋势</h2>
        <div class="u9-trend">
          <div v-for="(t, i) in stats.trend7d" :key="t.date" class="u9-col">
            <div class="u9-bar" :class="{ t: i === stats.trend7d.length - 1 }" :style="{ height: `${maxTrend ? Math.round(t.count / maxTrend * 80) : 0}px` }"></div>
            <div class="day">{{ t.date.slice(3) }}</div>
          </div>
        </div>
        <!-- 无障碍（U11 §6）：图表附数据表供读屏 -->
        <table class="u9-tbl"><thead><tr><th>日期</th><th>投递量</th></tr></thead><tbody>
          <tr v-for="t in stats.trend7d" :key="t.date"><td>{{ t.date }}</td><td>{{ t.count }}</td></tr>
        </tbody></table>
      </Card>

      <Card>
        <h2 style="font-size: 16px; margin: 0 0 12px">日报推送设置（A25）</h2>
        <div class="u9-pref">
          <div><div class="lab">推送时间</div><div class="sub">默认 20:00，日报准时送达</div></div>
          <input class="u9-time" type="time" v-model="pref.pushTime" aria-label="日报推送时间" />
        </div>
        <div class="u9-pref">
          <div><div class="lab">开启日报推送</div><div class="sub">{{ pref.enabled ? '开启后每日推送投递日报' : '已关闭日报推送' }}</div></div>
          <Toggle :on="pref.enabled" @change="(v) => pref.enabled = v" />
        </div>
        <div style="display: flex; justify-content: flex-end; margin-top: 12px">
          <Button variant="primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存设置' }}</Button>
        </div>
      </Card>
    </template>

    <Toast :show="toast.show" :message="toast.msg" />
  </div>
</template>

<style>
.u9-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:6px}
.u9-stat{background:var(--c-bg);border-radius:var(--r-md);padding:14px}
.u9-stat .n{font-size:24px;font-weight:700}
.u9-stat .l{font-size:12px;color:var(--c-muted);margin-top:2px}
.u9-stat.ok .n{color:var(--c-ok)} .u9-stat.bad .n{color:var(--c-bad)} .u9-stat.acc .n{color:var(--c-accent)}
.u9-bars{display:flex;flex-direction:column;gap:8px;margin-top:6px}
.u9-bar-row{display:flex;align-items:center;gap:10px;font-size:13px}
.u9-bar-row .nm{width:88px;color:var(--c-muted)}
.u9-bar-row .track{flex:1;height:10px;background:var(--c-bg);border-radius:var(--r-full);overflow:hidden}
.u9-bar-row .fill{display:block;height:100%;background:var(--c-accent);border-radius:var(--r-full)}
.u9-bar-row .ct{width:34px;text-align:right;color:var(--c-faint)}
.u9-trend{display:flex;align-items:flex-end;gap:8px;height:96px;margin-top:8px}
.u9-col{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px}
.u9-bar{width:100%;background:var(--c-accent-weak);border-radius:6px 6px 0 0;min-height:4px}
.u9-bar.t{background:var(--c-accent)}
.day{font-size:11px;color:var(--c-faint)}
.u9-tbl{width:100%;border-collapse:collapse;margin-top:10px;font-size:12px;color:var(--c-muted)}
.u9-tbl th,.u9-tbl td{padding:4px 6px;text-align:left;border-bottom:1px solid var(--c-border)}
.u9-pref{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:6px 0}
.u9-pref .lab{font-size:14px} .u9-pref .sub{font-size:12px;color:var(--c-faint)}
.u9-time{border:1px solid var(--c-border);border-radius:var(--r-md);padding:8px 10px;font-size:14px;min-height:40px;background:var(--c-surface);color:var(--c-text)}
@media (max-width:768px){.u9-grid{grid-template-columns:repeat(2,1fr)}}
@media (max-width:480px){.u9-stat .n{font-size:20px}.u9-bar-row .nm{width:64px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
