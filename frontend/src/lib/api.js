// A01–A25 契约 API 客户端（V 阶段生产前端）。
// 设计原则（红线/诚实边界）：
//  - 不硬编码任何密钥/平台 Cookie；访问令牌仅存本机 localStorage（PRD §1012）。
//  - 无真实后端时（本地 dev），若 VITE_USE_MOCK=true 则走与契约同形的本地 mock，便于联调；生产必须连真实后端。
//  - 所有响应解析严格匹配 design/contracts 下 schema（见 external-api.registry.json）。

const BASE = import.meta.env.VITE_API_BASE || '/api/v1';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

// A01–A25 端点映射（与 external-api.registry.json 一一对应）
export const ENDPOINTS = {
  A01: { method: 'POST', path: '/auth/login' },
  A02: { method: 'POST', path: '/auth/refresh' },
  A03: { method: 'GET', path: '/users/me' },
  A04: { method: 'POST', path: '/resume' },
  A05: { method: 'GET', path: '/resume/versions' },
  A06: { method: 'GET', path: '/resume/ats-score' },
  A07: { method: 'GET', path: '/jobs/search' },
  A08: { method: 'POST', path: '/jobs/favorite' },
  A09: { method: 'POST', path: '/applications/batch' },
  A10: { method: 'GET', path: '/applications' },
  A11: { method: 'GET', path: '/applications/{id}' },
  A12: { method: 'GET', path: '/strategies' },
  A13: { method: 'PUT', path: '/strategies' },
  A14: { method: 'GET', path: '/adapters' },
  A15: { method: 'POST', path: '/adapters/{id}/enable' },
  A16: { method: 'GET', path: '/interview/questions' },
  A17: { method: 'POST', path: '/interview/sessions' },
  A18: { method: 'POST', path: '/interview/sessions/{id}/answer' },
  A19: { method: 'GET', path: '/interview/sessions/{id}/report' },
  A20: { method: 'POST', path: '/orders' },
  A21: { method: 'POST', path: '/orders/{id}/callback' },
  A22: { method: 'GET', path: '/notifications' },
  A23: { method: 'GET', path: '/notifications/ws' },
  A24: { method: 'GET', path: '/daily-report/today' },
  A25: { method: 'PUT', path: '/users/daily-report/preference' },
};

function token() {
  return localStorage.getItem('rat_access_token') || '';
}

async function request(id, { params, body, auth = true } = {}) {
  const ep = ENDPOINTS[id];
  if (!ep) throw new Error(`未知端点 ${id}`);
  let url = BASE + ep.path;
  if (params) Object.entries(params).forEach(([k, v]) => { url = url.replace(`{${k}}`, encodeURIComponent(v)); });
  if (ep.method === 'GET' && body) {
    const qs = new URLSearchParams(body).toString();
    if (qs) url += `?${qs}`;
  }
  const headers = { 'Content-Type': 'application/json' };
  if (auth && token()) headers['Authorization'] = `Bearer ${token()}`;

  if (USE_MOCK) return mockResponse(id, body, params);

  const res = await fetch(url, {
    method: ep.method,
    headers,
    body: ep.method !== 'GET' && body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401 && id !== 'A01' && id !== 'A02') {
    // A02 静默刷新（U10 架构师约定）
    const ok = await refresh();
    if (ok) return request(id, { params, body, auth });
    throw new ApiError('UNAUTH', '登录态失效，请重新登录');
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(data.code || `HTTP_${res.status}`, data.message || res.statusText);
  return data.data ?? data;
}

export async function refresh() {
  const rt = localStorage.getItem('rat_refresh_token');
  if (!rt) return false;
  try {
    const res = await fetch(BASE + ENDPOINTS.A02.path, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refreshToken: rt }),
    });
    const d = await res.json();
    if (!res.ok) return false;
    localStorage.setItem('rat_access_token', d.data.accessToken);
    if (d.data.refreshToken) localStorage.setItem('rat_refresh_token', d.data.refreshToken);
    return true;
  } catch { return false; }
}

// 业务方法（按契约字段映射，供各屏调用）
export const api = {
  login: (channel, creds, deviceId) => request('A01', { body: { channel, ...creds, deviceId }, auth: false }),
  me: () => request('A03'),
  notifications: (level, page = 1, pageSize = 20) => request('A22', { body: { level, page, pageSize } }),
  notificationWs: () => request('A23'),
  dailyReport: () => request('A24'),
  saveDailyPref: (pushTime, enabled) => request('A25', { body: { pushTime, enabled } }),
  // A09 批量确认闸门（半自动投递核心）：confirm=提交选中项(pending_confirm→submitted)；revert=10s 撤销回滚。
  batchApplications: (applicationIds, action = 'confirm') => request('A09', { body: { applicationIds, action } }),
  // A10 投递列表（status 可选单值过滤；真实契约 applications-list.response）。
  applicationsList: (status, page = 1, pageSize = 20) => {
    const body = { page, pageSize };
    if (status) body.status = status;
    return request('A10', { body });
  },
  // A11 投递详情（状态机各态；真实契约 pending，按 interaction-U3.md §4 建模）。
  applicationDetail: (id) => request('A11', { params: { id } }),
  // …其余 A04–A21 按同一模式补充
};

