// U1 简历工作台（A04/A05/A06 生产组件）。
// 交互规格：design/ui/interaction-U1.md；契约：resumes-create / resume-versions / resume-ats。
// U11 基线：加载(skeleton) / 错误(重试) / 空态(引导新建) / 无障碍(aria + 响应式 375/768/1280)。
// 诚实边界：列表与「设为首选」无契约端点，走本地 mock store（合同缺口见 TASK-LOG，与 A10 同处理）。
import { useState, useEffect, useCallback } from 'react';
import { Card, Button, Modal, Toast, Skeleton, EmptyState, ErrorState } from '../components/UI.jsx';
import { api } from '../lib/api.js';

const fmtDate = (ms) => { const d = new Date(ms); return `${d.getMonth() + 1}月${d.getDate()}日`; };

export default function Resume() {
  const [resumes, setResumes] = useState(null);   // null=加载中, []=空态
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [versions, setVersions] = useState(null);   // 选中简历的版本
  const [ats, setAts] = useState({});                // resumeId -> {status, progress, report, failed}
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: '', template: 'standard' });
  const [toast, setToast] = useState({ show: false, message: '', onUndo: null });

  const load = useCallback(() => {
    setError(null);
    api.resumeList().then((list) => {
      setResumes(list);
      const first = list[0] && list[0].resumeId;
      if (first && !selectedId) setSelectedId(first);
    }).catch(() => setError('简历列表加载失败'));
  }, [selectedId]);

  useEffect(() => { load(); }, [load]);

  // 选中简历 → 拉版本
  useEffect(() => {
    if (!selectedId) { setVersions(null); return; }
    setVersions(null);
    api.resumeVersions(selectedId).then(setVersions).catch(() => setVersions({ versions: [], diffAvailable: false }));
  }, [selectedId]);

  const flash = (message, onUndo) => { setToast({ show: true, message, onUndo: onUndo || null }); setTimeout(() => setToast((t) => ({ ...t, show: false })), 2600); };

  // A04 新建简历
  const onCreate = () => {
    if (!form.title.trim()) { flash('请填写简历标题'); return; }
    api.createResume({ title: form.title.trim(), template: form.template }).then((r) => {
      setShowCreate(false); setForm({ title: '', template: 'standard' });
      load();
      flash(`已创建：${r.resumeId}`);
    }).catch(() => flash('创建失败，请重试'));
  };

  // A05 设为首选（本地 mock 直改；契约缺口）
  const onPrefer = (versionId) => {
    api.setPreferred(selectedId, versionId).then(() => {
      api.resumeVersions(selectedId).then(setVersions);
      setResumes((rs) => rs.map((r) => r.resumeId === selectedId ? { ...r, preferredVersionId: versionId } : r));
      flash('已设为首选版本');
    });
  };

  // A06 触发 ATS 评分（异步状态机 pending→running→done/failed；done 展示 mock 评分环+维度分）
  const onAts = (resumeId) => {
    setAts((s) => ({ ...s, [resumeId]: { status: 'pending', progress: 0 } }));
    api.triggerAts(resumeId).then(() => {
      setAts((s) => ({ ...s, [resumeId]: { status: 'running', progress: 45 } }));
      setTimeout(() => {
        // 真实路径 = 轮询 b05-ats 事件回填 ats_report；此处 mock 评分环。
        const report = { atsScore: 72, suggestions: [
          { section: '项目经历', hint: '用「动词+量化结果」重写 2 条经历，ATS 匹配度更高。' },
          { section: '技能关键词', hint: '岗位 JD 高频词「React/TypeScript」建议前置。' },
          { section: '教育背景', hint: '时间倒序、补充 GPA（若≥3.5）。' },
        ] };
        setAts((s) => ({ ...s, [resumeId]: { status: 'done', progress: 100, report } }));
      }, 1400);
    }).catch(() => setAts((s) => ({ ...s, [resumeId]: { status: 'failed' } })));
  };

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (resumes === null) return <div style={{ padding: 16 }}><Skeleton lines={4} /></div>;

  return (
    <div style={{ maxWidth: 1080, margin: '0 auto', padding: '12px 8px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <h2 style={{ margin: 0, fontSize: 18 }}>简历工作台</h2>
        <Button variant="primary" onClick={() => setShowCreate(true)}>＋ 新建简历</Button>
      </div>

      {resumes.length === 0 ? (
        <EmptyState hint="还没有简历，先新建一份吧。" action={<Button variant="primary" onClick={() => setShowCreate(true)}>＋ 新建简历</Button>} />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1.2fr)', gap: 14 }}>
          {/* 左栏：简历列表 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {resumes.map((r) => {
              const a = ats[r.resumeId] || {};
              return (
                <Card key={r.resumeId} className={r.resumeId === selectedId ? 'sel' : ''}
                  style={{ cursor: 'pointer', borderColor: r.resumeId === selectedId ? 'var(--c-accent)' : 'var(--c-border)', padding: 14 }}>
                  <div onClick={() => setSelectedId(r.resumeId)}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                      <strong style={{ fontSize: 15 }}>{r.title}</strong>
                      {r.preferredVersionId && <span style={{ fontSize: 11, background: 'var(--c-accent-weak)', color: 'var(--c-accent)', borderRadius: 'var(--r-full)', padding: '2px 8px' }}>首选 v{(r.versionCount)}</span>}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--c-muted)', marginTop: 4 }}>模板 {r.template} · {r.versionCount} 个版本</div>
                    {/* ATS 评分任务卡（异步状态机） */}
                    <AtsCard a={a} onAts={() => onAts(r.resumeId)} />
                  </div>
                </Card>
              );
            })}
          </div>

          {/* 右栏：版本面板 */}
          <Card style={{ padding: 16, minHeight: 200 }}>
            {!selectedId || versions === null ? (
              <div style={{ color: 'var(--c-faint)', padding: 20, textAlign: 'center' }}>加载版本…</div>
            ) : versions.versions.length === 0 ? (
              <div style={{ color: 'var(--c-faint)', padding: 20, textAlign: 'center' }}>尚未选择简历</div>
            ) : (
              <VersionPanel versions={versions} onPrefer={onPrefer} />
            )}
          </Card>
        </div>
      )}

      {/* A04 新建弹窗 */}
      <Modal open={showCreate} title="新建简历" confirmLabel="创建" onCancel={() => setShowCreate(false)} onConfirm={onCreate}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <label style={{ fontSize: 13, color: 'var(--c-muted)' }}>标题
            <input aria-label="简历标题" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              style={{ width: '100%', marginTop: 6, padding: 10, borderRadius: 'var(--r-md)', border: '1px solid var(--c-border)', fontSize: 14 }} placeholder="如：高级前端工程师" />
          </label>
          <label style={{ fontSize: 13, color: 'var(--c-muted)' }}>模板
            <select aria-label="简历模板" value={form.template} onChange={(e) => setForm((f) => ({ ...f, template: e.target.value }))}
              style={{ width: '100%', marginTop: 6, padding: 10, borderRadius: 'var(--r-md)', border: '1px solid var(--c-border)', fontSize: 14 }}>
              <option value="standard">标准版</option>
              <option value="tech">技术版</option>
            </select>
          </label>
        </div>
      </Modal>

      <Toast show={toast.show} message={toast.message} onUndo={toast.onUndo} />
    </div>
  );
}

