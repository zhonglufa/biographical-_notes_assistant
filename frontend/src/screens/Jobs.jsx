// U2 岗位浏览（A07/A08 生产组件）。
// 交互规格：design/ui/interaction-U2.md；契约：jobs-list.response / jobs-search.request / jobs-favorite.{request,response}。
// U11 基线：加载(Skeleton) / 错误(重试) / 空态(引导放宽筛选) / Toast(含撤销) / 无障碍(aria) / 响应式 375/768/1280。
// 诚实边界：忽略(ignore)契约响应只回 status=ignored，不在 jobStub 显式标 ignored 字段→本组件维护 ignoredSet（前端态，
//   撤销忽略即从 set 移除；与 U3 已有的本地态处理对齐，不臆造后端字段）。
import { useState, useEffect, useCallback, useRef } from 'react';
import { Card, Button, Skeleton, EmptyState, ErrorState, Toast } from '../components/UI.jsx';
import { api } from '../lib/api.js';

const PLAT = { boss: 'Boss直聘', liepin: '猎聘', zhaopin: '智联', '51job': '前程无忧', lagou: '拉勾' };
const PLAT_LIST = ['boss', 'liepin', 'zhaopin', '51job', 'lagou'];

function bandOf(score) {
  if (score == null) return null;
  if (score >= 80) return 'green';
  if (score >= 60) return 'blue';
  return 'gray';
}
function bandStyle(b) {
  if (b === 'green') return { bg: 'var(--c-ok-soft, #ECFDF3)', bd: 'var(--c-ok-bd, #ABEFC6)', fg: 'var(--c-ok, #16A34A)' };
  if (b === 'blue')  return { bg: 'var(--c-info-soft, #EFF6FF)', bd: 'var(--c-info-bd, #BFDBFE)', fg: 'var(--c-info, #2563EB)' };
  if (b === 'gray')  return { bg: 'var(--c-bg, #F1F5F9)', bd: 'var(--c-border)', fg: 'var(--c-muted)' };
  return { bg: 'var(--c-bg, #F1F5F9)', bd: 'var(--c-border)', fg: 'var(--c-faint)' };
}
const fmtSalary = (j) => (j.salaryMin == null ? '薪资面议' : `${Math.round(j.salaryMin / 1000)}-${Math.round(j.salaryMax / 1000)}K`);

