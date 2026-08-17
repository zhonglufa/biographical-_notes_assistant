<script setup>
// U7 支付与会员（V 阶段生产组件，接入真实 A20/A21）。
// 契约对齐见 design/ui/roles/U7-arch.md §4 字段映射表：
//   A03 /users/me → plan(free|pro|team) + quotaUsed/quotaLimit
//   A20 POST /orders {plan(pro|team),months(int),coupon?} → {orderNo,amount(分),payUrl,expireAt(epoch ms)}
//   A21 POST /orders/{id}/callback（mock）驱动 订单状态机 + memberPlanChanged 权益刷新
// 安全/诚实：payUrl 仅占位展示，不真跳转；金额前端仅展示(分→元换算，不计算)；MockPay 模拟 A21 回调。
// 订单状态机：pending(待支付)→paid(已支付)→active(已开通)→expired(已过期)|refunded(已退款)。
import { ref, computed, onUnmounted } from 'vue'
import { Card, Button, Modal, Toast } from '../components/UI.js'
import { api } from '../lib/api.js'

// 套餐枚举（前端展示三档；premium 后端映射团队版）
const PLAN = {
  free:  { name: '免费版', color: 'var(--c-faint)', sub: '每日投递上限 30 份 · ≤3 平台 · AI 面试每日 3 次' },
  pro:   { name: '专业版', color: 'var(--c-accent)', sub: '每日投递上限 100 份 · 全平台 · AI 面试 10 次/日' },
  team:  { name: '团队版', color: 'var(--c-blue)', sub: '专业版全部 · 多版本简历 · AI 面试无限次' },
}
// 价格（元/月，仅用于展示对照；下单金额由"服务端"返回，前端不取价）
const PRICE = { pro: { 1: 29, 3: 79, 6: 149, 12: 279 }, team: { 1: 99, 3: 269, 6: 519, 12: 999 } }

const curPlan = ref('free')
const quota = ref({ used: 0, limit: 30 })
const downgraded = ref(false)

const orders = ref([
  { orderNo: 'ORD-20260817-0001', desc: '专业版 · 3 个月', state: 'active', color: 'var(--c-ok)', bc: '#bbf7d0', bg: '#f0fdf4' },
])

// 下单面板（A20）
const orderOpen = ref(false)
const payOpen = ref(false)
const target = ref('pro')
const months = ref(1)
const curOrderNo = ref(null)
const payMeta = ref('')
const mockPayDisabled = ref(false)
let countTimer = null

const toast = ref({ show: false, msg: '' })
let toastTimer = null
function showToast(msg) {
  toast.value = { show: true, msg }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = { ...toast.value, show: false } }, 2600)
}

function setPlan(p) {
  curPlan.value = p
}
function openOrder(t) {
  target.value = t
  months.value = 1
  orderOpen.value = true
}
function closeOrder() { orderOpen.value = false }
function pickPeriod(m) { months.value = m }

async function createOrder() {
  try {
    const r = await api.createOrder({ plan: target.value, months: months.value }) // A20 {orderNo,amount,payUrl,expireAt}
    curOrderNo.value = r.orderNo
    const yuan = (r.amount || 0) / 100
    payMeta.value = `订单号 ${r.orderNo} ｜ ¥${yuan} ｜ 24h 内有效`
    mockPayDisabled.value = false
    closeOrder()
    payOpen.value = true
    addOrder(r.orderNo, `${PLAN[target.value].name} · ${months.value} 个月`, 'pending', 'var(--c-blue)', '#dbeafe', '#eff6ff')
    startCount(r.expireAt)
    showToast('订单已创建，请完成支付')
  } catch (e) { showToast(e.message || '下单失败') }
}
function startCount(expireAt) {
  if (countTimer) clearInterval(countTimer)
  const el = document.getElementById('iv-count')
  countTimer = setInterval(() => {
    const left = Math.max(0, expireAt - Date.now())
    if (!el) return
    const h = Math.floor(left / 3600000), m = Math.floor(left % 3600000 / 60000), s = Math.floor(left % 60000 / 1000)
    el.textContent = left <= 0 ? '订单已过期' : `剩余 ${h}h ${m}m ${s}s`
    if (left <= 0) clearInterval(countTimer)
  }, 1000)
}
function closePay() {
  if (countTimer) clearInterval(countTimer)
  payOpen.value = false
}
// MockPay 模拟 A21 回调：paymentStatusChanged.paid → memberPlanChanged.<plan>
function mockCallback() {
  if (mockPayDisabled.value) return
  mockPayDisabled.value = true
  updateOrder(curOrderNo.value, 'active', 'var(--c-ok)', '#bbf7d0', '#f0fdf4')
  setPlan(target.value)
  downgraded.value = false
  closePay()
  showToast(`已升级为${PLAN[target.value].name}，权益已生效`)
}
function addOrder(id, desc, state, color, bc, bg) {
  orders.value.unshift({ orderNo: id, desc, state, color, bc, bg })
}
function updateOrder(id, state, color, bc, bg) {
  const o = orders.value.find((x) => x.orderNo === id)
  if (o) { o.state = state; o.color = color; o.bc = bc; o.bg = bg }
}
function simulateExpired() {
  addOrder('ORD-EXP-' + Date.now().toString().slice(-6), '专业版 · 3 个月', 'expired', 'var(--c-faint)', '#e5e7eb', '#f9fafb')
  showToast('订单已过期（24h 内未支付）')
}
function simulateDowngrade() {
  downgraded.value = true
  setPlan('free')
  showToast('会员已降级为免费版')
}

