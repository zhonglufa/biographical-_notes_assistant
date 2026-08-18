<script setup>
// U6 面试模拟（V 阶段生产组件，接入真实 A16/A17/A18/A19）。
// 契约对齐见 design/ui/roles/U6-arch.md §4 字段映射表：
//   A16 questionSets[]{setId,title,questionCount,difficulty?,tags?}
//   A17 POST /interview/sessions {type,jobId?,mode,questionSetId?} → {sessionId,status(created|in_progress|completed|abandoned)}
//   A18 POST /interview/sessions/{id}/answer {answer(text|audioRef),questionId?,asrProvider?} → {accepted,score(0-1,nullable)}
//   A19 GET /interview/sessions/{id}/report → {sessionId,overallScore(0-100),dimensions[]{dim,rawScore(1-5),reason,score?},feedback,degradeFlag?}
// 安全红线（U6-engineer TRACE）：摄像头仅本地占位预览，绝不调用真实 getUserMedia 采集/上传；语音仅占位切文本。
// 配额 mock：专业版每日 10 次（来自 A03 users/me quota，本地 mock）。
import { ref, computed, onUnmounted } from 'vue'
import { Card, Button, Skeleton, EmptyState, ErrorState, Toast } from '../components/UI.js'
import { api } from '../lib/api.js'

// 三视图：prep(备战) / sim(模拟) / report(报告)
const tab = ref('prep')

// —— 配额（mock：专业版每日 10 次）——
const quota = ref({ limit: 10, used: 0 })
const remain = computed(() => Math.max(0, quota.value.limit - quota.value.used))
const quotaExhausted = computed(() => remain.value <= 0)

// —— 备战（A16）——
const loadingPrep = ref(true)
const prepErr = ref(null)
const sets = ref([])
const openSet = ref(null)

// —— 模拟（A17/A18）——
const session = ref(null)          // { sessionId, status }
const chat = ref([])                // [{ who:'ai'|'me', text }]
const chatLive = ref('')           // aria-live 文本
const answerText = ref('')
const turn = ref(0)
const aiScript = [
  '你好，先做一个简单的自我介绍吧。',
  '你刚提到负责过电商后端，能讲讲你们是怎么做服务拆分的？',
  '如果订单服务 RT 突然飙升，你的排查思路是什么？',
  '最后，你觉得相比其他候选人，你最大的优势是什么？',
]
const endVisible = ref(false)
const simErr = ref(null)

// —— 报告（A19）——
const report = ref(null)
const reportErr = ref(null)

const toast = ref({ show: false, msg: '' })
let toastTimer = null

function showToast(msg) {
  toast.value = { show: true, msg }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = { ...toast.value, show: false } }, 2600)
}

// ===== 加载题集（A16）=====
async function loadSets() {
  loadingPrep.value = true; prepErr.value = null
  try {
    const d = await api.interviewQuestions() // A16
    sets.value = (d.questionSets || []).map((s) => ({ ...s }))
  } catch (e) { prepErr.value = e.message || '题集加载失败' }
  finally { loadingPrep.value = false }
}
loadSets()

function toggleSet(id) {
  openSet.value = openSet.value === id ? null : id
}

// ===== 视图切换 =====
function switchTab(t) {
  tab.value = t
  if (t === 'prep') loadSets()
}
function gotoSim(setId) {
  if (quotaExhausted.value) { showToast('今日面试次数已用完，请升级套餐或查看历史报告'); return }
  tab.value = 'sim'
  const s = sets.value.find((x) => x.setId === setId)
  showToast(s ? `已为「${s.title}」预选题集，开始面试即可` : '开始面试即可')
}

// ===== 创建会话（A17）=====
async function startSession() {
  if (quotaExhausted.value) { showToast('今日面试次数已用完，请升级套餐或查看历史报告'); return }
  simErr.value = null
  try {
    const r = await api.createSession({ type: 'general', jobId: 'j1', mode: 'text' }) // A17
    session.value = { sessionId: r.sessionId, status: r.status || 'in_progress' }
    quota.value.used += 1
    chat.value = []
    pushBubble('ai', aiScript[0]); turn.value = 1
    endVisible.value = true
    showToast(`会话已创建：${r.sessionId}`)
  } catch (e) { simErr.value = e.message || '创建会话失败'; showToast('创建会话失败') }
}

