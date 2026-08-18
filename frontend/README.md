# resume-ai-prod 生产前端（V 阶段）

> **V 阶段目标**：把 `design/ui/screens/*.html`（U 阶段 mock 原型）转化为接入真实 **A01–A25 契约 API** 的前端工程代码（本地不部署、不触红线）。
> 本目录即「生产就绪脚本」级交付：工程化脚手架 + 共享组件库（来自 U11 交互总纲模式库）+ 契约 API 客户端 + 已转化范式屏（U8 通知中心、U10 用户登录）。

## 运行
```bash
npm install
npm run dev        # 本地开发（VITE_API_TARGET 指向 scaffold 后端）
npm run build      # 产出 dist/（可交由 O 阶段 CD 部署到单机器/小容器）
npm test           # vitest 组件/契约测试
```

## 目录
- `src/styles/tokens.css` —— 设计系统 token（与 `design/ui/00-design-system.html` 同源，保证原型↔生产视觉一致）
- `src/lib/api.js` —— **A01–A25 端点映射 + ApiClient**（认证令牌仅存本机 localStorage；无真实密钥/部署）
- `src/components/UI.jsx` —— 共享组件（Card/Button/Badge/Toggle/Skeleton/Modal/Toast/Tabs），实现 U11 交互总纲模式库
- `src/screens/*.jsx` —— 已转化屏；**范式**：U8 通知中心（A22/A23）、U10 用户登录（A01/A02/A03）
- `src/App.jsx` —— 应用壳 + 路由（AuthGuard 未登录遮业务，PRD §797 红线）

## 转化说明（V2）
其余 U1–U7/U9/U11 屏按同一范式转化（api 客户端 + 共享组件 + 契约字段映射），属机械性工作；
转化优先级由 `design/v-stage.md` 规定。所有屏须通过 `design/ui/UI-SELFCHECK.md` R1–R7 响应式自查方可合并。

## 红线（诚实边界）
- 不硬编码任何 API 密钥 / 平台 Cookie；令牌仅本机存储。
- 不自动部署；部署/真实账号/上线仅用户触发（见 PROJECT_BRAIN §3）。
