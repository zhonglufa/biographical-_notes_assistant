// U8 通知中心（V 阶段生产组件，接入真实 A22/A23）。
// 范式：api.notifications(A22) 拉取 → 加载(Skeleton)/数据/错误(ErrorState+重试)；
//       api.notificationWs(A23) 取得 wsUrl → 建连 → 新通知插顶 + 未读+1；断线降级轮询。
import { useState, useEffect, useRef } from 'react';
import { Card, Badge, Skeleton, EmptyState, ErrorState, Modal, Toast } from '../components/UI.jsx';
import { api } from '../lib/api.js';

const LV = { L0: '重要', L1: '重要', L2: '普通', L3: '营销' };
const rel = ms => { const m = Math.floor((Date.now() - ms) / 60000); if (m < 1) return '刚刚'; if (m < 60) return `${m} 分钟前`; const h = Math.floor(m / 60); return h < 24 ? `${h} 小时前` : `${Math.floor(h / 24)} 天前`; };

export default function Notifications() {
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [filter, setFilter] = useState('all');
  const [confirm, setConfirm] = useState(false);
  const [toast, setToast] = useState({ show: false, msg: '', undo: null });
  const [conn, setConn] = useState('live');
  const lastDeleted = useRef(null);
  const undoTimer = useRef(null);

  async function load() {
    setLoading(true); setErr(null);
    try {
      const d = await api.notifications(filter === 'all' ? undefined : filter);
      setItems(d.items); setUnread(d.unread);
    } catch (e) { setErr(e.message || '加载失败'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); connectWs(); /* eslint-disable-next-line */ }, [filter]);

  async function connectWs() {
    try {
      const { wsUrl } = await api.notificationWs();
      const ws = new WebSocket(wsUrl);
      ws.onmessage = () => { load(); };
      ws.onclose = () => { setConn('offline'); poll(); };
      setConn('live');
    } catch { setConn('offline'); poll(); }
  }
  function poll() { const t = setInterval(load, 30000); return () => clearInterval(t); }

  function markRead(id) { setItems(is => is.map(i => i.id === id ? { ...i, read: true } : i)); setUnread(u => Math.max(0, u - 1)); }
  function markAll() { setItems(is => is.map(i => ({ ...i, read: true }))); setUnread(0); setConfirm(false); setToast({ show: true, msg: '已全部标记为已读' }); }
  function del(id) {
    const i = items.findIndex(x => x.id === id); if (i < 0) return;
    lastDeleted.current = { item: items[i], index: i };
    setItems(is => is.filter(x => x.id !== id));
    setToast({ show: true, msg: '通知已删除', undo: () => undo() });
    clearTimeout(undoTimer.current); undoTimer.current = setTimeout(() => setToast(s => ({ ...s, show: false })), 5000);
  }
  function undo() { if (lastDeleted.current) { setItems(is => { const c = [...is]; c.splice(Math.min(lastDeleted.current.index, c.length), 0, lastDeleted.current.item); return c; }); lastDeleted.current = null; } setToast(s => ({ ...s, show: false })); }

  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '24px 16px 60px' }}>
      <div className="rui-card" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        <h1 style={{ fontSize: 18, margin: 0, flex: 1 }}>通知中心</h1>
        <span style={{ fontSize: 12, color: 'var(--c-muted)' }}>{conn === 'live' ? '实时' : '离线(轮询)'}</span>
        <Badge count={unread} />
        <button className="btn" onClick={() => setConfirm(true)} style={{ minHeight: 40 }}>全部已读</button>
      </div>

      <div style={{ display: 'flex', gap: 8, overflowX: 'auto', padding: '4px 0 12px' }}>
        {['all', 'L0', 'L1', 'L2', 'L3'].map(lv => (
          <button key={lv} className={`tab ${filter === lv ? 'active' : ''}`} onClick={() => setFilter(lv)}
            style={{ border: '1px solid var(--c-border)', background: filter === lv ? 'var(--c-accent-weak)' : 'var(--c-surface)', color: filter === lv ? 'var(--c-accent)' : 'var(--c-muted)', borderRadius: 'var(--r-full)', padding: '7px 14px', fontSize: 13, whiteSpace: 'nowrap', cursor: 'pointer', minHeight: 36 }}>{lv === 'all' ? '全部' : lv}</button>
        ))}
      </div>

      {loading ? <Skeleton lines={3} /> : err ? <ErrorState message={err} onRetry={load} /> : items.length === 0 ? <EmptyState hint="暂无通知" /> : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {items.map(n => (
            <div key={n.id} className={`rui-card ${n.read ? 'read' : ''}`} style={{ position: 'relative', display: 'flex', gap: 12, padding: '14px 14px 14px 18px', opacity: n.read ? .72 : 1 }}>
              <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, background: `var(--c-${n.level.toLowerCase()})` }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: n.read ? 500 : 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                  {n.title}
                  <span style={{ fontSize: 11, padding: '1px 7px', borderRadius: 'var(--r-full)', color: '#fff', background: `var(--c-${n.level.toLowerCase()})` }}>{LV[n.level]}</span>
                </div>
                <div style={{ color: 'var(--c-muted)', fontSize: 13, marginTop: 4 }}>{n.body}</div>
                <div style={{ fontSize: 12, color: 'var(--c-faint)', marginTop: 8 }}>{rel(n.createdAt)} · {n.channel === '站内' ? '站内信' : n.channel}</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end' }}>
                {!n.read && <button className="mini" onClick={() => markRead(n.id)} style={{ border: 'none', background: 'transparent', color: 'var(--c-muted)', cursor: 'pointer' }}>标已读</button>}
                <button className="mini" onClick={() => del(n.id)} style={{ border: 'none', background: 'transparent', color: 'var(--c-muted)', cursor: 'pointer' }}>删除</button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={confirm} title="全部标记为已读？" body="将把未读通知设为已读，多端会同步。" onCancel={() => setConfirm(false)} onConfirm={markAll} />
      <Toast show={toast.show} message={toast.msg} onUndo={toast.undo} />
    </div>
  );
}