// ===== 作答提交（A18）=====
async function sendAnswer() {
  const txt = answerText.value.trim()
  if (!txt || !session.value) return
  pushBubble('me', txt)
  answerText.value = ''
  simErr.value = null
  try {
    await api.answerSession(session.value.sessionId, { answer: txt, questionId: 'q' + turn.value }) // A18 接受+score(本地不强制使用)
    if (turn.value < aiScript.length) {
      pushBubble('ai', aiScript[turn.value]); turn.value += 1
    } else {
      pushBubble('ai', '好的，你的回答已记录，正在生成评估报告…')
    }
  } catch (e) { simErr.value = e.message || '作答提交失败'; showToast('作答提交失败') }
}

// ===== 结束出报告（A19）=====
async function endSession() {
  if (!session.value) return
  simErr.value = null
  try {
    const r = await api.sessionReport(session.value.sessionId) // A19
    report.value = r
    session.value.status = 'completed'
    endVisible.value = false
    tab.value = 'report'
    showToast('面试已完成，报告已生成')
  } catch (e) { reportErr.value = e.message || '报告生成失败'; showToast('报告生成失败') }
}

function pushBubble(who, text) {
  chat.value.push({ who, text })
  chatLive.value = (who === 'ai' ? '面试官：' : '你：') + text
}

// ===== 摄像头本地占位（红线：不调真实采集上传）=====
const camOn = ref(false)
function toggleCam() {
  camOn.value = !camOn.value
  showToast(camOn.value ? '本地镜像已开启（仅本地预览，不参与评估、不录制不上传）' : '本地镜像已关闭')
}

onUnmounted(() => { if (toastTimer) clearTimeout(toastTimer) })
</script>