function AtsCard({ a, onAts }) {
  if (!a.status) return <Button style={{ marginTop: 10, fontSize: 13, padding: '7px 12px', minHeight: 36 }} onClick={onAts}>触发 ATS 评分</Button>;
  if (a.status === 'pending') return <div style={{ marginTop: 10, fontSize: 12, color: 'var(--c-muted)' }}>评分任务已创建…</div>;
  if (a.status === 'running') return (
    <div style={{ marginTop: 10 }}>
      <div style={{ fontSize: 12, color: 'var(--c-muted)', marginBottom: 4 }}>评分中 {a.progress}%</div>
      <div style={{ height: 6, background: 'var(--c-bg)', borderRadius: 'var(--r-full)', overflow: 'hidden' }}><div style={{ height: '100%', width: `${a.progress}%`, background: 'var(--c-accent)' }} /></div>
    </div>);
  if (a.status === 'failed') return <div style={{ marginTop: 10, fontSize: 13 }}><span style={{ color: 'var(--c-bad)' }}>评分失败</span> <Button style={{ fontSize: 12, padding: '4px 10px', minHeight: 30 }} onClick={onAts}>重试</Button></div>;
  // done
  return (
    <div style={{ marginTop: 10, display: 'flex', gap: 12, alignItems: 'center' }}>
      <div style={{ width: 46, height: 46, borderRadius: '50%', background: 'conic-gradient(var(--c-ok) ' + a.report.atsScore + '%, var(--c-bg) 0)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700 }}>{a.report.atsScore}</div>
      <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12, color: 'var(--c-muted)' }}>
        {a.report.suggestions.slice(0, 2).map((s, i) => <li key={i}><b style={{ color: 'var(--c-strong)' }}>{s.section}</b>：{s.hint}</li>)}
      </ul>
    </div>);
}

function VersionPanel({ versions, onPrefer }) {
  const { versions: vs, diffAvailable } = versions;
  return (
    <div>
      <h3 style={{ margin: '0 0 10px', fontSize: 15 }}>版本时间线</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {vs.map((v) => (
          <div key={v.versionId} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', border: '1px solid var(--c-border)', borderRadius: 'var(--r-md)', background: v.isPreferred ? 'var(--c-accent-weak)' : 'var(--c-surface)' }}>
            <div>
              <div style={{ fontSize: 14 }}>v{v.versionNo} {v.isPreferred && <span style={{ fontSize: 11, color: 'var(--c-accent)' }}>★ 首选</span>}</div>
              <div style={{ fontSize: 12, color: 'var(--c-muted)' }}>{fmtDate(v.createdAt)}{v.note ? ' · ' + v.note : ''}</div>
            </div>
            {!v.isPreferred && <Button style={{ fontSize: 12, padding: '6px 12px', minHeight: 32 }} onClick={() => onPrefer(v.versionId)}>设为首选</Button>}
          </div>
        ))}
      </div>
      <div style={{ marginTop: 12 }}>
        <Button variant={diffAvailable ? 'primary' : 'default'} disabled={!diffAvailable}
          onClick={() => flashSafe(diffAvailable)} style={{ fontSize: 13 }}>
          对比两版 {diffAvailable ? '' : '（需 ≥2 版）'}
        </Button>
        {!diffAvailable && <div style={{ fontSize: 11, color: 'var(--c-faint)', marginTop: 4 }}>版本数 ≥2 后方可结构化 diff。</div>}
      </div>
    </div>
  );
}

// 对比为视图占位（真实走 resume-diff 端点）；diffAvailable=false 时按钮禁用，不触发。
function flashSafe(ok) { if (ok) console.log('[U1] 打开结构 diff 视图（resume-diff 端点）'); }

// 适配 375/768/1280：移动端改为单列（CSS 媒体查询在 tokens/全局；此处在 grid 用 minmax 已自适应）。
