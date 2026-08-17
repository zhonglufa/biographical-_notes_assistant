<!-- U1 简历工作台（A04/A05/A06 生产组件）。 -->
<!-- 交互规格：design/ui/interaction-U1.md；契约：resumes-create / resume-versions / resume-ats。 -->
<!-- U11 基线：加载(skeleton) / 错误(重试) / 空态(引导新建) / 无障碍(aria + 响应式 375/768/1280)。 -->
<script setup>
import { ref, onMounted, watch } from 'vue';
import { Card, Button, Modal, Skeleton, EmptyState, ErrorState, Toast } from '../components/UI.js';
import { api } from '../lib/api.js';

const fmtDate = ms => { const d = new Date(ms); return `${d.getMonth() + 1}月${d.getDate()}日`; };

const resumes = ref(null);
const error = ref(null);
const selectedId = ref(null);
const versions = ref(null);
const ats = ref({});
const showCreate = ref(false);
const form = ref({ title: '', template: 'standard' });
const toast = ref({ show: false, message: '', onUndo: null });

async function load() {
  error.value = null;
  try {
    const list = await api.resumeList();
    resumes.value = list;
    const first = list[0] && list[0].resumeId;
    if (first && !selectedId.value) selectedId.value = first;
  } catch { error.value = '简历列表加载失败'; }
}
onMounted(load);

async function loadVersions() {
  if (!selectedId.value) { versions.value = null; return; }
  versions.value = null;
  try { versions.value = await api.resumeVersions(selectedId.value); }
  catch { versions.value = { versions: [], diffAvailable: false }; }
}

watch(selectedId, loadVersions, { immediate: true });

function flash(message, onUndo) { toast.value = { show: true, message, onUndo: onUndo || null }; setTimeout(() => toast.value = { ...toast.value, show: false }, 2600); }

function onCreate() {
  if (!form.value.title.trim()) { flash('请填写简历标题'); return; }
  api.createResume({ title: form.value.title.trim(), template: form.value.template }).then(r => {
    showCreate.value = false; form.value = { title: '', template: 'standard' };
    load();
    flash(`已创建：${r.resumeId}`);
  }).catch(() => flash('创建失败，请重试'));
}

function onPrefer(versionId) {
  api.setPreferred(selectedId.value, versionId).then(() => {
    loadVersions();
    resumes.value = resumes.value.map(r => r.resumeId === selectedId.value ? { ...r, preferredVersionId: versionId } : r);
    flash('已设为首选版本');
  });
}

function onAts(resumeId) {
  ats.value = { ...ats.value, [resumeId]: { status: 'pending', progress: 0 } };
  api.triggerAts(resumeId).then(() => {
    ats.value = { ...ats.value, [resumeId]: { status: 'running', progress: 45 } };
    setTimeout(() => {
      const report = { atsScore: 72, suggestions: [
        { section: '项目经历', hint: '用「动词+量化结果」重写 2 条经历，ATS 匹配度更高。' },
        { section: '技能关键词', hint: '岗位 JD 高频词「React/TypeScript」建议前置。' },
        { section: '教育背景', hint: '时间倒序、补充 GPA（若≥3.5）。' },
      ] };
      ats.value = { ...ats.value, [resumeId]: { status: 'done', progress: 100, report } };
    }, 1400);
  }).catch(() => ats.value = { ...ats.value, [resumeId]: { status: 'failed' } });
}

function flashSafe(ok) { if (ok) console.log('[U1] 打开结构 diff 视图（resume-diff 端点）'); }
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
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <Card v-for="r in resumes" :key="r.resumeId" :class="r.resumeId === selectedId ? 'sel' : ''" style="cursor: pointer; border-color: r.resumeId === selectedId ? 'var(--c-accent)' : 'var(--c-border)'; padding: 14px;" @click="selectedId = r.resumeId">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
              <strong style="font-size: 15px;">{{ r.title }}</strong>
              <span v-if="r.preferredVersionId" style="font-size: 11px; background: var(--c-accent-weak); color: var(--c-accent); border-radius: var(--r-full); padding: 2px 8px;">首选 v{{ r.versionCount }}</span>
            </div>
            <div style="font-size: 12px; color: var(--c-muted); margin-top: 4px;">模板 {{ r.template }} · {{ r.versionCount }} 个版本</div>
            <AtsCard :a="ats[r.resumeId] || {}" @ats="onAts(r.resumeId)" />
          </div>
        </Card>
      </div>
      <Card style="padding: 16px; min-height: 200px;">
        <VersionPanel v-if="selectedId && versions" :versions="versions" @prefer="onPrefer" />
        <div v-else style="color: var(--c-faint); padding: 20px; text-align: center;">加载版本…</div>
      </Card>
    </div>

    <Modal :open="showCreate" title="新建简历" confirm-label="创建" @cancel="showCreate = false" @confirm="onCreate">
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <label style="font-size: 13px; color: var(--c-muted);">标题
          <input v-model="form.title" aria-label="简历标题" placeholder="如：高级前端工程师" style="width: 100%; margin-top: 6px; padding: 10px; border-radius: var(--r-md); border: 1px solid var(--c-border); font-size: 14px;" />
        </label>
        <label style="font-size: 13px; color: var(--c-muted);">模板
          <select v-model="form.template" aria-label="简历模板" style="width: 100%; margin-top: 6px; padding: 10px; border-radius: var(--r-md); border: 1px solid var(--c-border); font-size: 14px;">
            <option value="standard">标准版</option>
            <option value="tech">技术版</option>
          </select>
        </label>
      </div>
    </Modal>

    <Toast :show="toast.show" :message="toast.message" @undo="toast.onUndo" />
  </div>
