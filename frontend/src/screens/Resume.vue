<!-- U1 简历工作台（A04/A05/A06 生产组件）。 -->
<!-- 交互规格：design/ui/interaction-U1.md；契约：resumes-create / resume-versions / resume-ats。 -->
<!-- U11 基线：加载(skeleton) / 错误(重试) / 空态(引导新建) / 无障碍(aria + 响应式 375/768/1280)。 -->
<!-- 诚实边界：列表与「设为首选」无契约端点，走本地 mock store（合同缺口见 TASK-LOG，与 A10 同处理）。 -->
<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { Card, Button, Modal, Toast, Skeleton, EmptyState, ErrorState } from '../components/UI.js';
import { api } from '../lib/api.js';

const fmtDate = (ms) => { const d = new Date(ms); return `${d.getMonth() + 1}月${d.getDate()}日`; };

const resumes = ref(null);   // null=加载中, []=空态
const error = ref(null);
const selectedId = ref(null);
const versions = ref(null);   // 选中简历的版本
const ats = ref({});          // resumeId -> {status, progress, report, failed}
const showCreate = ref(false);
const form = ref({ title: '', template: 'standard' });
const toast = ref({ show: false, message: '', onUndo: null });

const enriched = computed(() => (resumes.value || []).map((r) => ({ ...r, a: ats.value[r.resumeId] || {} })));

function load() {
  error.value = null;
  api.resumeList().then((list) => {
    resumes.value = list;
    const first = list[0] && list[0].resumeId;
    if (first && !selectedId.value) selectedId.value = first;
  }).catch(() => { error.value = '简历列表加载失败'; });
}
onMounted(load);

watch(selectedId, () => {
  if (!selectedId.value) { versions.value = null; return; }
  versions.value = null;
  api.resumeVersions(selectedId.value)
    .then((v) => { versions.value = v; })
    .catch(() => { versions.value = { versions: [], diffAvailable: false }; });
});

function flash(message, onUndo) {
  toast.value = { show: true, message, onUndo: onUndo || null };
  setTimeout(() => { toast.value = { ...toast.value, show: false }; }, 2600);
}

// A04 新建简历
function onCreate() {
  if (!form.value.title.trim()) { flash('请填写简历标题'); return; }
  api.createResume({ title: form.value.title.trim(), template: form.value.template }).then((r) => {
    showCreate.value = false; form.value = { title: '', template: 'standard' };
    load();
    flash(`已创建：${r.resumeId}`);
  }).catch(() => flash('创建失败，请重试'));
}

// A05 设为首选（本地 mock 直改；契约缺口）
function onPrefer(versionId) {
  api.setPreferred(selectedId.value, versionId).then(() => {
    api.resumeVersions(selectedId.value).then((v) => { versions.value = v; });
    resumes.value = resumes.value.map((r) => (r.resumeId === selectedId.value ? { ...r, preferredVersionId: versionId } : r));
    flash('已设为首选版本');
  });
}

// A06 触发 ATS 评分（异步状态机 pending→running→done/failed；done 展示 mock 评分环+维度分）
function onAts(resumeId) {
  ats.value = { ...ats.value, [resumeId]: { status: 'pending', progress: 0 } };
  api.triggerAts(resumeId).then(() => {
    ats.value = { ...ats.value, [resumeId]: { status: 'running', progress: 45 } };
    setTimeout(() => {
      const report = {
        atsScore: 72,
        suggestions: [
          { section: '项目经历', hint: '用「动词+量化结果」重写 2 条经历，ATS 匹配度更高。' },
          { section: '技能关键词', hint: '岗位 JD 高频词「React/TypeScript」建议前置。' },
          { section: '教育背景', hint: '时间倒序、补充 GPA（若≥3.5）。' },
        ],
      };
      ats.value = { ...ats.value, [resumeId]: { status: 'done', progress: 100, report } };
    }, 1400);
  }).catch(() => {
    ats.value = { ...ats.value, [resumeId]: { status: 'failed' } };
  });
}

function flashSafe() { console.log('[U1] 打开结构 diff 视图（resume-diff 端点）'); }
</script>

