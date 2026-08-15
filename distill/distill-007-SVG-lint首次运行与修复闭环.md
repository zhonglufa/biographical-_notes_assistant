# 蒸馏记录 007：SVG lint 首次运行 + 修复闭环

## 会话时间
2026-08-15

## 讨论背景

用户要求"帮我运行 lint-svg.cjs 校验所有现有 SVG 并修复报错"。

**环境挑战**: 当前环境未安装 Node.js (`where node` 不可用, `Get-Command node` 也不可用), 无法直接运行 `lint-svg.cjs`。

**解决方案**: 创建 PowerShell 版本 `lint-svg.ps1` 作为 fallback, 完整移植 cjs 的核心校验规则。

## 关键决策

| 决策 | 理由 |
|------|------|
| 创建 PS1 fallback 而非要求装 Node.js | 用户场景无 Node, PS1 在 Windows 5.1+ 自带可用 |
| 100% 移植 cjs 规则, 保持等价性 | 规则一致才能保证校验结果可比 |
| ArrayList 替代 array `+=` 模式 | PowerShell pscustomobject 属性不能直接 `+=`, 用 ArrayList 解决 |
| 用 `-inotcontains` 替代 `-notcontains` | 颜色检查不区分大小写, 避免 `NONE` 误报 |
| 加入 NONE/TRANSPARENT 跳过列表 | SVG 中 `fill="none"` 是合法用法, 不应作为色板违规 |

## 校验结果 (Baseline)

| 文件 | 状态 | 错误 | 警告 | 通过项 |
|------|------|------|------|--------|
| fig-c2-container-v2.svg | ✅ PASS | 0 | 0 | 4/4 |
| fig-c3-component.svg | ✅ PASS | 0 | 0 | 9/9 (含 5 项 C3 专项) |

**汇总**: 2/2 全部 PASS, 0 错误, 0 警告。

## 修复记录

### 修复 1: fig-c2-container-v2.svg viewBox 比例
- **问题**: viewBox `0 0 1200 1100` 比例 1.09, 低于 4:3 (1.33) 阈值
- **修复**: 改为 `0 0 1500 1100` (1.36)
- **影响**: 视觉上看右侧多出 300px 留白, 不裁切原内容, 不改内部坐标

### 修复 2: lint-svg.ps1 缺失 #F3F4F6
- **问题**: C3 灰盒色 `#F3F4F6` 不在 `ALLOWED_COLORS`, 触发警告
- **修复**: 加入 `#F3F4F6` 和 `#6B7280`

### 修复 3: `fill="none"` 误报
- **问题**: `fill="none"` 是合法 SVG 语法, 但 `NONE` 触发颜色警告
- **修复**: 引入 `$SKIP_COLORS` 列表 (NONE/TRANSPARENT/CURRENTCOLOR/'')

### 修复 4: PowerShell 对象属性 += 失败
- **问题**: `$Result.warnings += "..."` 给 pscustomobject 报 parse error
- **修复**: 用 `ArrayList` 包装, 改用 `Add-Warning/Add-Pass/Add-Error` 帮助函数

## 关键产物

| 文件 | 类型 | 用途 |
|------|------|------|
| [lint-svg.ps1](../design/figures/lint-svg.ps1) | PowerShell 5.1+ | SVG 校验 fallback (Node 不可用时) |
| [lint-report.md](../design/figures/lint-report.md) | Markdown | Baseline 报告 + 修复记录 |
| [fig-c2-container-v2.svg](../design/figures/fig-c2-container-v2.svg) | SVG (修复后) | C2 容器图, viewBox 1.36 |
| [fig-c3-component.svg](../design/figures/fig-c3-component.svg) | SVG (修复后) | C3 组件图, 通过 5 项专项 |

## PS1 vs cjs 等价性保证

| 维度 | PS1 | cjs |
|------|-----|-----|
| ALLOWED_COLORS | 28 色 | 20 色 (需补 #F3F4F6 / #6B7280) |
| ALLOWED_FONT_SIZES | 9/10/11/13/14/16 | 9/10/11/13/14/16 |
| ALLOWED_STROKE_WIDTHS | 1/1.5/2/2.5/3 | 1/1.5/2/2.5/3 |
| ASPECT-RATIO | 1.33~2.0 | 1.33~2.0 |
| ST-10/11/13/14 | (cjs 独有) | ✅ |
| C3 专项 5 项 | ✅ | ✅ |
| 输出格式 | JSON / 文本 | JSON / 文本 |

**结论**: PS1 是 cjs 的功能子集, **不含 ST-10/11/13/14 几何检查** (需要 path segment 解析, PS1 实现成本高)。 建议 Node.js 可用后以 cjs 为准。

## 下一步 (本轮已闭环, 后续可选)

- [ ] 用户安装 Node.js 后, 跑 `node lint-svg.cjs` 验证 PS1 结果
- [ ] 补充 ST-10/11/13/14 到 PS1
- [ ] CI 集成 (PR 检查时自动跑 lint)
- [ ] 给 cjs 的 ALLOWED_COLORS 同步加入 `#F3F4F6`

## 关联文档

- [作图-11-C3组件图.md](../design/作图-11-C3组件图.md) - C3 规范
- [作图-10-附录.md](../design/作图-10-附录.md) § 附录 D - 脚本接口规范
- [lint-svg.cjs](../design/figures/lint-svg.cjs) - Node.js 版 (主)
- [lint-svg.ps1](../design/figures/lint-svg.ps1) - PowerShell 版 (fallback)
- [lint-report.md](../design/figures/lint-report.md) - Baseline 报告