export class ApiError extends Error {
  constructor(code, message) { super(message); this.code = code; }
}

// —— 本地 mock（仅 VITE_USE_MOCK，联调用；与契约同形）——
function mockResponse(id, body, params) {
  const now = Date.now();
  const store = {
    A22: () => ({ items: [
      { id: 'n1', level: 'L0', title: '面试邀请 · 字节跳动', body: '邀请参加视频面试。', read: false, createdAt: now - 3 * 60000, channel: 'push' },
      { id: 'n2', level: 'L1', title: '投递失败需处理 · 智联', body: '3 份因验证码触发暂停。', read: false, createdAt: now - 50 * 60000, channel: 'push' },
      { id: 'n3', level: 'L2', title: '今日已投递 10 份', body: '成功 9 / 失败 1。', read: true, createdAt: now - 2 * 3600000, channel: 'push' },
    ], unread: 2 }),
    A23: () => ({ wsUrl: 'wss://mock.local/notifications?token=demo' }),
    A24: () => ({ date: '2026-08-17', summary: '今日投递 12 份，成功 11。', stats: { appliedTotal: 12, success: 11, failed: 1, byPlatform: [{ platformId: 'Boss直聘', count: 5 }], hrViews: 4, interviewInvites: 2, newQuestions: 6, trend7d: [{ date: '08-17', count: 12 }] } }),
    A03: () => ({ userId: 'u1', email: 'you@example.com', plan: 'pro', quotaUsed: 32, quotaLimit: 100, preferences: { pushTime: '20:00', doNotDisturb: false } }),
    A01: () => ({ accessToken: 'at-demo', refreshToken: 'rt-demo', expiresIn: 3600, userId: 'u1', plan: 'pro' }),
    A25: () => ({ ok: true, updatedAt: now }),
    // A09 批量确认闸门（mock 支持 confirm/revert 动作）
    A09: (b) => {
      const { applicationIds = [], action = 'confirm' } = b || {};
      if (action === 'revert') return { reverted: applicationIds, at: now };
      return { accepted: applicationIds, rejected: [], at: now };
    },
    // A10 投递列表（与 applications-list.response 同形；mock 额外带 title/company 仅供本地联调，
    //   真实契约不含此二字段，组件已做回退显示——合同缺口见 TASK-LOG）
    A10: () => {
      const h = 3600 * 1000, d = 24 * h;
      const sample = [
        { applicationId: 'a1', jobId: 'j-bytedance-fe', jobTitle: '前端工程师 · 字节跳动', company: '字节跳动', platformId: 'Boss直聘', status: 'pending_confirm', appliedAt: now - 1 * h },
        { applicationId: 'a2', jobId: 'j-tencent-be', jobTitle: '后端开发 · 腾讯', company: '腾讯', platformId: '猎聘', status: 'submitted', appliedAt: now - 2 * h },
        { applicationId: 'a3', jobId: 'j-alibaba-pm', jobTitle: '产品经理 · 阿里', company: '阿里巴巴', platformId: 'Boss直聘', status: 'viewed', appliedAt: now - 3 * h },
        { applicationId: 'a4', jobId: 'j-meituan-fe', jobTitle: '资深前端 · 美团', company: '美团', platformId: '智联招聘', status: 'interview_invited', appliedAt: now - 5 * h },
        { applicationId: 'a5', jobId: 'j-baidu-algo', jobTitle: '算法工程师 · 百度', company: '百度', platformId: '猎聘', status: 'rejected', appliedAt: now - 26 * h },
        { applicationId: 'a6', jobId: 'j-xiaohongshu-op', jobTitle: '运营 · 小红书', company: '小红书', platformId: 'Boss直聘', status: 'pending_confirm', appliedAt: now - 30 * 60000 },
        { applicationId: 'a7', jobId: 'j-didi-be', jobTitle: 'Go 后端 · 滴滴', company: '滴滴', platformId: 'Boss直聘', status: 'offer', appliedAt: now - 50 * h },
        { applicationId: 'a8', jobId: 'j-kuaishou-fe', jobTitle: '前端架构 · 快手', company: '快手', platformId: '智联招聘', status: 'contacting', appliedAt: now - 4 * h },
      ];
      return { items: sample, total: sample.length };
    },
    // A11 投递详情（真实契约 pending；mock 构造状态机详情）
    A11: (b, p) => {
      const id = (p && p.id) || 'a1';
      const status = { a1: 'pending_confirm', a2: 'submitted', a3: 'viewed', a4: 'interview_invited', a5: 'rejected', a6: 'pending_confirm', a7: 'offer', a8: 'contacting' }[id] || 'pending_confirm';
      return {
        applicationId: id, jobId: 'j-' + id, jobTitle: '示例岗位 · ' + id, company: '示例公司', platformId: 'Boss直聘',
        status, appliedAt: now - 3600 * 1000,
        history: [{ status, at: now - 3600 * 1000 }],
      };
    },
  };
  const fn = store[id];
  if (!fn) throw new ApiError('NOT_MOCKED', `端点 ${id} 未提供 mock`);
  return Promise.resolve(fn(body, params));
}
