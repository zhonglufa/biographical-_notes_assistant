<!-- U4 策略配置（A12/A13 生产组件，V 阶段）。 -->
<!-- 交互规格：design/ui/interaction-U4.md；契约：strategies.request / strategies.response (registry line 21-22 fully-detailed)。 -->
<!-- U11 基线：加载(Skeleton) / 错误(ErrorState+重试) / 校验(toast 拦截) / Toast(含撤销=恢复未保存前的快照) / 无障碍(aria-label / role="switch") / 响应式 375/768/1280。 -->
<!-- 护栏联动：dailyLimit 与 U3 「今日 X / 限额 N」 同源（A12 dailyLimit）；matchThreshold 对应本机 Agent plan() 过滤 low 匹配（LLD 本机Agent v1.3）。 -->
<!-- 合同缺口：NONE（A12/A13 schema 4 字段 + A13 写响应 {ok,updatedAt} 全，registry fully-detailed）。 -->
<script setup>
import { ref, computed, onMounted } from 'vue';
import { Card, Button, Skeleton, ErrorState, Toast } from '../components/UI.js';
import { api } from '../lib/api.js';

const PLAT = [
  { id: 'boss', label: 'Boss直聘' },
  { id: 'liepin', label: '猎聘' },
  { id: 'zhaopin', label: '智联' },
  { id: '51job', label: '前程无忧' },
  { id: 'lagou', label: '拉勾' },
];

// 4 字段表单态（与 strategies 契约同形）。
function blank() { return { matchThreshold: 0.8, dailyLimit: 20, platforms: ['boss', 'liepin', 'zhaopin'], blacklist: ['某保险', '996'] }; }
const DEFAULT_STRAT = blank();

const loaded = ref(null);     // 服务端拉到的当前策略
const draft = ref(blank());   // 编辑中的草稿
const dirty = ref(false);     // 与初始已加载值是否有差异
const saving = ref(false);
const err = ref(null);
const blInput = ref('');
const toast = ref({ show: false, message: '', onUndo: null });

function flash(message, onUndo) {
  toast.value = { show: true, message, onUndo: onUndo || null };
  setTimeout(() => { toast.value = { ...toast.value, show: false }; }, 2800);
}

function load() {
  err.value = null;
  loaded.value = null;
  api.getStrategy()
    .then((s) => {
      loaded.value = s;
      draft.value = { matchThreshold: Number(s.matchThreshold), dailyLimit: parseInt(s.dailyLimit, 10), platforms: [...(s.platforms || [])], blacklist: [...(s.blacklist || [])] };
      dirty.value = false;
    })
    .catch(() => { err.value = '策略加载失败'; });
}
onMounted(load);

// 变更检测：草稿与已加载服务端值任一字段不同则视为 dirty，可触发撤销。
function markDirty() { dirty.value = true; }

// 阈值滑块（0–100% ↔ 0–1）
const thrPct = computed({
  get: () => Math.round(draft.value.matchThreshold * 100),
  set: (v) => { draft.value.matchThreshold = Math.max(0, Math.min(100, Number(v))) / 100; markDirty(); },
});

// 阈值语义分档（绿/蓝/灰）
const thrBand = computed(() => {
  const p = thrPct.value;
  if (p >= 80) return { key: 'green', label: '优先确认（绿）', fg: 'var(--c-ok, #16A34A)', bg: '#ECFDF3', bd: '#ABEFC6' };
  if (p >= 60) return { key: 'blue', label: '可纳入（蓝）', fg: 'var(--c-info, #2563EB)', bg: '#EFF6FF', bd: '#BFDBFE' };
  return { key: 'gray', label: '低匹配（灰·不进队列）', fg: 'var(--c-muted, #64748B)', bg: '#F1F5F9', bd: '#E2E8F0' };
});

function onLimit() { markDirty(); }

// 平台 chips：点选切换；强制至少启用 1 个（与契约 / 设计稿警告一致）
function togglePlat(id) {
  const set = new Set(draft.value.platforms);
  if (set.has(id)) { if (set.size <= 1) { flash('至少启用一个平台'); return; } set.delete(id); }
  else { set.add(id); }
  draft.value.platforms = [...set];
  markDirty();
}

// 黑名单 tags：回车/添加/+× 删除
function addBl() {
  const v = (blInput.value || '').trim();
  if (!v) return;
  if (draft.value.blacklist.includes(v)) { flash('黑名单已存在该词'); return; }
  draft.value.blacklist = [...draft.value.blacklist, v];
  blInput.value = '';
  markDirty();
}
function onBlKey(e) { if (e.key === 'Enter') { e.preventDefault(); addBl(); } }
function delBl(i) { draft.value.blacklist.splice(i, 1); draft.value = { ...draft.value }; markDirty(); }

// 恢复默认
function resetDef() {
  draft.value = blank();
  blInput.value = '';
  dirty.value = true;
  flash('已恢复默认策略（点击保存后生效）');
}

