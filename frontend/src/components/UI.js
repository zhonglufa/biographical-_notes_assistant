// 共享组件库 —— 实现 U11 交互设计总纲的模式库（§1–§6）。
// 各屏统一复用，避免交互漂移；动效时长/缓动引用 tokens.css 的 --d-* / --e-*。
// 本文件用 Vue 渲染函数 h() 实现，不依赖 JSX 插件，保持构建简单。
import { h, defineComponent } from 'vue';

export const Card = defineComponent({
  name: 'RuiCard',
  props: { className: { type: String, default: '' } },
  setup(props, { slots }) {
    return () => h('div', {
      class: `rui-card ${props.className}`,
      style: { background: 'var(--c-surface)', border: '1px solid var(--c-border)', borderRadius: 'var(--r-lg)', padding: '18px', boxShadow: 'var(--shadow)' }
    }, slots.default?.());
  }
});

export const Button = defineComponent({
  name: 'RuiButton',
  props: { variant: { type: String, default: 'default' } },
  emits: ['click'],
  setup(props, { slots, emit, attrs }) {
    const base = { borderRadius: 'var(--r-md)', padding: '11px 16px', fontSize: '15px', minHeight: '44px', cursor: 'pointer', border: '1px solid var(--c-border)', background: 'var(--c-surface)' };
    const style = props.variant === 'primary'
      ? { ...base, background: 'var(--c-accent)', borderColor: 'var(--c-accent)', color: '#fff', fontWeight: 600 }
      : base;
    return () => h('button', { class: 'btn', style, onClick: () => emit('click'), ...attrs }, slots.default?.());
  }
});

export const Badge = defineComponent({
  name: 'RuiBadge',
  props: { count: { type: Number, default: 0 } },
  setup(props) {
    const zero = !props.count;
    const style = { minWidth: '22px', height: '22px', padding: '0 7px', borderRadius: 'var(--r-full)', background: zero ? 'var(--c-border)' : 'var(--c-l0)', color: zero ? 'var(--c-faint)' : '#fff', fontSize: '12px', fontWeight: 700, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' };
    return () => h('span', { class: 'badge', style }, props.count || 0);
  }
});

export const Toggle = defineComponent({
  name: 'RuiToggle',
  props: { on: { type: Boolean, default: false } },
  emits: ['change'],
  setup(props, { emit }) {
    return () => h('div', {
      class: `toggle ${props.on ? 'on' : ''}`,
      role: 'switch',
      'aria-checked': props.on,
      onClick: () => emit('change', !props.on),
      style: { width: '48px', height: '28px', borderRadius: 'var(--r-full)', background: props.on ? 'var(--c-ok)' : 'var(--c-border)', position: 'relative', cursor: 'pointer' }
    }, [
      h('div', { class: 'kn', style: { position: 'absolute', top: '3px', left: props.on ? '23px' : '3px', width: '22px', height: '22px', background: '#fff', borderRadius: '50%', transition: 'left var(--d-base) var(--e-out)' } })
    ]);
  }
});

export const Skeleton = defineComponent({
  name: 'RuiSkeleton',
  props: { lines: { type: Number, default: 3 } },
  setup(props) {
    return () => h('div', {}, Array.from({ length: props.lines }).map((_, i) =>
      h('div', {
        key: i,
        class: 'rui-skeleton',
        style: { height: '56px', borderRadius: 'var(--r-lg)', background: 'linear-gradient(90deg,#eef1f6 25%,#e3e8f0 37%,#eef1f6 63%)', backgroundSize: '400% 100%', animation: 'rui-sk 1.3s infinite', marginBottom: '10px' }
      })
    ));
  }
});

export const EmptyState = defineComponent({
  name: 'RuiEmptyState',
  props: { hint: { type: String, default: '' } },
  setup(props, { slots }) {
    return () => h('div', { style: { border: '2px dashed var(--c-border)', borderRadius: 'var(--r-lg)', padding: '30px', textAlign: 'center', color: 'var(--c-faint)' } }, [
      props.hint,
      slots.action ? h('div', { style: { marginTop: '12px' } }, slots.action()) : null
    ]);
  }
});

export const ErrorState = defineComponent({
  name: 'RuiErrorState',
  props: { message: { type: String, default: '' } },
  emits: ['retry'],
  setup(props, { emit, slots }) {
    return () => h('div', { role: 'alert', 'aria-live': 'polite', style: { color: 'var(--c-bad)', padding: '16px', textAlign: 'center' } }, [
      props.message,
      slots.retry ? h('div', { style: { marginTop: '10px' } }, slots.retry()) : null
    ]);
  }
});

export const Modal = defineComponent({
  name: 'RuiModal',
  props: {
    open: { type: Boolean, default: false },
    title: { type: String, default: '' },
    confirmLabel: { type: String, default: '确认' },
    hideConfirm: { type: Boolean, default: false }
  },
  emits: ['cancel', 'confirm'],
  setup(props, { slots, emit }) {
    return () => {
      if (!props.open) return null;
      return h('div', {
        class: 'modal-mask',
        style: { position: 'fixed', inset: 0, background: 'rgba(20,30,50,.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', zIndex: 20 },
        onClick: () => emit('cancel')
      }, [
        h('div', {
          class: 'modal',
          style: { background: '#fff', borderRadius: 'var(--r-lg)', padding: '22px', maxWidth: '360px', width: '100%', maxHeight: '90vh', overflowY: 'auto' },
          onClick: e => e.stopPropagation()
        }, [
          h('h3', { style: { margin: '0 0 8px', fontSize: '16px' } }, props.title),
          h('div', { style: { color: 'var(--c-muted)', fontSize: '14px', margin: '0 0 18px' } }, slots.default?.()),
          h('div', { style: { display: 'flex', gap: '10px', justifyContent: 'flex-end' } }, [
            h(Button, { onClick: () => emit('cancel') }, () => '取消'),
            props.hideConfirm ? null : h(Button, { variant: 'primary', onClick: () => emit('confirm') }, () => props.confirmLabel)
          ])
        ])
      ]);
    };
  }
});

export const Toast = defineComponent({
  name: 'RuiToast',
  props: { message: { type: String, default: '' }, show: { type: Boolean, default: false } },
  emits: ['undo'],
  setup(props, { emit }) {
    return () => h('div', {
      class: `toast ${props.show ? 'show' : ''}`,
      style: {
        position: 'fixed', left: '50%', bottom: '24px',
        transform: props.show ? 'translateX(-50%) translateY(0)' : 'translateX(-50%) translateY(20px)',
        opacity: props.show ? 1 : 0,
        background: '#1f2733', color: '#fff', padding: '11px 18px', borderRadius: 'var(--r-full)',
        transition: 'all var(--d-base) var(--e-out)', zIndex: 30, pointerEvents: props.show ? 'auto' : 'none'
      }
    }, [
      props.message,
      emit('undo') ? h('span', {
        class: 'undo',
        onClick: () => emit('undo'),
        style: { color: '#7eb0ff', marginLeft: '12px', cursor: 'pointer', fontWeight: 600 }
      }, '撤销') : null
    ]);
  }
});
