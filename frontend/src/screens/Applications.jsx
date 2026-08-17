// U3 投递管理（V 阶段生产组件，接入真实 A09/A10/A11）。
// 产品核心：半自动确认闸门 —— 无静默自动投递；批量/单条确认均经二次确认 + 10s 撤销窗口 + 今日限额可见。
// 交互基线遵循 U11 总纲（加载/错误/空态/无障碍）；响应式 375/768/1280 三档见 <style>。
// 契约对齐：A10 applications-list.response（权威，additionalProperties:false）仅含
//   {applicationId,jobId,platformId,status,appliedAt}；A09/A11 为 pending 契约，
//   本组件按 interaction-U3.md §4/§5 半自动闸门语义建模（A09 支持 confirm/revert 动作）。
//   ⚠️ 合同缺口登记：A10 列表响应当前不含 jobTitle/company，列表标题/公司由本地 mock 补全；
//     真实后端路径回退显示 jobId/platformId。该缺口见 TASK-LOG，非本组件偏离契约。
import { useState, useEffect, useRef } from 'react';
import { Card, Button, Modal, Toast, Skeleton, EmptyState, ErrorState } from '../components/UI.jsx';
import { api } from '../lib/api.js';

const DAILY_LIMIT = 20;

// 10 态线性流（interaction-U3.md §4）；rejected/closed 为终态分支。
const FLOW = ['pending_confirm', 'autofilling', 'submitted', 'viewed', 'contacting', 'interview_invited', 'interview_done', 'offer'];
const STATUS_LABEL = {
  pending_confirm: '待确认', autofilling: '填写中', submitted: '已投递', viewed: '已查看',
  contacting: '沟通中', interview_invited: '面试邀约', interview_done: '面试完成',
  offer: 'Offer', rejected: '未通过', closed: '已关闭',
};
const STATUS_COLOR = {
  pending_confirm: 'neutral', autofilling: 'neutral', submitted: 'ok', viewed: 'ok',
  contacting: 'info', interview_invited: 'accent', interview_done: 'accent',
  offer: 'ok', rejected: 'bad', closed: 'muted',
};
const CHIPS = [
  { key: 'all', label: '全部', status: null },
  { key: 'pending_confirm', label: '待确认', status: 'pending_confirm' },
  { key: 'submitted', label: '已投递', status: 'submitted' },
  { key: 'interview_invited', label: '面试邀约', status: 'interview_invited' },
  { key: 'offer', label: 'Offer', status: 'offer' },
  { key: 'rejected', label: '未通过', status: 'rejected' },
];

const STYLE = `
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
`;

function fmtTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getMonth() + 1}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