onUnmounted(() => { if (countTimer) clearInterval(countTimer); if (toastTimer) clearTimeout(toastTimer) })

// 当前套餐卡对比高亮
const curIsFree = computed(() => curPlan.value === 'free')
</script>

<template>
  <div style="max-width: 1000px; margin: 0 auto; padding: 24px 16px 60px">
    <div class="pm-head">
      <h1 style="font-size: 18px; margin: 0">我的会员</h1>
      <span class="pm-badge"><span class="pm-dot" :style="{ background: PLAN[curPlan].color }"></span>{{ PLAN[curPlan].name }}</span>
    </div>

    <div v-if="downgraded" class="pm-downgrade">⚠️ 会员已过期，已自动降级为免费版：原有配置已保留但不可修改，超限的在途投递任务允许执行完毕。升级后可重新激活。</div>

    <Card className="pm-block">
      <h2 class="pm-h2">当前套餐</h2>
      <div class="pm-plan-card">
        <div class="pm-meta">
          <div class="pm-name">{{ PLAN[curPlan].name }}</div>
          <div class="pm-sub">{{ PLAN[curPlan].sub }}</div>
        </div>
        <Button variant="primary" @click="openOrder(curIsFree ? 'pro' : 'team')">升级{{ curIsFree ? '专业版' : '团队版' }}</Button>
      </div>
    </Card>

    <Card className="pm-block">
      <h2 class="pm-h2">套餐对比</h2>
      <div class="pm-compare">
        <div v-for="(p, key) in { free: PLAN.free, pro: PLAN.pro, team: PLAN.team }" :key="key"
             class="pm-pc" :class="{ current: curPlan === key }">
          <div class="pm-pc-t">{{ p.name }}</div>
          <div class="pm-pc-p">{{ key === 'free' ? '¥0' : '¥' + PRICE[key][1] + '/月' }}</div>
          <ul class="pm-pc-ul">
            <li v-if="key === 'free'">日投递 30 份 · ≤3 平台 · AI 面试 3 次/日</li>
            <li v-else-if="key === 'pro'">日投递 100 份 · 全平台 · AI 面试 10 次/日</li>
            <li v-else>专业版全部 · 多版本简历 · AI 面试无限次</li>
          </ul>
          <Button v-if="curPlan === key" disabled>当前套餐</Button>
          <Button v-else variant="primary" @click="openOrder(key)">升级</Button>
        </div>
      </div>
    </Card>

    <Card className="pm-block">
      <h2 class="pm-h2">我的订单</h2>
      <div class="pm-orders">
        <div v-for="o in orders" :key="o.orderNo" class="pm-orow">
          <span class="pm-oid">{{ o.orderNo }}</span>
          <span>{{ o.desc }}</span>
          <span class="pm-ostate" :style="{ color: o.color, borderColor: o.bc, background: o.bg }">{{ o.state }}</span>
        </div>
      </div>
      <div class="pm-sim">
        <Button @click="simulateExpired">模拟：订单过期</Button>
        <Button @click="simulateDowngrade">模拟：会员降级</Button>
      </div>
    </Card>

    <!-- 下单面板（A20） -->
    <Modal :open="orderOpen" :title="`升级 ${PLAN[target].name}`" @cancel="closeOrder" @confirm="createOrder">
      <p style="margin:0 0 10px">选择订购周期（金额由服务端计算，前端不取价）。</p>
      <div class="pm-seg">
        <button v-for="m in [1,3,6,12]" :key="m" :class="{ on: months === m }" @click="pickPeriod(m)">{{ m }} 个月</button>
      </div>
    </Modal>

    <!-- 支付弹窗（A21 payUrl 占位） -->
    <Modal :open="payOpen" title="扫码支付" @cancel="closePay" @confirm="mockCallback">
      <div class="pm-qr">支付二维码占位<br>（payUrl 仅展示，不真实跳转）</div>
      <div style="text-align:center;font-size:13px">{{ payMeta }}</div>
      <div id="iv-count" class="pm-count"></div>
      <p style="text-align:center;font-size:13px;color:var(--c-muted)">完成支付后点击下方模拟回调（A21）</p>
    </Modal>

    <Toast :show="toast.show" :message="toast.msg" />
  </div>