<template>
  <div style="max-width: 1000px; margin: 0 auto; padding: 24px 16px 60px">
    <div class="iv-head">
      <h1 style="font-size: 18px; margin: 0">面试模拟</h1>
      <span class="iv-quota" aria-live="polite">今日剩余面试：<b>{{ remain }}</b> / {{ quota.limit }}（专业版）</span>
    </div>

    <!-- Tabs -->
    <div class="iv-tabs" role="tablist">
      <button class="iv-tab" :class="{ active: tab === 'prep' }" role="tab" :aria-selected="tab === 'prep'" @click="switchTab('prep')">面试备战</button>
      <button class="iv-tab" :class="{ active: tab === 'sim' }" role="tab" :aria-selected="tab === 'sim'" @click="switchTab('sim')">AI 面试模拟</button>
      <button class="iv-tab" :class="{ active: tab === 'report' }" role="tab" :aria-selected="tab === 'report'" @click="switchTab('report')">评估报告</button>
    </div>

    <!-- 备战（A16） -->
    <div v-show="tab === 'prep'">
      <Skeleton v-if="loadingPrep" :lines="3" />
      <ErrorState v-else-if="prepErr" :message="prepErr" @retry="loadSets" />
      <EmptyState v-else-if="sets.length === 0" hint="AI 正在生成题集，请稍后刷新">
        <template #action><Button @click="loadSets">刷新</Button></template>
      </EmptyState>
      <template v-else>
        <Card v-for="s in sets" :key="s.setId" className="iv-acc">
          <div
            class="iv-acc-head"
            role="button" tabindex="0"
            :aria-expanded="openSet === s.setId"
            @click="toggleSet(s.setId)"
            @keydown.enter.prevent="toggleSet(s.setId)"
            @keydown.space.prevent="toggleSet(s.setId)"
          >
            <span class="iv-acc-title">
              {{ s.title }}
              <span class="iv-acc-meta">{{ s.questionCount }} 题 · <span class="iv-pill" :class="'d-' + (s.difficulty || 'na')">{{ s.difficulty || '—' }}</span><span v-for="tg in (s.tags || [])" :key="tg" class="iv-pill">{{ tg }}</span></span>
            </span>
            <span class="iv-acc-chevron">{{ openSet === s.setId ? '▲' : '▼' }}</span>
          </div>
          <div v-show="openSet === s.setId" class="iv-acc-body">
            <p class="iv-acc-tip">建议结合你的简历与目标岗位 JD，用 STAR 法则组织回答。难度：{{ s.difficulty || '—' }}。</p>
            <Button variant="primary" @click="gotoSim(s.setId)">模拟作答</Button>
          </div>
        </Card>
      </template>
    </div>

    <!-- 模拟（A17/A18） -->
    <div v-show="tab === 'sim'">
      <div v-if="quotaExhausted" class="iv-note">今日面试次数已用完，请升级套餐或查看历史报告。移动端仅支持查看评估报告。</div>
      <Card className="iv-block">
        <h2 class="iv-h2">创建会话（A17）</h2>
        <div class="iv-row">
          <span class="iv-field">面试类型</span><span>通用面试</span>
          <span class="iv-field">目标岗位</span><span>Java 后端开发</span>
          <span class="iv-field">作答模式</span><span>文本</span>
          <Button variant="primary" :disabled="quotaExhausted || !!session" @click="startSession">开始面试</Button>
        </div>
      </Card>

      <div class="iv-sim">
        <Card className="iv-block" style="margin-bottom:0">
          <h2 class="iv-h2">对话（A18）</h2>
          <ErrorState v-if="simErr" :message="simErr" />
          <div class="iv-chat" aria-live="polite">
            <span class="iv-live" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">{{ chatLive }}</span>
            <div v-for="(m, i) in chat" :key="i" class="iv-bub" :class="m.who">{{ m.text }}</div>
          </div>
          <div class="iv-inputbar">
            <input v-model="answerText" type="text" class="iv-input" placeholder="输入你的作答…（语音模式为占位，不调真实麦克风）" @keydown.enter="sendAnswer" />
            <Button @click="sendAnswer">发送</Button>
            <Button v-if="endVisible" variant="primary" @click="endSession">结束面试</Button>
          </div>
        </Card>

        <div class="iv-pip" :class="{ on: camOn }">
          <div class="iv-cam">本地镜像预览<br>（可选 · 不参与评估 · 不录制不上传）</div>
          <Button @click="toggleCam">{{ camOn ? '关闭本地镜像' : '开启本地镜像' }}</Button>
          <div class="iv-pip-tip">摄像头仅本地自视角参考，评估完全基于文本/语音内容。</div>
        </div>
      </div>
    </div>

    <!-- 报告（A19） -->
    <div v-show="tab === 'report'">
      <EmptyState v-if="!report" hint="暂无报告。完成一场模拟面试后，报告将显示在这里" />
      <ErrorState v-else-if="reportErr" :message="reportErr" @retry="endSession" />
      <Card v-else className="iv-block">
        <h2 class="iv-h2">评估报告（A19）</h2>
        <div class="iv-report-top">
          <div>
            <div class="iv-muted">综合评分</div>
            <div class="iv-score">{{ report.overallScore }}</div>
          </div>
          <div class="iv-report-sid">会话 {{ report.sessionId }}</div>
        </div>
        <div class="iv-dims">
          <div v-for="d in (report.dimensions || [])" :key="d.dim" class="iv-dim">
            <div class="iv-dim-lab"><span>{{ d.dim }}</span><span>{{ d.rawScore }}/5</span></div>
            <div class="iv-bar"><i :style="{ width: (d.rawScore / 5 * 100) + '%' }"></i></div>
            <div class="iv-dim-reason">{{ d.reason }}</div>
          </div>
        </div>
        <div class="iv-feedback">{{ report.feedback }}</div>
        <div v-if="report.degradeFlag" class="iv-note">degradeFlag = true：本次 LLM 评估超时/失败，已启用题库预设题兜底，分数仅供参考。</div>
        <div class="iv-row" style="margin-top:12px">
          <Button disabled>申诉（v2）</Button>
          <Button disabled>重跑（v2）</Button>
        </div>
      </Card>
    </div>

    <Toast :show="toast.show" :message="toast.msg" />
  </div>
</template>

