// 共享组件库 —— 实现 U11 交互设计总纲的模式库（§1–§6）。
// 各屏统一复用，避免交互漂移；动效时长/缓动引用 tokens.css 的 --d-* / --e-*。
import { useState, useEffect } from 'react';

export function Card({ children, className = '' }) {
  return <div className={`rui-card ${className}`} style={{ background: 'var(--c-surface)', border: '1px solid var(--c-border)', borderRadius: 'var(--r-lg)', padding: 18, boxShadow: 'var(--shadow)' }}>{children}</div>;
}

export function Button({ variant = 'default', children, ...p }) {
  const base = { borderRadius: 'var(--r-md)', padding: '11px 16px', fontSize: 15, minHeight: 44, cursor: 'pointer', border: '1px solid var(--c-border)', background: 'var(--c-surface)' };
  const styles = variant === 'primary' ? { ...base, background: 'var(--c-accent)', borderColor: 'var(--c-accent)', color: '#fff', fontWeight: 600 } : base;
  return <button className="btn" style={styles} {...p}>{children}</button>;
}

export function Badge({ count }) {
  if (!count) return <span className="badge zero" style={badgeStyle(true)}>0</span>;
  return <span className="badge" style={badgeStyle(false)}>{count}</span>;
}
function badgeStyle(zero) {
  return { minWidth: 22, height: 22, padding: '0 7px', borderRadius: 'var(--r-full)', background: zero ? 'var(--c-border)' : 'var(--c-l0)', color: zero ? 'var(--c-faint)' : '#fff', fontSize: 12, fontWeight: 700, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' };
}

export function Toggle({ on, onChange }) {
  return <div className={`toggle ${on ? 'on' : ''}`} role="switch" aria-checked={on} onClick={() => onChange(!on)} style={{ width: 48, height: 28, borderRadius: 'var(--r-full)', background: on ? 'var(--c-ok)' : 'var(--c-border)', position: 'relative', cursor: 'pointer' }}><div className="kn" style={{ position: 'absolute', top: 3, left: on ? 23 : 3, width: 22, height: 22, background: '#fff', borderRadius: '50%', transition: 'left var(--d-base) var(--e-out)' }} /></div>;
}

export function Skeleton({ lines = 3 }) {
  return <div>{Array.from({ length: lines }).map((_, i) => <div key={i} className="rui-skeleton" style={{ height: 56, borderRadius: 'var(--r-lg)', background: 'linear-gradient(90deg,#eef1f6 25%,#e3e8f0 37%,#eef1f6 63%)', backgroundSize: '400% 100%', animation: 'rui-sk 1.3s infinite', marginBottom: 10 }} />)}</div>;
}

export function EmptyState({ hint, action }) {
  return <div style={{ border: '2px dashed var(--c-border)', borderRadius: 'var(--r-lg)', padding: 30, textAlign: 'center', color: 'var(--c-faint)' }}>{hint}{action && <div style={{ marginTop: 12 }}>{action}</div>}</div>;
}

export function ErrorState({ message, onRetry }) {
  return <div role="alert" aria-live="polite" style={{ color: 'var(--c-bad)', padding: 16, textAlign: 'center' }}>{message}{onRetry && <div style={{ marginTop: 10 }}><Button onClick={onRetry}>重试</Button></div>}</div>;
}

export function Modal({ open, title, body, children, onCancel, onConfirm, confirmLabel = '确认', hideConfirm = false }) {
  if (!open) return null;
  const content = children || body;
  return <div className="modal-mask" style={{ position: 'fixed', inset: 0, background: 'rgba(20,30,50,.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, zIndex: 20 }} onClick={onCancel}>
    <div className="modal" style={{ background: '#fff', borderRadius: 'var(--r-lg)', padding: 22, maxWidth: 360, width: '100%', maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
      <h3 style={{ margin: '0 0 8px', fontSize: 16 }}>{title}</h3>
      <div style={{ color: 'var(--c-muted)', fontSize: 14, margin: '0 0 18px' }}>{content}</div>
      <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
        <Button onClick={onCancel}>取消</Button>{!hideConfirm && <Button variant="primary" onClick={onConfirm}>{confirmLabel}</Button>}
      </div>
    </div>
  </div>;
}

export function Toast({ message, onUndo, show }) {
  return <div className={`toast ${show ? 'show' : ''}`} style={{ position: 'fixed', left: '50%', bottom: 24, transform: show ? 'translateX(-50%) translateY(0)' : 'translateX(-50%) translateY(20px)', opacity: show ? 1 : 0, background: '#1f2733', color: '#fff', padding: '11px 18px', borderRadius: 'var(--r-full)', transition: 'all var(--d-base) var(--e-out)', zIndex: 30 }}>
    {message}{onUndo && <span className="undo" onClick={onUndo} style={{ color: '#7eb0ff', marginLeft: 12, cursor: 'pointer', fontWeight: 600 }}>撤销</span>}
  </div>;
}