</template>

<style>
.pm-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:18px;flex-wrap:wrap}
.pm-badge{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:600;padding:5px 12px;border-radius:999px;border:1px solid var(--c-border)}
.pm-dot{width:8px;height:8px;border-radius:50%}
.pm-downgrade{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:var(--r-md);padding:12px 14px;font-size:13px;margin-bottom:14px}
.pm-block{margin-bottom:18px}
.pm-h2{font-size:15px;margin:0 0 12px;color:var(--c-muted);font-weight:600;letter-spacing:.04em}
.pm-plan-card{display:flex;align-items:center;gap:14px;padding:14px;border:1px solid var(--c-border);border-radius:var(--r-md)}
.pm-meta{flex:1;min-width:0}
.pm-name{font-weight:600}
.pm-sub{font-size:12px;color:var(--c-muted);margin-top:3px}
.pm-compare{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.pm-pc{border:1px solid var(--c-border);border-radius:var(--r-md);padding:14px;display:flex;flex-direction:column;gap:8px}
.pm-pc.current{border-color:var(--c-accent);box-shadow:0 0 0 2px rgba(108,92,231,.15)}
.pm-pc-t{font-weight:700;font-size:15px}
.pm-pc-p{color:var(--c-accent);font-size:18px;font-weight:700}
.pm-pc-ul{margin:4px 0;padding-left:18px;font-size:13px;color:var(--c-muted)}
.pm-orders{display:flex;flex-direction:column;gap:10px}
.pm-orow{display:flex;align-items:center;gap:12px;padding:12px;border:1px solid var(--c-border);border-radius:var(--r-sm)}
.pm-oid{font-size:12px;color:var(--c-muted);font-family:ui-monospace,monospace}
.pm-ostate{margin-left:auto;font-size:12px;font-weight:600;padding:4px 10px;border-radius:999px;border:1px solid var(--c-border)}
.pm-sim{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.pm-seg{display:flex;gap:8px;margin:10px 0}
.pm-seg button{flex:1;min-height:40px;font:inherit;border:1px solid var(--c-border);background:var(--c-surface);border-radius:var(--r-md);cursor:pointer}
.pm-seg button.on{background:var(--c-accent);border-color:var(--c-accent);color:#fff;font-weight:600}
.pm-qr{width:150px;height:150px;margin:10px auto;border:1px dashed var(--c-border);border-radius:var(--r-md);display:flex;align-items:center;justify-content:center;color:var(--c-faint);font-size:12px;text-align:center}
.pm-count{font-variant-numeric:tabular-nums;color:var(--c-muted);font-size:13px;text-align:center;margin-top:6px}
@media (max-width:768px){
  .pm-compare{grid-template-columns:1fr}
  .pm-pc.current{box-shadow:none}
  .pm-plan-card{flex-wrap:wrap}
  .pm-orow{flex-wrap:wrap}
  .pm-orow .pm-ostate{margin-left:0}
}
@media (max-width:480px){
  .pm-seg{flex-wrap:wrap}.pm-seg button{flex:1 1 40%}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
