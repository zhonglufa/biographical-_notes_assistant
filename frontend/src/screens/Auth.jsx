// U10 用户与登录（V 阶段生产组件，接入真实 A01/A02/A03）。
// 红线：未登录仅展示引导页，不暴露业务数据（PRD §797）；令牌仅存本机 localStorage（§1012）。
import { useState } from 'react';
import { Card, Button, Toggle } from '../components/UI.jsx';
import { api } from '../lib/api.js';

export default function Auth({ onLogin }) {
  const [channel, setChannel] = useState('email');
  const [email, setEmail] = useState('');
  const [pwd, setPwd] = useState('');
  const [code, setCode] = useState('');
  const [err, setErr] = useState('');

  async function submit() {
    setErr('');
    try {
      const creds = channel === 'email' ? { email, password: pwd } : { email, code };
      const d = await api.login(channel, creds, 'dev-' + Math.random().toString(36).slice(2, 10));
      localStorage.setItem('rat_access_token', d.accessToken);
      localStorage.setItem('rat_refresh_token', d.refreshToken);
      onLogin(d);
    } catch (e) { setErr(e.message || '登录失败'); }
  }

  return (
    <div style={{ maxWidth: 480, margin: '0 auto', padding: '24px 16px 60px' }}>
      <div style={{ textAlign: 'center', padding: '24px 0 8px' }}>
        <div style={{ width: 56, height: 56, borderRadius: 16, background: 'linear-gradient(135deg,var(--c-accent),#7aa2ff)', margin: '0 auto 12px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 24, fontWeight: 700 }}>投</div>
        <h1 style={{ fontSize: 20, margin: '0 0 6px' }}>简历投递助手</h1>
        <p style={{ color: 'var(--c-muted)', fontSize: 14, margin: 0 }}>AI 匹配岗位 · 半自动投递 · 每日日报</p>
      </div>
      <Card>
        <div style={{ display: 'flex', gap: 6, background: 'var(--c-bg)', borderRadius: 'var(--r-md)', padding: 4, marginBottom: 16 }}>
          {['email', 'sms', 'wechat'].map(ch => (
            <button key={ch} onClick={() => { setChannel(ch); setErr(''); }}
              style={{ flex: 1, textAlign: 'center', padding: 9, borderRadius: 'var(--r-sm)', fontSize: 13, cursor: 'pointer', border: 'none', background: channel === ch ? 'var(--c-surface)' : 'transparent', color: channel === ch ? 'var(--c-accent)' : 'var(--c-muted)', fontWeight: channel === ch ? 600 : 400 }}>{ch === 'email' ? '邮箱密码' : ch === 'sms' ? '邮箱验证码' : '微信扫码'}</button>
          ))}
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', fontSize: 13, color: 'var(--c-muted)', marginBottom: 6 }}>邮箱</label>
          <input className="input" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" style={inp} />
        </div>
        {channel === 'email' ? (
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', fontSize: 13, color: 'var(--c-muted)', marginBottom: 6 }}>密码</label>
            <input className="input" type="password" value={pwd} onChange={e => setPwd(e.target.value)} placeholder="••••••••" style={inp} />
          </div>
        ) : channel === 'sms' ? (
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', fontSize: 13, color: 'var(--c-muted)', marginBottom: 6 }}>验证码</label>
            <input className="input" value={code} onChange={e => setCode(e.target.value)} placeholder="6 位验证码" style={inp} />
          </div>
        ) : (
          <div style={{ border: '1px solid var(--c-border)', borderRadius: 'var(--r-md)', padding: 24, textAlign: 'center', color: 'var(--c-faint)', marginBottom: 12 }}>微信扫码登录（失败时回退邮箱）</div>
        )}
        <div className="err" role="alert" aria-live="polite" style={{ color: 'var(--c-bad)', fontSize: 13, marginBottom: 8 }}>{err}</div>
        <Button variant="primary" onClick={submit} style={{ width: '100%' }}>登录</Button>
        <div style={{ fontSize: 12, color: 'var(--c-faint)', marginTop: 10, textAlign: 'center' }}>未登录时仅展示本引导页，不暴露任何业务数据</div>
      </Card>
    </div>
  );
}

const inp = { width: '100%', border: '1px solid var(--c-border)', borderRadius: 'var(--r-md)', padding: '11px 12px', fontSize: 15, minHeight: 44 };