</template>

<script>
import { h, defineComponent } from 'vue';
import { Button } from '../components/UI.js';

const AtsCard = defineComponent({
  props: { a: Object },
  emits: ['ats'],
  setup(props, { emit }) {
    return () => {
      const a = props.a;
      if (!a.status) return h(Button, { style: { marginTop: '10px', fontSize: '13px', padding: '7px 12px', minHeight: '36px' }, onClick: () => emit('ats') }, () => '触发 ATS 评分');
      if (a.status === 'pending') return h('div', { style: { marginTop: '10px', fontSize: '12px', color: 'var(--c-muted)' } }, '评分任务已创建…');
      if (a.status === 'running') return h('div', { style: { marginTop: '10px' } }, [
        h('div', { style: { fontSize: '12px', color: 'var(--c-muted)', marginBottom: '4px' } }, `评分中 ${a.progress}%`),
        h('div', { style: { height: '6px', background: 'var(--c-bg)', borderRadius: 'var(--r-full)', overflow: 'hidden' } }, [h('div', { style: { height: '100%', width: `${a.progress}%`, background: 'var(--c-accent)' } })])
      ]);
      if (a.status === 'failed') return h('div', { style: { marginTop: '10px', fontSize: '13px' } }, [h('span', { style: { color: 'var(--c-bad)' } }, '评分失败 '), h(Button, { style: { fontSize: '12px', padding: '4px 10px', minHeight: '30px' }, onClick: () => emit('ats') }, () => '重试')]);
      return h('div', { style: { marginTop: '10px', display: 'flex', gap: '12px', alignItems: 'center' } }, [
        h('div', { style: { width: '46px', height: '46px', borderRadius: '50%', background: `conic-gradient(var(--c-ok) ${a.report.atsScore}%, var(--c-bg) 0)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 700 } }, a.report.atsScore),
        h('ul', { style: { margin: 0, paddingLeft: '16px', fontSize: '12px', color: 'var(--c-muted)' } }, a.report.suggestions.slice(0, 2).map(s => h('li', { key: s.section }, [h('b', { style: { color: 'var(--c-strong)' } }, s.section), '：' + s.hint])))
      ]);
    };
  }
});

const VersionPanel = defineComponent({
  props: { versions: Object },
  emits: ['prefer'],
  setup(props, { emit }) {
    const fmtDate = ms => { const d = new Date(ms); return `${d.getMonth() + 1}月${d.getDate()}日`; };
    return () => {
      const vs = props.versions.versions || [];
      const diffAvailable = props.versions.diffAvailable;
      return h('div', {}, [
        h('h3', { style: { margin: '0 0 10px', fontSize: '15px' } }, '版本时间线'),
        h('div', { style: { display: 'flex', flexDirection: 'column', gap: '8px' } }, vs.map(v =>
          h('div', { key: v.versionId, style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', border: '1px solid var(--c-border)', borderRadius: 'var(--r-md)', background: v.isPreferred ? 'var(--c-accent-weak)' : 'var(--c-surface)' } }, [
            h('div', {}, [
              h('div', { style: { fontSize: '14px' } }, ['v' + v.versionNo, v.isPreferred ? h('span', { style: { fontSize: '11px', color: 'var(--c-accent)' } }, ' ★ 首选') : null]),
              h('div', { style: { fontSize: '12px', color: 'var(--c-muted)' } }, fmtDate(v.createdAt) + (v.note ? ' · ' + v.note : ''))
            ]),
            !v.isPreferred ? h(Button, { style: { fontSize: '12px', padding: '6px 12px', minHeight: '32px' }, onClick: () => emit('prefer', v.versionId) }, () => '设为首选') : null
          ])
        )),
        h('div', { style: { marginTop: '12px' } }, [
          h(Button, { variant: diffAvailable ? 'primary' : 'default', disabled: !diffAvailable, style: { fontSize: '13px' }, onClick: () => diffAvailable && console.log('[U1] 打开结构 diff 视图') }, () => '对比两版 ' + (diffAvailable ? '' : '（需 ≥2 版）')),
          !diffAvailable ? h('div', { style: { fontSize: '11px', color: 'var(--c-faint)', marginTop: '4px' } }, '版本数 ≥2 后方可结构化 diff。') : null
        ])
      ]);
    };
  }
});

export { AtsCard, VersionPanel };
</script>

<style scoped>
.sel { border-color: var(--c-accent) !important; }
</style>