// 保存前校验（前端 + 契约语义对齐：thr 0–1 / limit 非负整数 / platforms≥1）
function validate() {
  const d = draft.value;
  const t = Number(d.matchThreshold);
  if (Number.isNaN(t) || t < 0 || t > 1) { flash('匹配阈值需在 0–100%'); return null; }
  const l = parseInt(d.dailyLimit, 10);
  if (Number.isNaN(l) || l < 0 || String(l) !== String(d.dailyLimit)) { flash('每日限额须为非负整数'); return null; }
  if (!Array.isArray(d.platforms) || d.platforms.length === 0) { flash('至少启用一个平台'); return null; }
  if (!Array.isArray(d.blacklist)) { flash('黑名单非法'); return null; }
  return { matchThreshold: t, dailyLimit: l, platforms: [...d.platforms], blacklist: [...d.blacklist] };
}

// 保存（A13 PUT /strategies → ok + updatedAt）
async function save() {
  const body = validate();
  if (!body) return;
  saving.value = true;
  try {
    const r = await api.saveStrategy(body);
    if (!r || !r.ok) { flash('保存失败：服务端未确认'); return; }
    dirty.value = false;
    // 成功后回拉以校验后端真值
    await load();
    flash(`策略已保存（updatedAt=${formatTs(r.updatedAt)}）`, () => {
      // 撤销 = 回滚到本次保存前的服务端值（重新拉取）
      load();
      flash('已撤销本次保存');
    });
  } catch (e) {
    flash('保存失败：' + (e && e.message ? e.message : '网络异常'));
  } finally { saving.value = false; }
}

function formatTs(ms) {
  if (!ms) return '—';
  const d = new Date(Number(ms));
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}
</script>