export default function Jobs() {
  const [items, setItems] = useState(null);          // null=加载中
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({ keyword: '', location: '', salaryMin: '', platform: '' });
  const [applied, setApplied] = useState({ keyword: '', location: '', salaryMin: '', platform: '' });
  const [ignoredSet, setIgnoredSet] = useState(() => new Set());  // 合同缺口：前端态维护 ignore 集合
  const [toast, setToast] = useState({ show: false, message: '', onUndo: null });
  const searchRef = useRef(0);  // 防止过期请求覆盖新结果

  const flash = useCallback((message, onUndo) => {
    setToast({ show: true, message, onUndo: onUndo || null });
    setTimeout(() => setToast((t) => ({ ...t, show: false })), 2600);
  }, []);

  const load = useCallback((params) => {
    const myReq = ++searchRef.current;
    setError(null);
    setItems(null);
    // 参数整形：salaryMin 转整数（元/月）；空值丢弃
    const q = {};
    if (params.keyword) q.keyword = params.keyword;
    if (params.location) q.location = params.location;
    if (params.platform) q.platform = params.platform;
    if (params.salaryMin !== '' && params.salaryMin != null) {
      const n = parseInt(params.salaryMin, 10);
      if (!Number.isNaN(n) && n >= 0) q.salaryMin = n;
    }
    api.jobsList(q).then((res) => {
      if (myReq !== searchRef.current) return;  // 过期请求丢弃
      setItems(res.items);
      setTotal(res.total);
      setPage(res.page);
    }).catch(() => { if (myReq !== searchRef.current) return; setError('岗位列表加载失败'); });
  }, []);

  useEffect(() => { load(applied); }, [applied, load]);

  // —— 搜索 / 筛选 ——
  const onSearch = () => {
    // 校验：薪资下限非法输入 → 友好提示，不报错（U11 §5）
    if (form.salaryMin !== '' && form.salaryMin != null) {
      const n = parseInt(form.salaryMin, 10);
      if (Number.isNaN(n) || n < 0) { flash('请输入数字（K 或元/月）'); return; }
    }
    setPage(1);
    setApplied({ ...form });
  };
  const onPlatform = (pl) => {
    const next = { ...form, platform: pl };
    setForm(next);
    setPage(1);
    setApplied(next);
  };
  const onClear = () => {
    const empty = { keyword: '', location: '', salaryMin: '', platform: '' };
    setForm(empty);
    setPage(1);
    setApplied(empty);
  };

  // —— 收藏 / 忽略 / 详情 ——
  const onFavorite = (job) => {
    if (ignoredSet.has(job.jobId)) return;  // 已忽略的不可直接收藏（需先撤销忽略）
    api.favoriteJob(job.jobId, 'favorite').then((res) => {
      if (res && res.ok) {
        setItems((arr) => arr.map((j) => j.jobId === job.jobId ? { ...j, favorited: true } : j));
        flash('已收藏，已送入「待确认投递」');
      } else {
        flash('收藏失败，请重试');
      }
    }).catch(() => flash('收藏失败，请重试'));
  };
  const onUnfavorite = (job) => {
    api.favoriteJob(job.jobId, 'favorite').then(() => {  // mock 复用 favorite 入参；语义：再次触发即取消（前端态清理）
      setItems((arr) => arr.map((j) => j.jobId === job.jobId ? { ...j, favorited: false } : j));
      flash('已取消收藏');
    }).catch(() => flash('操作失败，请重试'));
  };
  const onIgnore = (job) => {
    api.favoriteJob(job.jobId, 'ignore').then((res) => {
      if (res && res.ok) {
        const next = new Set(ignoredSet); next.add(job.jobId);
        setIgnoredSet(next);
        flash('已忽略，不再推送该岗位', () => {
          const r = new Set(next); r.delete(job.jobId);
          setIgnoredSet(r);
          flash('已撤销忽略');
        });
      } else {
        flash('忽略失败，请重试');
      }
    }).catch(() => flash('忽略失败，请重试'));
  };
  const onDetail = (job) => {
    // 详情页待 V 阶段补（真实路径 jobs-detail 端点 pending）；此处给占位反馈
    flash(`打开岗位详情：${job.title}（mock）`);
  };

  // —— 翻页 ——
  const maxPage = Math.max(1, Math.ceil(total / pageSize));
  const goto = (p) => { if (p < 1 || p > maxPage) return; setPage(p); load({ ...applied, page: p, pageSize }); };

  if (error) return <ErrorState message={error} onRetry={() => load(applied)} />;
  if (items === null) return <div style={{ padding: 16 }}><Skeleton lines={4} /></div>;

  return (
    <div style={{ maxWidth: 1080, margin: '0 auto', padding: '12px 8px' }}>
      <div style={{ marginBottom: 10 }}>
        <h2 style={{ margin: 0, fontSize: 18 }}>岗位浏览</h2>
        <div style={{ fontSize: 12, color: 'var(--c-muted)', marginTop: 2 }}>搜索 / 筛选招聘平台岗位，按 AI 匹配度排序；收藏送入待确认投递，忽略后不再推送。</div>
      </div>

      {/* 筛选条（A07 查询参数：keyword/location/salaryMin） */}
      <Card style={{ padding: 12, marginBottom: 10 }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <input aria-label="关键词" placeholder="关键词：Java / 后端 / 微服务"
            value={form.keyword} onChange={(e) => setForm((f) => ({ ...f, keyword: e.target.value }))}
            onKeyDown={(e) => { if (e.key === 'Enter') onSearch(); }}
            style={inputStyle} />
          <input aria-label="城市" placeholder="城市：上海"
            value={form.location} onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
            onKeyDown={(e) => { if (e.key === 'Enter') onSearch(); }}
            style={{ ...inputStyle, minWidth: 120 }} />
          <input aria-label="月薪下限" placeholder="月薪下限(元)" inputMode="numeric"
            value={form.salaryMin} onChange={(e) => setForm((f) => ({ ...f, salaryMin: e.target.value.replace(/[^\d]/g, '') }))}
            onKeyDown={(e) => { if (e.key === 'Enter') onSearch(); }}
            style={{ ...inputStyle, width: 130 }} />
          <Button variant="primary" onClick={onSearch}>搜索</Button>
          <Button onClick={onClear}>清空</Button>
          <span style={{ marginLeft: 'auto', color: 'var(--c-muted)', fontSize: 13 }}>共 {total} 个岗位</span>
        </div>
        <div style={{ marginTop: 10, display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: 'var(--c-muted)' }}>平台：</span>
          <Chip on={form.platform === ''} onClick={() => onPlatform('')}>全部</Chip>
          {PLAT_LIST.map((pl) => <Chip key={pl} on={form.platform === pl} onClick={() => onPlatform(pl)}>{PLAT[pl]}</Chip>)}
        </div>
      </Card>

      {/* 岗位列表 */}
      {items.length === 0 ? (
        <EmptyState hint="没有匹配的岗位。试试放宽筛选条件，或去「简历工作台」更新偏好。" />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {items.map((j) => {
            const b = j.matchBand || bandOf(j.matchScore);
            const st = bandStyle(b);
            const ignored = ignoredSet.has(j.jobId);
            return (
              <Card key={j.jobId} style={{ padding: 14, opacity: ignored ? 0.55 : 1 }}>
                <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                  {/* 匹配度环（matchBand 着色） */}
                  <div aria-label="AI 匹配度" style={{ flexShrink: 0, width: 56, height: 56, borderRadius: 12, background: st.bg, border: '1px solid ' + st.bd, color: st.fg, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                    <div style={{ fontSize: 16, lineHeight: 1 }}>{j.matchScore == null ? '—' : j.matchScore}</div>
                    <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--c-muted)' }}>匹配</div>
                  </div>
                  {/* 信息 */}
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                      <strong style={{ fontSize: 15, color: 'var(--c-strong)' }}>{j.title}</strong>
                      {j.favorited && <span style={{ fontSize: 11, background: 'var(--c-accent)', color: '#fff', borderRadius: 'var(--r-full)', padding: '1px 8px' }}>已收藏</span>}
                      {ignored && <span style={{ fontSize: 11, background: 'var(--c-bg)', color: 'var(--c-muted)', border: '1px solid var(--c-border)', borderRadius: 'var(--r-full)', padding: '1px 8px' }}>已忽略</span>}
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--c-muted)', margin: '4px 0' }}>
                      {j.company} · {PLAT[j.platformId] || j.platformId} · {j.location || '—'} · {fmtSalary(j)} · {j.source === 'detail' ? '详情采集' : '搜索采集'}
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--c-body)', background: 'var(--c-bg)', borderRadius: 'var(--r-sm)', padding: '8px 10px' }}>
                      匹配理由：<b style={{ color: 'var(--c-accent)' }}>{j.matchReason || '—'}</b>
                    </div>
                  </div>
                  {/* 操作 */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end', flexShrink: 0, minWidth: 100 }}>
                    {ignored ? (
                      <Button style={{ fontSize: 13, padding: '6px 12px', minHeight: 32 }} onClick={() => {
                        const next = new Set(ignoredSet); next.delete(j.jobId);
                        setIgnoredSet(next); flash('已撤销忽略');
                      }}>撤销忽略</Button>
                    ) : j.favorited ? (
                      <Button style={{ fontSize: 13, padding: '6px 12px', minHeight: 32 }} onClick={() => onUnfavorite(j)}>取消收藏</Button>
                    ) : (
                      <Button variant="primary" style={{ fontSize: 13, padding: '6px 12px', minHeight: 32 }} onClick={() => onFavorite(j)}>收藏 →</Button>
                    )}
                    {!ignored && <Button style={{ fontSize: 13, padding: '6px 12px', minHeight: 32 }} onClick={() => onIgnore(j)}>忽略</Button>}
                    <Button style={{ fontSize: 13, padding: '6px 12px', minHeight: 32 }} onClick={() => onDetail(j)}>详情</Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* 分页器 */}
      {total > pageSize && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'center', margin: '16px 0', color: 'var(--c-muted)', fontSize: 13 }}>
          <span>第 {page} / {maxPage} 页</span>
          <Button disabled={page <= 1} onClick={() => goto(page - 1)} style={{ fontSize: 13, padding: '6px 12px', minHeight: 32 }}>上一页</Button>
          <Button disabled={page >= maxPage} onClick={() => goto(page + 1)} style={{ fontSize: 13, padding: '6px 12px', minHeight: 32 }}>下一页</Button>
        </div>
      )}

      <Toast show={toast.show} message={toast.message} onUndo={toast.onUndo} />
    </div>
  );
}

const inputStyle = {
  minWidth: 180, padding: '9px 12px', borderRadius: 'var(--r-md)', border: '1px solid var(--c-border)', fontSize: 14, background: 'var(--c-surface)',
};

function Chip({ on, children, onClick }) {
  return (
    <button onClick={onClick} style={{
      fontSize: 13, padding: '6px 12px', borderRadius: 'var(--r-full)',
      border: '1px solid ' + (on ? 'var(--c-accent)' : 'var(--c-border)'),
      background: on ? 'var(--c-accent-weak, #EEF2FF)' : 'var(--c-surface)',
      color: on ? 'var(--c-accent)' : 'var(--c-body)',
      fontWeight: on ? 600 : 400, cursor: 'pointer', minHeight: 32,
    }}>{children}</button>
  );
}
