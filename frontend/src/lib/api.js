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
  // 以下为 U1 列表/首选的客户端扩展端点（契约无对应定义 → 合同缺口，见 TASK-LOG）
  A04_LIST: { method: 'GET', path: '/resumes' },
  A05_PREFER: { method: 'PATCH', path: '/resumes/{rid}/versions/{vid}/prefer' },
  A07: { method: 'GET', path: '/jobs' },
  A08: { method: 'POST', path: '/jobs/{id}/favorite' },
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
  // A12 读取当前投递策略（matchThreshold/dailyLimit/platforms/blacklist）
  getStrategy: () => request('A12'),
  // A13 更新投递策略（PUT /strategies）
  saveStrategy: (strategy) => request('A13', { body: strategy }),
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
  // A08 收藏/忽略（POST /jobs/{id}/favorite，body={action: 'favorite'|'ignore'}，响应 {ok,favoriteId,status}）
  favoriteJob: (jobId, action) => request('A08', { params: { id: jobId }, body: { action } }),
  // A07 岗位列表/筛选（GET /jobs，query={keyword?,location?,platform?,salaryMin?,page,pageSize}）
  jobsList: (params = {}) => request('A07', { body: { page: 1, pageSize: 20, ...params } }),
  // —— U1 简历工作台（A04/A05/A06）——
  // 简历列表：契约无 GET /resumes 列表端点 → 用本地 mock store（合同缺口见 TASK-LOG）。
  resumeList: () => request('A04_LIST'),
  // A04 创建简历（POST /resumes）→ resumeId/versionId/createdAt
  createResume: ({ title, template, body }) => request('A04', { body: { title, template, body } }),
  // A05 简历版本列表（GET /resumes/{id}/versions）→ versions[] + diffAvailable
  resumeVersions: (resumeId) => request('A05', { params: { id: resumeId } }),
  // A06 触发 ATS 评分（POST /resumes/{id}/ats）→ taskId/status(pending)
  triggerAts: (resumeId) => request('A06', { params: { id: resumeId } }),
  // 设为首选：契约无独立端点（需 PATCH /resumes/{id}/versions/{vid}/prefer）→ 本地 mock 直改 store（合同缺口）
  setPreferred: (resumeId, versionId) => request('A05_PREFER', { params: { rid: resumeId, vid: versionId } }),
  // —— U5 适配器管理（A14 列表 / A15 启用停用）——
  // A14 GET /adapters（适配器列表与状态；字段对齐 adapter-facade + b09-health）
  adapterList: () => request('A14'),
  // A15 POST /adapters/{id}/enable {enabled:bool} → {adapterId,status(enabled|disabled)}
  enableAdapter: (id, enabled) => request('A15', { params: { id }, body: { enabled } }),
  // —— U6 面试模拟（A16 题集 / A17 建会话 / A18 作答 / A19 报告）——
  // A16 GET /interview/questions → {questionSets:[{setId,title,questionCount,difficulty?,tags?}]}
  interviewQuestions: () => request('A16'),
  // A17 POST /interview/sessions {type,jobId?,mode,questionSetId?} → {sessionId,status}
  createSession: (body) => request('A17', { body }),
  // A18 POST /interview/sessions/{id}/answer {answer,questionId?,asrProvider?} → {accepted,score?(0-1)}
  answerSession: (id, body) => request('A18', { params: { id }, body }),
  // A19 GET /interview/sessions/{id}/report → {sessionId,overallScore(0-100),dimensions[],feedback,degradeFlag?}
  sessionReport: (id) => request('A19', { params: { id } }),
  // —— U7 支付与会员（A20 下单 / A21 回调）——
  // A20 POST /orders {plan(pro|team),months,coupon?} → {orderNo,amount(分),payUrl,expireAt(ms)}
  createOrder: (body) => request('A20', { body }),
  // A21 POST /orders/{id}/callback（mock 驱动 订单状态机 + memberPlanChanged）
  orderCallback: (id, body) => request('A21', { params: { id }, body }),
};

export class ApiError extends Error {
  constructor(code, message) { super(message); this.code = code; }
}

