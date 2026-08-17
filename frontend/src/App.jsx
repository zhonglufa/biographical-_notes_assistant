// 应用壳 + 路由守卫（AuthGuard）：未登录 → Auth；已登录 → 业务路由。
// PRD §797 红线：未登录不暴露任何业务数据。
import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './screens/Auth.jsx';
import Notifications from './screens/Notifications.jsx';
import { api } from './lib/api.js';
import { Card, Toggle } from './components/UI.jsx';

function Account() {
  const [me, setMe] = useState(null);
  useEffect(() => { api.me().then(setMe).catch(() => {}); }, []);
  if (!me) return <div style={{ padding: 24 }}>加载账户…</div>;
  return (
    <div style={{ maxWidth: 480, margin: '0 auto', padding: '24px 16px' }}>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', background: 'var(--c-accent-weak)', borderRadius: 'var(--r-md)', padding: 14, marginBottom: 14 }}>
          <div><div style={{ fontWeight: 700, color: 'var(--c-accent)' }}>{me.plan} 版</div><div style={{ fontSize: 12, color: 'var(--c-muted)' }}>解锁 100 份/天</div></div>
          <span style={{ fontSize: 12, background: 'var(--c-accent)', color: '#fff', borderRadius: 'var(--r-full)', padding: '2px 10px' }}>当前套餐</span>
        </div>
        <div style={{ marginBottom: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--c-muted)', marginBottom: 6 }}><span>今日套餐额度</span><span>{me.quotaUsed} / {me.quotaLimit || '不限'}</span></div>
          <div style={{ height: 10, background: 'var(--c-bg)', borderRadius: 'var(--r-full)', overflow: 'hidden' }}><div style={{ height: '100%', width: me.quotaLimit ? `${me.quotaUsed / me.quotaLimit * 100}%` : '0%', background: 'var(--c-accent)' }} /></div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '13px 0', borderBottom: '1px solid var(--c-border)', fontSize: 14 }}>邮箱 <span style={{ color: 'var(--c-muted)' }}>{me.email || '—'}</span></div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '13px 0', fontSize: 14 }}>本机 Agent 登录态（Cookie 仅存本机） <Toggle on onChange={() => {}} /></div>
        <div style={{ marginTop: 18, color: 'var(--c-bad)', cursor: 'pointer', textAlign: 'right' }}
          onClick={() => { localStorage.removeItem('rat_access_token'); localStorage.removeItem('rat_refresh_token'); window.location.reload(); }}>退出并清除本机凭据 ›</div>
      </Card>
    </div>
  );
}

function Shell({ user }) {
  return (
    <div className="app-shell" style={{ display: 'grid', gridTemplateColumns: '232px 1fr', minHeight: '100vh' }}>
      <aside className="app-side" style={{ background: 'var(--c-surface)', borderRight: '1px solid var(--c-border)', padding: 16, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <strong style={{ padding: '8px 10px' }}>简历投递助手</strong>
        <a href="#/notifications" style={nav}>通知中心</a>
        <a href="#/account" style={nav}>我的</a>
      </aside>
      <main style={{ padding: 8 }}>
        <Routes>
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/account" element={<Account />} />
          <Route path="*" element={<Navigate to="/notifications" replace />} />
        </Routes>
      </main>
    </div>
  );
}
const nav = { padding: '9px 10px', borderRadius: 'var(--r-sm)', color: 'var(--c-muted)', textDecoration: 'none', fontSize: 14 };

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('rat_access_token'));
  if (!token) return <Auth onLogin={() => { setToken(localStorage.getItem('rat_access_token')); }} />;
  return <BrowserRouter><Shell user={token} /></BrowserRouter>;
}
