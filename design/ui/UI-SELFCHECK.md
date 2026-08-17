<!-- TRACE
role: Team Lead | 主 agent
package: UI 质量门禁 · 自我反思 + 自查清单（全局规范）
agent_run: 2026-08-17T21:50
author_of_record: Team Lead (主 agent)
upstream_read: [design/ui/screens/U1-resume.html, U2-jobs.html, U3-applications.html, U4-strategy.html, U5-adapter.html, design/ui/00-design-system.html]
downstream_write: [design/ui/ROLE-WORKBOOK.md §9, PROJECT_BRAIN.md §8, design/ui/screens/*.html(响应式补丁)]
decisions: 2026-08-17 用户指出"UI 没考虑响应式 + 排版乱"。复盘根因=设计系统无响应式规范 + 各屏各自写 CSS + QA 无移动端自查闸门。本文件把"为什么乱/能否顺畅使用"说清，并把三端自查列为提交前必过闸门、把"防卡死验证"列为派发纪律。
status: DONE
-->

# UI 自我反思与三端自查清单（UI-SELFCHECK）

> 本文件是 **提交前必过的 UI 质量闸门**。所有 U 包（U1–U11）的 HTML 原型在 commit 前，QA 角色（及 Team Lead 兜底）必须按 §3 逐项自查并写入 `Ux-qa.md`。
> 目的：回答用户两个质疑——**① 为什么之前排版乱 / 没响应式；② 用户能否顺畅使用**——并把"下次自己自检"固化成机制，不再依赖人工事后发现。

---

## 1. 复盘：为什么之前"排版乱 + 没响应式"

**结论：这是系统性缺口，不是个例。** U1–U5 全部存在，根因有三：

1. **设计系统从未定义响应式规范（根因）**
   `00-design-system.html` 只有 `viewport` meta，没有断点、没有"侧栏壳如何折叠"、没有"卡片如何堆叠"的范式。各屏只能各写各的 CSS，导致 4 个屏都用了 `grid-template-columns:232px 1fr` 固定侧栏却**没有一个写 `@media`**。
2. **各屏 CSS 各自为政、无共享样式表**
   每份 `screens/Ux-*.html` 都是自包含内联 `<style>`，没有引入统一响应式片段。哪怕设计系统后来补了规范，也不会自动生效到已有屏。
3. **QA 缺少"移动端自查"闸门（直接原因）**
   之前的 QA 只查"双闸门 + UI 一致性 + 无障碍 + 交互可用"，**没要求渲染到手机宽度验证**。于是循环把"桌面 OK 但手机崩"的原型直接提交了。

**U5 的具体乱点（用户点名的那个）**：卡片 `.card` 是 `display:flex` 单行，含 `.health{min-width:120px}` 固定宽 + 两个操作按钮；手机宽度下 `点 + 信息 + 健康(120) + 按钮(≈140)` 超过 375px → 横向挤压/溢出，操作按钮难点。

---

## 2. 用户能否顺畅使用？（诚实结论）

| 设备 | 之前 | 现在（本补丁后） |
|---|---|---|
| 桌面 PC ≥1024px | ✅ 正常 | ✅ 正常 |
| 平板 768–1023px | ⚠️ 侧栏偏宽、内容略挤 | ✅ 侧栏折叠/内容收窄 |
| 手机 ≤768px（占用户主力） | ❌ 侧栏吃掉 232px、卡片不堆叠、横向溢出、按钮难点 | ✅ 侧栏变顶部横滚条、卡片纵向堆叠、按钮整行可点（≥40px） |

**之前的真实可用性：桌面能看，手机基本不可用。** 这不符合"用户能否顺畅使用"的要求，已修。

---

## 3. UI 三端自查清单（提交前必过 · 任一项 FAIL 即退回）

QA 在 `Ux-qa.md` 必须逐条给出 **PASS / FAIL + 实测宽度**，不得凭印象打勾：

- [ ] **R1 三宽渲染**：在 **375px / 768px / 1280px** 三档下页面均正常打开（用浏览器开发者工具或 `prefers-color-scheme` 同思路的视口模拟；无 GUI 时以 CSS 逻辑审查 `@media` 覆盖是否完整替代判定）。
- [ ] **R2 无横向溢出**：任一宽度下 `document.documentElement.scrollWidth ≤ window.innerWidth`（不出现横向滚动条）。重点查固定 `min-width`/`width` 元素（健康列、按钮组、筛选输入框、slider）。
- [ ] **R3 无重叠/错位**：文字不被截断、徽标不被按钮压住、模态框不被顶部栏遮挡。
- [ ] **R4 可点性**：所有可点击元素（按钮/标签/勾选）最小点按区 ≥ **40×40px**（移动端）。
- [ ] **R5 模态/弹窗自适应**：对话框 `width` 设 `max-width:90vw`（或更小），不超出视口。
- [ ] **R6 动效合规**：仍尊重 `prefers-reduced-motion: reduce`（已有全局降级）。
- [ ] **R7 语义可访问**：关键操作有文本/aria，不仅靠颜色区分状态（对照 `02-motion-system.html` 与 §19 无障碍）。

> 说明：本运行环境无图形浏览器，R1/R2 的"实测"以 **CSS 逻辑审查** 为准——QA 必须确认每个屏的 `<style>` 末尾含有对应 `@media` 块（壳折叠 + 卡片堆叠），且覆盖 ≤768px 与 ≤480px 两档；有 GUI 时再补真机/模拟器截图。

---

## 4. 防"卡住 / 没真跑"机制（派发纪律）

针对 2026-08-17 出现的"子 agent 调度瞬断 → 一直'准备中'、产物零文件"问题，固化如下：

1. **派发后必验证**：每派发一个角色 agent，返回后**立即检查其承诺产物文件是否存在且非空**（`ls -l` 或 Read 头几行）。
2. **缺失则重试一次**：同一角色重新派发（提示"上轮未产出文件，请确认已写入 X"）；仍缺失 → **Team Lead 代笔**并按 TRACE 标注"子 agent 瞬断、lead 代笔"，不伪造"角色独立产出"。
3. **打点日志**：每轮 automation memory 顶部状态块记录"本轮回合：派发 / 重试 / lead 代笔"。
4. **不阻塞整轮**：任一角色超时/失败，转其他可独立包继续，标 `PENDING/BLOCKED`，等下轮续做（电路保护器）。

---

## 5. 响应式 CSS 范式（各屏复制用 · 与 `00-design-system.html` §6 一致）

**带侧栏壳的屏（U1–U4）**：在 `<style>` 末尾追加——

```css
/* 响应式：手机端侧栏折叠为顶部横滚条 + 卡片纵向堆叠（依据 §6 + UI-SELFCHECK §3） */
@media (max-width:768px){
  .app{grid-template-columns:1fr;}
  .side{flex-direction:row;align-items:center;overflow-x:auto;border-right:none;border-bottom:1px solid var(--c-border);}
  .brand{flex-shrink:0;border-bottom:none;border-right:1px solid var(--c-border);padding:12px 14px;font-size:14px;}
  .nav{flex-direction:row;flex-wrap:nowrap;padding:8px;gap:4px;overflow-x:auto;}
  .nav a{white-space:nowrap;margin-bottom:0;padding:8px 10px;}
  .side-foot{display:none;}
  .main{min-height:0;}
  .top{flex-wrap:wrap;height:auto;min-height:52px;padding:8px 12px;gap:8px;}
  .top .search{max-width:none;flex:1 1 100%;order:3;}
  .content{padding:14px;max-width:none;}
  .page-head h1{font-size:18px;}
  .job,.app-row,.resume{flex-wrap:wrap;}
  .job .acts,.app-row .acts,.resume .acts{width:100%;justify-content:flex-start;margin-top:8px;flex-direction:row;flex-wrap:wrap;}
  .app-row .acts{justify-content:flex-end;}
  .input,.select{width:100%;min-width:0;max-width:100%;}
  .slider{width:100%;max-width:320px;}
  .btn{min-height:40px;}
}
@media (max-width:480px){
  .content{padding:10px;}
  .card{padding:14px;}
  .filter{flex-direction:column;align-items:stretch;}
  .filter .input{min-width:0;}
}
```

**卡片型屏（U5 适配器，无侧栏壳）**：在 `<style>` 末尾追加——

```css
/* 响应式：卡片在窄屏纵向堆叠（依据 §6 + UI-SELFCHECK §3） */
@media (max-width:640px){
  .card{flex-wrap:wrap;align-items:flex-start;}
  .meta{flex:1 0 55%;}
  .health{min-width:0;flex:1 0 100%;text-align:left;margin-top:6px;order:3;}
  .actions{flex:1 0 100%;justify-content:flex-end;margin-top:8px;order:4;}
  .btn{min-height:40px;}
}
```