// —— 本地 mock（仅 VITE_USE_MOCK，联调用；与契约同形）——
// 简历列表/首选无契约端点 → 客户端 store（合同缺口见 TASK-LOG）
let _rid = 0;
let _strategy = {
  matchThreshold: 0.8,
  dailyLimit: 20,
  platforms: ['boss', 'liepin', 'zhaopin'],
  blacklist: ['某保险', '996'],
};
const _resumeStore = [
  { resumeId: 'r-se', title: '高级前端工程师 · 标准版', template: 'standard', versions: [
    { versionId: 'v-se-1', versionNo: 1, createdAt: Date.now() - 9 * 86400000, note: '初稿', isPreferred: false },
    { versionId: 'v-se-2', versionNo: 2, createdAt: Date.now() - 2 * 86400000, note: '补充项目经历', isPreferred: true },
  ] },
  { resumeId: 'r-be', title: '后端开发 · 技术版', template: 'tech', versions: [
    { versionId: 'v-be-1', versionNo: 1, createdAt: Date.now() - 5 * 86400000, note: null, isPreferred: true },
  ] },
];

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
    // A12/A13 投递策略（U4 策略配置）
    A12: () => ({ ..._strategy, updatedAt: now }),
    A13: (b) => {
      if (b) {
        _strategy = {
          matchThreshold: Number(b.matchThreshold) ?? _strategy.matchThreshold,
          dailyLimit: Number.isInteger(Number(b.dailyLimit)) ? Number(b.dailyLimit) : _strategy.dailyLimit,
          platforms: Array.isArray(b.platforms) ? b.platforms : _strategy.platforms,
          blacklist: Array.isArray(b.blacklist) ? b.blacklist : _strategy.blacklist,
        };
      }
      return { ok: true, updatedAt: now };
    },
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
    // —— U1 简历工作台 mock（A04 创建 / A04_LIST 列表 / A05 版本 / A05_PREFER 设为首选 / A06 触发ATS）——
    A04_LIST: () => _resumeStore.map(r => ({
      resumeId: r.resumeId, title: r.title, template: r.template,
      versionCount: r.versions.length,
      preferredVersionId: (r.versions.find(v => v.isPreferred) || {}).versionId || null,
    })),
    A04: (b) => {
      const id = 'r' + (++_rid) + '-' + Date.now().toString(36);
      const vid = 'v-' + id + '-1';
      const t = Date.now();
      const rec = { resumeId: id, title: (b && b.title) || '未命名简历', template: (b && b.template) || 'standard', versions: [{ versionId: vid, versionNo: 1, createdAt: t, note: null, isPreferred: true }] };
      _resumeStore.unshift(rec);
      return { resumeId: id, versionId: vid, createdAt: t };
    },
    A05: (b, p) => {
      const rid = (p && p.id) || (_resumeStore[0] && _resumeStore[0].resumeId);
      const rec = _resumeStore.find(r => r.resumeId === rid) || { versions: [] };
      return { versions: rec.versions, diffAvailable: rec.versions.length >= 2 };
    },
    A05_PREFER: (b, p) => {
      const rec = _resumeStore.find(r => r.resumeId === (p && p.rid));
      if (rec) rec.versions.forEach(v => { v.isPreferred = (v.versionId === (p && p.vid)); });
      return { ok: true };
    },
    A06: (b, p) => ({ taskId: 't-' + ((p && p.id) || 'r1') + '-' + Date.now().toString(36), status: 'pending' }),
    // —— U2 岗位浏览 mock（A07 列表 / A08 收藏|忽略）——
    // 完整 8 条岗位数据（覆盖 5 个平台 + 3 个 matchBand + favorited/ignored 状态），与 jobs-list.response.jobStub 同形
    A07: (b) => {
      const p = b || {};
      const all = [
        { jobId: 'j-2001', title: 'Java 开发工程师', company: '启明科技', platformId: 'boss', salaryMin: 15000, salaryMax: 25000, location: '上海', source: 'search', matchScore: 92, matchBand: 'green', matchReason: '技能 87% 吻合（Java/Spring/微服务）；地点命中偏好', favorited: false, ignored: false, collectedAt: now - 3600000 },
        { jobId: 'j-2002', title: '后端开发工程师', company: '云途互联', platformId: 'liepin', salaryMin: 18000, salaryMax: 30000, location: '杭州', source: 'search', matchScore: 85, matchBand: 'green', matchReason: '经验符合（2年+）；技术栈重合度高', favorited: true, ignored: false, collectedAt: now - 7200000 },
        { jobId: 'j-2003', title: '高级前端工程师', company: '小步创研', platformId: 'boss', salaryMin: 20000, salaryMax: 35000, location: '北京', source: 'search', matchScore: 78, matchBand: 'blue', matchReason: '技术栈匹配 React/Vue；需补充项目量化', favorited: false, ignored: false, collectedAt: now - 10800000 },
        { jobId: 'j-2004', title: '全栈开发', company: '极创科技', platformId: 'zhaopin', salaryMin: null, salaryMax: null, location: '远程', source: 'search', matchScore: 65, matchBand: 'blue', matchReason: '远程命中偏好；薪资需确认', favorited: false, ignored: false, collectedAt: now - 14400000 },
        { jobId: 'j-2005', title: 'Go 后端开发', company: '速购电商', platformId: 'lagou', salaryMin: 20000, salaryMax: 35000, location: '北京', source: 'search', matchScore: 54, matchBand: 'gray', matchReason: '语言不符（主栈 Go，你主栈 Java）', favorited: false, ignored: false, collectedAt: now - 18000000 },
        { jobId: 'j-2006', title: 'Python 数据工程师', company: '海纳数科', platformId: 'liepin', salaryMin: 16000, salaryMax: 28000, location: '深圳', source: 'search', matchScore: 71, matchBand: 'blue', matchReason: 'SQL/数据建模加分；语言部分吻合', favorited: false, ignored: false, collectedAt: now - 21600000 },
        { jobId: 'j-2007', title: 'DevOps 工程师', company: '和光运维', platformId: '51job', salaryMin: 18000, salaryMax: 32000, location: '广州', source: 'search', matchScore: 88, matchBand: 'green', matchReason: 'CI/CD/K8s 经验高度匹配；薪资优', favorited: false, ignored: false, collectedAt: now - 25200000 },
        { jobId: 'j-2008', title: '初级前端', company: '草创工作室', platformId: 'lagou', salaryMin: 8000, salaryMax: 12000, location: '上海', source: 'search', matchScore: 48, matchBand: 'gray', matchReason: '级别偏低，经验溢出', favorited: false, ignored: true, collectedAt: now - 28800000 },
      ];
      // 过滤
      const kw = (p.keyword || '').trim().toLowerCase();
      const loc = (p.location || '').trim().toLowerCase();
      const salMin = (p.salaryMin == null) ? null : Number(p.salaryMin);
      const pl = p.platform || '';
      const filtered = all.filter((j) => (
        (!kw || (j.title + j.company).toLowerCase().includes(kw)) &&
        (!loc || (j.location || '').toLowerCase().includes(loc)) &&
        (!pl || j.platformId === pl) &&
        (salMin == null || (j.salaryMin || 0) >= salMin)
      ));
      // 分页（mock：page/pageSize 语义真实）
      const page = Math.max(1, Number(p.page) || 1);
      const pageSize = Math.max(1, Math.min(100, Number(p.pageSize) || 20));
      const start = (page - 1) * pageSize;
      const items = filtered.slice(start, start + pageSize);
      return { items, total: filtered.length, page, pageSize };
    },
    A08: (b, p) => {
      const action = (b && b.action) || 'favorite';
      const jobId = (p && p.id) || 'j-2001';
      // 真实契约 ok/favoriteId/status；mock 直接返回最终态
      if (action === 'ignore') return { ok: true, favoriteId: null, status: 'ignored' };
      if (action === 'favorite') return { ok: true, favoriteId: 'fav-' + jobId + '-' + now.toString(36), status: 'favorited' };
      return { ok: true, favoriteId: null, status: 'removed' };
    },
    // —— U4 策略配置 mock（A12 读取 / A13 更新）——
    // 契约 strategies.response / strategies.request（matchThreshold 0–1 / dailyLimit int≥0 / platforms[] / blacklist[]）。
    // 真实响应为 strategies.request/response 同形 4 字段；A13 写响应为 {ok, updatedAt}（registry line 22 已 fully-detailed）。
    // 合同缺口：NONE（registry 4 字段全 + 写响应 ok+updatedAt 全）。
    _strat: (() => {
      const s = { matchThreshold: 0.8, dailyLimit: 20, platforms: ['boss', 'liepin', 'zhaopin'], blacklist: ['某保险', '996'] };
      let updatedAt = now;
      return {
        get: () => ({ matchThreshold: s.matchThreshold, dailyLimit: s.dailyLimit, platforms: [...s.platforms], blacklist: [...s.blacklist] }),
        set: (next) => { s.matchThreshold = Number(next.matchThreshold); s.dailyLimit = parseInt(next.dailyLimit, 10); s.platforms = Array.isArray(next.platforms) ? [...next.platforms] : []; s.blacklist = Array.isArray(next.blacklist) ? [...next.blacklist] : []; updatedAt = Date.now(); },
        updatedAt: () => updatedAt,
      };
    })(),
    A12: () => store._strat.get(),
    A13: (b) => { store._strat.set(b || {}); return { ok: true, updatedAt: store._strat.updatedAt() }; },
    // —— U5 适配器管理 mock（A14 列表 / A15 启用停用）——
    // A14 GET /adapters：对齐 adapter-facade(platformName/platformType/version/status) + b09-health(healthy/cookieHealthy/checkedAt/avgLatencyMs)。
    // 覆盖 6 态（installed/test_mode/enabled/disabled/degraded/login_expired），供 UI 全态验证。
    A14: () => ({
      items: [
        { adapterId: 'boss', platformName: 'BOSS直聘', platformType: 'social', version: 'v1.2.0', status: 'enabled', health: { healthy: true, cookieHealthy: true, checkedAt: now - 2 * 60000, avgLatencyMs: 120 } },
        { adapterId: 'liepin', platformName: '猎聘', platformType: 'headhunter', version: 'v1.1.0', status: 'enabled', health: { healthy: true, cookieHealthy: true, checkedAt: now - 60000, avgLatencyMs: 95 } },
        { adapterId: 'job51', platformName: '前程无忧', platformType: 'other', version: 'v1.0.3', status: 'degraded', health: { healthy: false, cookieHealthy: true, checkedAt: now - 5 * 60000, avgLatencyMs: 820 } },
        { adapterId: 'zhaopin', platformName: '智联招聘', platformType: 'other', version: 'v1.0.1', status: 'login_expired', health: { healthy: true, cookieHealthy: false, checkedAt: now - 8 * 60000, avgLatencyMs: 140 } },
        { adapterId: 'lagou', platformName: '拉勾', platformType: 'social', version: 'v0.9.0', status: 'disabled', health: { healthy: true, cookieHealthy: true, checkedAt: now - 12 * 60000, avgLatencyMs: 160 } },
        { adapterId: 'guopin', platformName: '国聘网', platformType: 'state-owned', version: 'v0.5.0', status: 'installed', health: { healthy: true, cookieHealthy: true, checkedAt: now - 20 * 60000, avgLatencyMs: 210 } },
        { adapterId: 'niuke', platformName: '牛客网', platformType: 'campus', version: 'v0.4.0', status: 'test_mode', health: { healthy: true, cookieHealthy: true, checkedAt: now - 30 * 60000, avgLatencyMs: 180 } },
      ],
    }),
    // A15 POST /adapters/{id}/enable {enabled} → {adapterId,status(enabled|disabled)}
    A15: (b, p) => {
      const id = (p && p.id) || null
      const enabled = !!(b && b.enabled)
      return { adapterId: id, status: enabled ? 'enabled' : 'disabled' }
    },
    // —— U6 面试模拟 mock（A16 题集 / A17 建会话 / A18 作答 / A19 报告）——
    // 字段严格对齐 U6-arch §4：questionSets[]{setId,title,questionCount,difficulty?,tags?} / dimensions[]{dim,rawScore(1-5),reason}
    A16: () => ({ questionSets: [
      { setId: 's1', title: '自我介绍', questionCount: 2, difficulty: 'easy', tags: ['1分钟', '3分钟'] },
      { setId: 's2', title: '项目介绍', questionCount: 3, difficulty: 'medium', tags: ['STAR'] },
      { setId: 's3', title: '技术问题', questionCount: 8, difficulty: 'hard', tags: ['Java', '分布式'] },
      { setId: 's4', title: '行为问题', questionCount: 5, difficulty: 'medium', tags: ['软技能'] },
    ] }),
    A17: (b) => ({ sessionId: 'sess_' + Date.now().toString(36), status: 'in_progress' }),
    A18: (b) => ({ accepted: true, score: Number((Math.random() * 0.3 + 0.6).toFixed(2)) }),
    A19: (b, p) => {
      const dims = [
        { dim: '回答完整性', rawScore: 4, reason: '覆盖了核心要点，但部分细节可补充。' },
        { dim: '技术准确性', rawScore: 5, reason: '技术概念表述准确，举例恰当。' },
        { dim: '结构化表达', rawScore: 4, reason: '基本采用 STAR 结构，可更精炼。' },
        { dim: '与岗位匹配度', rawScore: 5, reason: '充分体现了岗位所需能力。' },
      ]
      const overallScore = Math.round(dims.reduce((a, d) => a + d.rawScore, 0) / dims.length / 5 * 100)
      return {
        sessionId: (p && p.id) || 'sess_demo',
        overallScore,
        dimensions: dims,
        feedback: '整体表现优秀，建议在“回答完整性”上补充更多量化结果（如 QPS、降幅）。',
        degradeFlag: false,
      }
    },
    // —— U7 支付与会员 mock（A20 下单 / A21 回调）——
    // amount 单位为分，前端仅展示(分→元换算，不计算)；payUrl 仅占位。
    _price: { pro: { 1: 29, 3: 79, 6: 149, 12: 279 }, team: { 1: 99, 3: 269, 6: 519, 12: 999 } },
    A20: (b) => {
      const plan = (b && b.plan) || 'pro'
      const months = Number((b && b.months) || 1)
      const yuan = (store._price[plan] && store._price[plan][months]) || 29
      const orderNo = 'ORD-' + Date.now().toString().slice(-10)
      return { orderNo, amount: yuan * 100, payUrl: 'https://mock.local/pay/' + orderNo, expireAt: Date.now() + 24 * 3600 * 1000 }
    },
    A21: (b, p) => ({ ok: true, orderNo: (p && p.id) || null, toState: 'paid' }),
  };
  const fn = store[id];
  if (!fn) throw new ApiError('NOT_MOCKED', `端点 ${id} 未提供 mock`);
  return Promise.resolve(fn(body, params));
}
