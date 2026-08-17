// U9 每日日报（V 阶段生产组件，接入真实 A24/A25）。
// 范式（与 U8 对齐）：api.dailyReport(A24) 拉取 → 加载(Skeleton)/数据/错误(ErrorState+重试)/空态(无活动)；
//       api.saveDailyPref(A25) 保存偏好 → loading + Toast 反馈；非法时间前端拦截不请求。
// 交互基线遵循 U11 总纲（加载/错误/空态/无障碍）；响应式 375/768/1280 三档见下方 <style>。
import { useState, useEffect } from 'react';
import { Card, Button, Toggle, Skeleton, EmptyState, ErrorState, Toast } from '../components/UI.jsx';
import { api } from '../lib/api.js';

// 组件内响应式样式（与设计 HTML 原型同源；token 取自 tokens.css 全局变量）。
const STYLE = `
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
`;

export default function DailyReport() {
  const [report, setReport] = useState(null);
  const [pref, setPref] = useState({ pushTime: '20:00', enabled: true });
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState({ show: false, msg: '' });

  async function load() {
    setLoading(true); setErr(null);
    try {
      const d = await api.dailyReport();   // A24
      setReport(d);
    } catch (e) { setErr(e.message || '加载失败'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const stats = report && report.stats;
  const total = stats && stats.byPlatform ? stats.byPlatform.reduce((s, p) => s + p.count, 0) : 0;
  const maxTrend = stats && stats.trend7d && stats.trend7d.length ? Math.max(...stats.trend7d.map(t => t.count)) : 0;
  const noActivity = report && (stats && stats.appliedTotal || 0) === 0 && (!stats || !stats.byPlatform || stats.byPlatform.length === 0);

  async function save() {
    if (!/^\d{2}:\d{2}$/.test(pref.pushTime)) { setToast({ show: true, msg: '时间格式不正确' }); return; }
    setSaving(true);
    try {
      await api.saveDailyPref(pref.pushTime, pref.enabled);   // A25
      setToast({ show: true, msg: `已保存：推送 ${pref.pushTime}，${pref.enabled ? '开启' : '关闭'}` });
    } catch (e) { setToast({ show: true, msg: e.message || '保存失败' }); }
    finally {
      setSaving(false);
      setTimeout(() => setToast(s => ({ ...s, show: false })), 2400);
    }
  }

  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '24px 16px 60px' }}>
      <style>{STYLE}</style>
      <h1 style={{ fontSize: 18, margin: '0 0 14px' }}>每日日报</h1>

      {loading ? <Skeleton lines={3} /> : err ? <ErrorState message={err} onRetry={load} /> : noActivity ? (
        <EmptyState hint="今日无投递活动 · 系统不会发送空日报" />
      ) : (
        <>
          <Card>
            <div style={{ fontSize: 14, color: 'var(--c-muted)', marginBottom: 10 }}>{report.summary}</div>
            <div className="u9-grid">
              <Stat n={stats.appliedTotal} l="今日投递总数" cls="acc" />
              <Stat n={stats.success} l="成功" cls="ok" />
              <Stat n={stats.failed} l="失败" cls="bad" />
              <Stat n={stats.hrViews} l="HR 查看" />
              <Stat n={stats.interviewInvites} l="面试邀请" />
              <Stat n={stats.newQuestions} l="新增面试题" />
            </div>
          </Card>

          <Card>
            <h2 style={{ fontSize: 16, margin: '0 0 12px' }}>各平台投递分布</h2>
            <div className="u9-bars">
              {stats.byPlatform.map(p => (
                <div className="u9-bar-row" key={p.platformId}>
                  <span className="nm">{p.platformId}</span>
                  <span className="track"><span className="fill" style={{ width: `${total ? Math.round(p.count / total * 100) : 0}%` }} /></span>
                  <span className="ct">{p.count}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <h2 style={{ fontSize: 16, margin: '0 0 12px' }}>近 7 天趋势</h2>
            <div className="u9-trend">
              {stats.trend7d.map((t, i) => (
                <div className="u9-col" key={t.date}>
                  <div className={`u9-bar ${i === stats.trend7d.length - 1 ? 't' : ''}`} style={{ height: `${maxTrend ? Math.round(t.count / maxTrend * 80) : 0}px` }} />
                  <div className="day">{t.date.slice(3)}</div>
                </div>
              ))}
            </div>
            {/* 无障碍（U11 §6）：图表附数据表供读屏 */}
            <table className="u9-tbl"><thead><tr><th>日期</th><th>投递量</th></tr></thead><tbody>
              {stats.trend7d.map(t => <tr key={t.date}><td>{t.date}</td><td>{t.count}</td></tr>)}
            </tbody></table>
          </Card>

          <Card>
            <h2 style={{ fontSize: 16, margin: '0 0 12px' }}>日报推送设置（A25）</h2>
            <div className="u9-pref">
              <div><div className="lab">推送时间</div><div className="sub">默认 20:00，日报准时送达</div></div>
              <input className="u9-time" type="time" value={pref.pushTime} onChange={e => setPref(p => ({ ...p, pushTime: e.target.value }))} aria-label="日报推送时间" />
            </div>
            <div className="u9-pref">
              <div><div className="lab">开启日报推送</div><div className="sub">{pref.enabled ? '开启后每日推送投递日报' : '已关闭日报推送'}</div></div>
              <Toggle on={pref.enabled} onChange={v => setPref(p => ({ ...p, enabled: v }))} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 12 }}>
              <Button variant="primary" onClick={save} disabled={saving}>{saving ? '保存中…' : '保存设置'}</Button>
            </div>
          </Card>
        </>
      )}
      <Toast show={toast.show} message={toast.msg} />
    </div>
  );
}

function Stat({ n, l, cls }) {
  return <div className={`u9-stat ${cls || ''}`} aria-label={`${l}：${n}`}><div className="n">{n}</div><div className="l">{l}</div></div>;
}