<template>
  <div style="max-width: 1080px; margin: 0 auto; padding: 12px 8px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
      <h2 style="margin: 0; font-size: 18px;">简历工作台</h2>
      <Button variant="primary" @click="showCreate = true">＋ 新建简历</Button>
    </div>

    <ErrorState v-if="error" :message="error" @retry="load" />
    <div v-else-if="resumes === null" style="padding: 16px;"><Skeleton :lines="4" /></div>
    <EmptyState v-else-if="resumes.length === 0" hint="还没有简历，先新建一份吧。">
      <template #action><Button variant="primary" @click="showCreate = true">＋ 新建简历</Button></template>
    </EmptyState>
    <div v-else style="display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1.2fr); gap: 14px;">
      <!-- 左栏：简历列表 -->
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <Card
          v-for="r in enriched"
          :key="r.resumeId"
          :class="{ sel: r.resumeId === selectedId }"
          :style="{ cursor: 'pointer', borderColor: r.resumeId === selectedId ? 'var(--c-accent)' : 'var(--c-border)', padding: '14px' }"
          @click="selectedId = r.resumeId"
        >
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
            <strong style="font-size: 15px;">{{ r.title }}</strong>
            <span v-if="r.preferredVersionId" style="font-size: 11px; background: var(--c-accent-weak); color: var(--c-accent); border-radius: var(--r-full); padding: 2px 8px;">首选 v{{ r.versionCount }}</span>
          </div>
          <div style="font-size: 12px; color: var(--c-muted); margin-top: 4px;">模板 {{ r.template }} · {{ r.versionCount }} 个版本</div>

          <!-- ATS 评分任务卡（异步状态机） -->
          <template v-if="!r.a.status">
            <Button style="margin-top: 10px; font-size: 13px; padding: 7px 12px; min-height: 36px;" @click.stop="onAts(r.resumeId)">触发 ATS 评分</Button>
          </template>
          <template v-else-if="r.a.status === 'pending'">
            <div style="margin-top: 10px; font-size: 12px; color: var(--c-muted);">评分任务已创建…</div>
          </template>
          <template v-else-if="r.a.status === 'running'">
            <div style="margin-top: 10px;">
              <div style="font-size: 12px; color: var(--c-muted); margin-bottom: 4px;">评分中 {{ r.a.progress }}%</div>
              <div style="height: 6px; background: var(--c-bg); border-radius: var(--r-full); overflow: hidden;">
                <div :style="{ height: '100%', width: r.a.progress + '%', background: 'var(--c-accent)' }"></div>
              </div>
            </div>
          </template>
          <template v-else-if="r.a.status === 'failed'">
            <div style="margin-top: 10px; font-size: 13px;"><span style="color: var(--c-bad);">评分失败</span>
              <Button style="font-size: 12px; padding: 4px 10px; min-height: 30px;" @click.stop="onAts(r.resumeId)">重试</Button></div>
          </template>
          <template v-else>
            <div style="margin-top: 10px; display: flex; gap: 12px; align-items: center;">
              <div :style="{ width: '46px', height: '46px', borderRadius: '50%', background: `conic-gradient(var(--c-ok) ${r.a.report.atsScore}%, var(--c-bg) 0)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 700 }">{{ r.a.report.atsScore }}</div>
              <ul style="margin: 0; padding-left: 16px; font-size: 12px; color: var(--c-muted);">
                <li v-for="(s, i) in r.a.report.suggestions.slice(0, 2)" :key="i"><b style="color: var(--c-strong);">{{ s.section }}</b>：{{ s.hint }}</li>
              </ul>
            </div>
          </template>
        </Card>
      </div>

      <!-- 右栏：版本面板 -->
      <Card style="padding: 16px; min-height: 200px;">
        <div v-if="!selectedId || versions === null" style="color: var(--c-faint); padding: 20px; text-align: center;">加载版本…</div>
        <div v-else-if="versions.versions.length === 0" style="color: var(--c-faint); padding: 20px; text-align: center;">尚未选择简历</div>
        <template v-else>
          <h3 style="margin: 0 0 10px; font-size: 15px;">版本时间线</h3>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            <div
              v-for="v in versions.versions"
              :key="v.versionId"
              :style="{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', border: '1px solid var(--c-border)', borderRadius: 'var(--r-md)', background: v.isPreferred ? 'var(--c-accent-weak)' : 'var(--c-surface)' }"
            >
              <div>
                <div style="font-size: 14px;">v{{ v.versionNo }} <span v-if="v.isPreferred" style="font-size: 11px; color: var(--c-accent);">★ 首选</span></div>
                <div style="font-size: 12px; color: var(--c-muted);">{{ fmtDate(v.createdAt) }}{{ v.note ? ' · ' + v.note : '' }}</div>
              </div>
              <Button v-if="!v.isPreferred" style="font-size: 12px; padding: 6px 12px; min-height: 32px;" @click="onPrefer(v.versionId)">设为首选</Button>
            </div>
          </div>
          <div style="margin-top: 12px;">
            <Button :variant="versions.diffAvailable ? 'primary' : 'default'" :disabled="!versions.diffAvailable" style="font-size: 13px;" @click="versions.diffAvailable && flashSafe()">
              对比两版 {{ versions.diffAvailable ? '' : '（需 ≥2 版）' }}
            </Button>
            <div v-if="!versions.diffAvailable" style="font-size: 11px; color: var(--c-faint); margin-top: 4px;">版本数 ≥2 后方可结构化 diff。</div>
          </div>
        </template>
      </Card>
    </div>

    <!-- A04 新建弹窗 -->
    <Modal :open="showCreate" title="新建简历" confirm-label="创建" @cancel="showCreate = false" @confirm="onCreate">
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <label style="font-size: 13px; color: var(--c-muted);">标题
          <input aria-label="简历标题" v-model="form.title" :style="{ width: '100%', marginTop: '6px', padding: '10px', borderRadius: 'var(--r-md)', border: '1px solid var(--c-border)', fontSize: '14px' }" placeholder="如：高级前端工程师" />
        </label>
        <label style="font-size: 13px; color: var(--c-muted);">模板
          <select aria-label="简历模板" v-model="form.template" :style="{ width: '100%', marginTop: '6px', padding: '10px', borderRadius: 'var(--r-md)', border: '1px solid var(--c-border)', fontSize: '14px' }">
            <option value="standard">标准版</option>
            <option value="tech">技术版</option>
          </select>
        </label>
      </div>
    </Modal>

    <Toast :show="toast.show" :message="toast.message" @undo="toast.onUndo" />
  </div>
</template>

<style scoped>
.sel { border-color: var(--c-accent) !important; }
</style>