<style>
.iv-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.iv-quota{font-size:13px;color:var(--c-muted)}
.iv-quota b{color:var(--c-accent)}
.iv-tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.iv-tab{font:inherit;border:1px solid var(--c-border);background:var(--c-surface);padding:9px 16px;border-radius:var(--r-md);cursor:pointer;font-size:14px;color:var(--c-muted);min-height:40px}
.iv-tab.active{background:var(--c-accent);border-color:var(--c-accent);color:#fff;font-weight:600}
.iv-block{margin-bottom:16px}
.iv-h2{font-size:15px;margin:0 0 12px;color:var(--c-muted);font-weight:600;letter-spacing:.04em}
.iv-row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.iv-field{font-size:13px;color:var(--c-muted)}
.iv-acc{margin-bottom:10px}
.iv-acc-head{display:flex;align-items:center;justify-content:space-between;padding:14px 4px;cursor:pointer;font-weight:600}
.iv-acc-head:focus{outline:2px solid var(--c-accent);outline-offset:-2px}
.iv-acc-meta{font-size:12px;color:var(--c-muted);font-weight:400;margin-left:10px}
.iv-pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:999px;background:#eef0f6;color:var(--c-muted);margin-right:6px}
.iv-pill.d-easy{background:#dcfce7;color:#15803d}
.iv-pill.d-medium{background:#fef3c7;color:#b45309}
.iv-pill.d-hard{background:#fee2e2;color:#b91c1c}
.iv-acc-body{padding:0 4px 14px}
.iv-acc-tip{color:var(--c-ink);font-size:14px;line-height:1.6;margin:8px 0 12px}
.iv-sim{display:grid;grid-template-columns:1fr 220px;gap:16px}
.iv-chat{background:#fafbfc;border:1px solid var(--c-border);border-radius:var(--r-md);padding:14px;height:420px;overflow:auto;display:flex;flex-direction:column;gap:10px}
.iv-bub{max-width:78%;padding:10px 13px;border-radius:var(--r-md);font-size:14px;line-height:1.5}
.iv-bub.ai{background:#eef0f6;align-self:flex-start;border-bottom-left-radius:4px}
.iv-bub.me{background:var(--c-accent);color:#fff;align-self:flex-end;border-bottom-right-radius:4px}
.iv-inputbar{display:flex;gap:8px;margin-top:10px}
.iv-input{flex:1;font:inherit;padding:8px 10px;min-height:40px;border:1px solid var(--c-border);border-radius:var(--r-md);background:var(--c-surface);color:var(--c-ink)}
.iv-pip{background:var(--c-surface);border:1px solid var(--c-border);border-radius:var(--r-md);padding:12px;text-align:center;font-size:12px;color:var(--c-muted)}
.iv-cam{width:100%;height:120px;border-radius:var(--r-sm);background:linear-gradient(135deg,#2a2f3a,#3a4150);display:flex;align-items:center;justify-content:center;color:#cbd2e0;font-size:12px;margin-bottom:8px}
.iv-pip.on .iv-cam{background:linear-gradient(135deg,#1f2733,#4b5566)}
.iv-pip-tip{margin-top:8px}
.iv-report-top{display:flex;justify-content:space-between;align-items:flex-start}
.iv-muted{color:var(--c-muted);font-size:13px}
.iv-score{font-size:46px;font-weight:700;color:var(--c-accent)}
.iv-report-sid{font-size:12px;color:var(--c-muted)}
.iv-dim{margin-bottom:12px}
.iv-dim-lab{display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px}
.iv-bar{height:8px;background:#eef0f6;border-radius:6px;overflow:hidden}
.iv-bar > i{display:block;height:100%;background:var(--c-accent);border-radius:6px;transition:width var(--d-base) var(--e-out)}
.iv-dim-reason{font-size:12px;color:var(--c-muted);margin-top:4px}
.iv-feedback{background:#fafbfc;border:1px solid var(--c-border);border-radius:var(--r-sm);padding:12px;font-size:14px;line-height:1.6;margin-top:14px}
.iv-note{font-size:12px;color:#b45309;background:#fffbeb;border:1px solid #fde68a;border-radius:var(--r-sm);padding:8px 10px;margin-top:10px}
@media (max-width:768px){.iv-sim{grid-template-columns:1fr}.iv-chat{height:340px}}
@media (max-width:480px){.iv-inputbar{flex-wrap:wrap}.iv-inputbar .btn{flex:1}.iv-pip-tip{font-size:11px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
