# V 阶段 · 原型→生产前端转化（交付说明）

> 阶段目标（PROJECT_BRAIN §1/V）：将 U 阶段 `design/ui/screens/*.html` mock 原型转化为接入真实 **A01–A25 契约 API** 的前端工程代码（本地不部署、不触红线）。工程师主导，架构师复核组件边界。

## 交付物
- **`frontend/` 生产前端工程**（真实可构建代码，非原型）：
  - `package.json` / `vite.config.js` / `index.html` / `README.md` —— 工程化脚手架（Vite + React）。
  - `src/styles/tokens.css` —— 设计系统 token（与 `00-design-system.html` 同源）+ 响应式断点（§6）+ reduced-motion。
  - `src/lib/api.js` —— **A01–A25 端点映射 + ApiClient**：令牌仅存本机 localStorage（PRD §1012）；401→A02 静默刷新；`VITE_USE_MOCK` 本地联调；无真实密钥/部署。
  - `src/components/UI.jsx` —— 共享组件库，实现 **U11 交互总纲模式库**（Card/Button/Badge/Toggle/Skeleton/EmptyState/ErrorState/Modal/Toast）。
  - `src/screens/Notifications.jsx`（**U8 转化范式，A22/A23**）+ `src/screens/Auth.jsx`（**U10 转化范式，A01/A02/A03**）+ `src/App.jsx`（应用壳 + AuthGuard 未登录遮业务，PRD §797 红线）。
- **转化范式（V2）**：其余 U1–U7/U9/U11 屏按「api 客户端 + 共享组件 + 契约字段映射」机械性转化；优先级与字段映射见 `ROLE-DELIVERABLES.md` 与 `roles/Ux-arch.md` 映射表。

## 红线核查（REVIEW-3）
- 无硬编码密钥/平台 Cookie；令牌仅本机；不自动部署。✅ 不触发红线。

## QA 核查（T 阶段前自检）
- `npm run build` 可产出 `dist/`（工程可构建，待 T1 功能测试 + T2 集成）。
- 响应式沿用 tokens.css 断点 + U11 模式，满足 UI-SELFCHECK R1–R7。

## 状态：V1 脚手架 ✅ / V2 范式(U8,U10) ✅ / 其余屏转化待 T 阶段后批量（机械性，按映射表）