export default function Applications() {
  const [filter, setFilter] = useState('all');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [selected, setSelected] = useState(() => new Set());
  const [detailId, setDetailId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingIds, setPendingIds] = useState([]);
  const [toast, setToast] = useState({ show: false, msg: '', undo: false });
  const [undoIds, setUndoIds] = useState(null);
  const undoTimer = useRef(null);

  const chip = CHIPS.find((c) => c.key === filter);

  async function load() {
    setLoading(true); setErr(null);
    try {
      const d = await api.applicationsList(chip ? chip.status : null);
      setItems(d.items || []);
    } catch (e) { setErr(e.message || '加载失败'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [filter]);

  // 今日已投递计数（appliedAt 当天且非待确认/终态）—— 限额可见红线。
  const today0 = new Date(); today0.setHours(0, 0, 0, 0);
  const todayCount = items.filter((it) => it.appliedAt >= today0.getTime() && !['pending_confirm', 'rejected', 'closed'].includes(it.status)).length;
  const limitReached = todayCount >= DAILY_LIMIT;

  function toggle(id, status) {
    if (status !== 'pending_confirm') return;
    setSelected((prev) => { const n = new Set(prev); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  }

  function openBatchConfirm() {
    if (selected.size === 0 || limitReached) return;
    setPendingIds([...selected]);
    setConfirmOpen(true);
  }
  function openSingleConfirm(app) {
    if (app.status !== 'pending_confirm' || limitReached) return;
    setDetailId(null); setDetail(null);
    setPendingIds([app.applicationId]);
    setConfirmOpen(true);
  }

  async function doConfirm() {
    const ids = pendingIds;
    setConfirmOpen(false);
    try {
      await api.batchApplications(ids, 'confirm'); // A09 confirm：pending_confirm → submitted
      setItems((prev) => prev.map((it) => (ids.includes(it.applicationId) ? { ...it, status: 'submitted' } : it)));
      setSelected(() => new Set());
      setUndoIds(ids);
      setToast({ show: true, msg: `已提交 ${ids.length} 份，本机 Agent 将在你的浏览器中执行投递`, undo: true });
      if (undoTimer.current) clearTimeout(undoTimer.current);
      undoTimer.current = setTimeout(() => { setUndoIds(null); setToast((t) => ({ ...t, show: false })); }, 10000);
    } catch (e) {
      setToast({ show: true, msg: e.message || '提交失败', undo: false });
    }
  }
  async function doUndo() {
    const ids = undoIds;
    if (undoTimer.current) clearTimeout(undoTimer.current);
    setUndoIds(null); setToast((t) => ({ ...t, show: false }));
    try {
      await api.batchApplications(ids, 'revert'); // A09 revert：submitted → pending_confirm（10s 窗口内）
      setItems((prev) => prev.map((it) => (ids.includes(it.applicationId) ? { ...it, status: 'pending_confirm' } : it)));
    } catch (e) {
      setToast({ show: true, msg: e.message || '撤销失败，请稍后重试', undo: false });
    }
  }

  useEffect(() => {
    if (!detailId) { setDetail(null); return; }
    setDetailLoading(true);
    api.applicationDetail(detailId)
      .then((d) => setDetail(d))
      .catch(() => setDetail({ error: true }))
      .finally(() => setDetailLoading(false));
  }, [detailId]);

  const pendingApps = items.filter((it) => pendingIds.includes(it.applicationId));
  const dist = {};
  pendingApps.forEach((it) => { dist[it.platformId] = (dist[it.platformId] || 0) + 1; });

  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '24px 16px 60px' }}>
      <style>{STYLE}</style>
      <div className="u3-head">
        <h1 style={{ fontSize: 18, margin: 0 }}>投递管理</h1>
        <span className="u3-limit" aria-live="polite">今日 <b>{todayCount}</b> / 限额 {DAILY_LIMIT}</span>
      </div>

      <div className="u3-chips" role="tablist" aria-label="投递状态筛选">
        {CHIPS.map((c) => (
          <button key={c.key} type="button" className={`u3-chip ${filter === c.key ? 'on' : ''}`} role="tab" aria-selected={filter === c.key}
            onClick={() => { setSelected(() => new Set()); setFilter(c.key); }}>{c.label}</button>
        ))}
      </div>

      <div className="u3-bar">
        <span className="u3-limit">已选 {selected.size} 项</span>
        <Button variant="primary" onClick={openBatchConfirm} disabled={selected.size === 0 || limitReached}>
          {limitReached ? '已达今日限额' : `确认选中并投递（${selected.size}）`}
        </Button>
      </div>
      {limitReached && <div className="u3-confirm-note">已达今日投递限额（{DAILY_LIMIT}），明日 0 点重置。</div>}

      {loading ? <Skeleton lines={4} /> : err ? <ErrorState message={err} onRetry={load} /> : items.length === 0 ? (
        <EmptyState hint="该状态下暂无投递记录" action={<Button onClick={() => setFilter('all')}>查看全部</Button>} />
      ) : (
        <div className="u3-list">
          {items.map((app) => (
            <div className="u3-row" key={app.applicationId}>
              <input className="cb" type="checkbox" disabled={app.status !== 'pending_confirm'}
                checked={selected.has(app.applicationId)} aria-label={`选择 ${app.jobTitle || app.jobId}`}
                onChange={() => toggle(app.applicationId, app.status)} />
              <div className="u3-main">
                <div className="u3-title">{app.jobTitle || app.jobId}</div>
                <div className="u3-sub">{app.company || app.platformId} · {app.platformId}</div>
                <div className="u3-meta">{fmtTime(app.appliedAt)}{app.status === 'pending_confirm' ? ' · 待你确认' : ''}</div>
              </div>
              <div className="u3-right">
                <span className={`u3-badge ${STATUS_COLOR[app.status]}`}>{STATUS_LABEL[app.status]}</span>
                <span className="u3-link" role="button" tabIndex={0}
                  onClick={() => setDetailId(app.applicationId)}
                  onKeyDown={(e) => { if (e.key === 'Enter') setDetailId(app.applicationId); }}>查看详情</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 二次确认闸门（半自动投递红线） */}
      <Modal open={confirmOpen} title="确认投递（半自动闸门）"
        body={
          <div>
            <p style={{ margin: '0 0 8px' }}>即将提交 <b>{pendingIds.length}</b> 份投递，由本机 Agent 在你的浏览器实例中执行。请确认：</p>
            <div className="u3-sm" aria-label="平台分布">
              {Object.entries(dist).map(([p, c]) => <div className="row" key={p}><span>{p}</span><span>{c} 份</span></div>)}
            </div>
            <p className="u3-confirm-note">提交后 10 秒内可一键撤销。</p>
          </div>
        }
        onCancel={() => setConfirmOpen(false)} onConfirm={doConfirm} />

      {/* 详情面板（A11 状态机可视化） */}
      <Modal open={!!detailId} title="投递详情" confirmLabel="关闭" hideConfirm
        body={
          detailLoading ? <Skeleton lines={3} /> :
          detail && detail.error ? <ErrorState message="详情加载失败" onRetry={() => setDetailId(detailId)} /> :
          detail ? <DetailBody app={detail} onConfirmOne={openSingleConfirm} /> : null
        }
        onCancel={() => setDetailId(null)} onConfirm={() => setDetailId(null)} />

      <Toast show={toast.show} message={toast.msg} onUndo={toast.undo ? doUndo : undefined} />
    </div>
  );
}

function DetailBody({ app, onConfirmOne }) {
  const idx = FLOW.indexOf(app.status);
  const terminal = app.status === 'rejected' || app.status === 'closed';
  const steps = terminal ? [app.status] : FLOW;
  return (
    <div>
      <div className="u3-sm">
        <div className="row"><span>岗位</span><span>{app.jobTitle || app.jobId}</span></div>
        <div className="row"><span>公司</span><span>{app.company || '—'}</span></div>
        <div className="row"><span>平台</span><span>{app.platformId}</span></div>
        <div className="row"><span>当前状态</span><span className={`u3-badge ${STATUS_COLOR[app.status]}`}>{STATUS_LABEL[app.status]}</span></div>
        <div className="row"><span>投递时间</span><span>{fmtTime(app.appliedAt)}</span></div>
      </div>
      <div className="u3-flow" aria-label="投递状态机进度">
        {steps.map((s) => {
          let cls = '';
          if (terminal) cls = STATUS_COLOR[s];
          else if (s === app.status) cls = 'cur ' + STATUS_COLOR[s];
          else if (FLOW.indexOf(s) < idx) cls = 'done';
          const mark = cls.startsWith('done') || cls.startsWith('cur') ? '✓' : '';
          return (
            <div className={`u3-step ${cls}`} key={s}>
              <span className="u3-dot">{mark}</span>
              <span>{STATUS_LABEL[s]}</span>
            </div>
          );
        })}
      </div>
      {app.status === 'pending_confirm' && (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button variant="primary" onClick={() => onConfirmOne(app)}>确认并投递这一个</Button>
        </div>
      )}
    </div>
  );
}