<template>
  <div style="max-width: 920px; margin: 0 auto; padding: 12px 8px;">
    <!-- 页头：标题 + A12/A13 标识 + 计数提示 -->
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; flex-wrap: wrap; gap: 8px;">
      <div>
        <h2 style="margin: 0; font-size: 18px; color: var(--c-text);">策略配置</h2>
        <div style="font-size: 12px; color: var(--c-muted); margin-top: 4px;">设定 AI 匹配门槛、每日投递上限、启用平台与黑名单，保存即生效。
          <span style="background: var(--c-accent); color: #fff; font-size: 11px; padding: 1px 8px; border-radius: var(--r-full); margin-left: 6px;">A12 / A13</span>
        </div>
      </div>
    </div>

    <ErrorState v-if="err" :message="err">
      <template #retry><Button @click="load">重新加载</Button></template>
    </ErrorState>

    <div v-else-if="!loaded" style="padding: 8px;">
      <Skeleton :lines="4" />
    </div>

    <template v-else>
      <!-- 1. 匹配阈值（A12 matchThreshold · 0–1） -->
      <Card style="margin-bottom: 14px;">
        <h3 style="margin: 0 0 10px; font-size: 13px; font-weight: 600; color: var(--c-text); border-left: 3px solid var(--c-accent); padding-left: 8px;">匹配阈值<span style="font-size: 11px; color: var(--c-muted); margin-left: 6px;">A12 matchThreshold · 0–1</span></h3>
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
          <input
            type="range" min="0" max="100" :value="thrPct"
            @input="(e) => (thrPct = e.target.value)"
            aria-label="匹配阈值（百分比）"
            style="flex: 1; min-width: 200px; max-width: 360px;"
          />
          <span :style="{ fontWeight: 700, fontSize: '18px', color: thrBand.fg }">{{ thrPct }}%</span>
          <span :style="{ fontSize: '12px', padding: '3px 10px', borderRadius: 'var(--r-full)', background: thrBand.bg, color: thrBand.fg, border: '1px solid ' + thrBand.bd }">{{ thrBand.label }}</span>
        </div>
        <div style="font-size: 12px; color: var(--c-faint, #9aa6b2); margin-top: 8px;">≥80%（绿）优先确认；60–79%（蓝）可纳入；低于阈值不进待确认队列。对应本机 Agent plan() 过滤 low 匹配。</div>
      </Card>

      <!-- 2. 每日投递限额（A12 dailyLimit · integer ≥0） -->
      <Card style="margin-bottom: 14px;">
        <h3 style="margin: 0 0 10px; font-size: 13px; font-weight: 600; color: var(--c-text); border-left: 3px solid var(--c-accent); padding-left: 8px;">每日投递限额<span style="font-size: 11px; color: var(--c-muted); margin-left: 6px;">A12 dailyLimit · int ≥0</span></h3>
        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
          <input
            type="number" min="0" max="200" v-model="draft.dailyLimit" @input="onLimit"
            aria-label="每日投递限额"
            style="font-family: var(--font); font-size: 14px; padding: 10px 12px; border: 1px solid var(--c-border); border-radius: var(--r-md); width: 200px; color: var(--c-text); background: var(--c-surface);"
          />
          <span style="font-size: 12px; color: var(--c-muted);">份 / 账号 · 与 U3 「今日 X / 限额 N」 同源；达限额时确认按钮禁用。</span>
        </div>
        <div style="font-size: 12px; color: var(--c-faint, #9aa6b2); margin-top: 8px;">建议新手 ≤20；与护栏 2（LLM 成本 / 投递量硬上限）联动。</div>
      </Card>

      <!-- 3. 启用平台（A12 platforms · 数组） -->
      <Card style="margin-bottom: 14px;">
        <h3 style="margin: 0 0 10px; font-size: 13px; font-weight: 600; color: var(--c-text); border-left: 3px solid var(--c-accent); padding-left: 8px;">启用平台<span style="font-size: 11px; color: var(--c-muted); margin-left: 6px;">A12 platforms · 数组</span></h3>
        <div role="group" aria-label="启用平台" style="display: flex; flex-wrap: wrap; gap: 8px;">
          <button
            v-for="p in PLAT" :key="p.id"
            type="button"
            @click="togglePlat(p.id)"
            :aria-pressed="draft.platforms.includes(p.id)"
            :style="{
              fontSize: '13px', padding: '8px 14px', borderRadius: 'var(--r-full)',
              border: '1px solid ' + (draft.platforms.includes(p.id) ? 'var(--c-accent)' : 'var(--c-border)'),
              background: draft.platforms.includes(p.id) ? 'var(--c-accent-weak)' : 'var(--c-surface)',
              color: draft.platforms.includes(p.id) ? 'var(--c-accent)' : 'var(--c-body)',
              fontWeight: draft.platforms.includes(p.id) ? 600 : 500,
              cursor: 'pointer', minHeight: '40px',
            }"
          >{{ p.label }}</button>
        </div>
        <div v-if="draft.platforms.length === 0" style="margin-top: 10px; padding: 10px 12px; background: #FFFAEB; border: 1px solid #FDE68A; border-radius: var(--r-md); color: #D97706; font-size: 13px;">⚠️ 至少启用一个平台，否则不会采集任何岗位。</div>
      </Card>

      <!-- 4. 黑名单（A12 blacklist · 数组） -->
      <Card style="margin-bottom: 14px;">
        <h3 style="margin: 0 0 10px; font-size: 13px; font-weight: 600; color: var(--c-text); border-left: 3px solid var(--c-accent); padding-left: 8px;">黑名单<span style="font-size: 11px; color: var(--c-muted); margin-left: 6px;">A12 blacklist · 数组</span></h3>
        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px;">
          <span
            v-for="(t, i) in draft.blacklist" :key="t + '-' + i"
            style="display: inline-flex; align-items: center; gap: 6px; background: var(--c-bg); color: var(--c-body); font-size: 13px; padding: 6px 10px; border-radius: var(--r-full); border: 1px solid var(--c-border);"
          >
            {{ t }}
            <b role="button" :aria-label="`删除 ${t}`" tabindex="0" @click="delBl(i)" @keydown.enter="delBl(i)" style="color: var(--c-bad, #e5484d); cursor: pointer; font-weight: 700; font-size: 14px; line-height: 1;">×</b>
          </span>
          <span v-if="draft.blacklist.length === 0" style="font-size: 12px; color: var(--c-faint, #9aa6b2);">（暂无）</span>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
          <input
            type="text" v-model="blInput" @keydown="onBlKey"
            placeholder="如：某保险 / 996 / 销售性质"
            aria-label="添加黑名单"
            style="font-family: var(--font); font-size: 14px; padding: 10px 12px; border: 1px solid var(--c-border); border-radius: var(--r-md); width: 280px; max-width: 100%; color: var(--c-text); background: var(--c-surface);"
          />
          <Button @click="addBl">添加</Button>
        </div>
        <div style="font-size: 12px; color: var(--c-faint, #9aa6b2); margin-top: 8px;">命中黑名单的岗位在匹配阶段直接过滤，不会进入待确认队列。</div>
      </Card>

      <!-- 操作栏：保存 / 恢复默认 / 脏标记 -->
      <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-top: 6px;">
        <Button variant="primary" :disabled="saving || !dirty" @click="save">{{ saving ? '保存中…' : '保存策略' }}</Button>
        <Button @click="resetDef">恢复默认</Button>
        <span v-if="dirty" style="font-size: 12px; color: #D97706;">● 有未保存的改动</span>
      </div>
    </template>

    <Toast :show="toast.show" :message="toast.message" @undo="toast.onUndo" />
  </div>
</template>

<style scoped>
/* 响应式（UI-SELFCHECK §5 范式）：手机端卡片纵向堆叠 + 输入/按钮 ≥40px 可点 + 滑块达 100% 宽 + 模态 ≤90vw。 */
@media (max-width: 768px) {
  .thr-row, .plat-row, .bl-row { flex-direction: column; align-items: stretch; }
  input[type="range"] { width: 100%; max-width: 100%; }
  input[type="number"], input[type="text"] { width: 100%; }
  button { min-height: 40px; }
}
</style>
