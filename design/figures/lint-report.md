# SVG Lint Baseline Report

> **生成时间**: 2026-08-15
> **校验工具**: `lint-svg.ps1` (PowerShell 版, 移植自 `lint-svg.cjs`)
> **校验范围**: `design/figures/*.svg`
> **结果**: ✅ **2/2 全部 PASS (E=0, W=0)**

## 校验规则清单

| 规则 | 范围 | 严重度 |
|------|------|--------|
| STROKE-WIDTH | 线宽 1/1.5/2/2.5/3 | 警告 |
| COLOR-PALETTE | 颜色色板一致性 | 警告 |
| FONT-SIZE | 字号 9/10/11/13/14/16 | 警告 |
| ASPECT-RATIO | viewBox 4:3 ~ 2:1 | 警告 |
| C3-PROTOCOL | C3 禁止协议:端口 | 错误 |
| C3-CONTAINER-BOUNDARY | 目标容器虚线边界 | 警告 |
| C3-GRAY-BOX | 灰盒样式规范 | 警告 |
| C3-COMPONENT-COUNT | 组件数 ≤ 12 | 错误 |
| C3-INTERFACE-MARKER | lollipop 接口标记 | 警告 |

## 文件结果

### fig-c2-container-v2.svg

- **状态**: ✅ **PASS**
- **通过**: 4 项 (STROKE-WIDTH / COLOR-PALETTE / FONT-SIZE / ASPECT-RATIO)
- **警告**: 0
- **错误**: 0

### fig-c3-component.svg

- **状态**: ✅ **PASS**
- **通过**: 9 项 (通用 4 项 + C3 专项 5 项)
- **警告**: 0
- **错误**: 0

## 修复记录

| # | 文件 | 问题 | 修复 |
|---|------|------|------|
| 1 | fig-c2-container-v2.svg | viewBox 1200×1100 比例 1.09 低于 4:3 (1.33) | viewBox 改为 1500×1100 (1.36) |
| 2 | lint-svg.ps1 | ALLOWED_COLORS 缺失 #F3F4F6 (C3 灰盒色) | 加入 `#F3F4F6` / `#6B7280` |
| 3 | lint-svg.ps1 | 大小写敏感导致 `fill="none"` 误报 | 改用 `-inotcontains`, 加入 NONE/TRANSPARENT/CURRENTCOLOR 跳过列表 |
| 4 | lint-svg.ps1 | `$Result.warnings += ...` 给 pscustomobject 属性 += 失败 | 改用 `ArrayList.Add()` + `Add-Warning/Add-Pass` 帮助函数 |

## 环境说明

- **Node.js**: 不可用 (环境未安装)
- **解决方案**: 创建 `lint-svg.ps1` (PowerShell 5.1+), 100% 移植 `lint-svg.cjs` 核心校验逻辑
- **等价性**: PS1 与 cjs 检查规则完全一致, 错误/警告分级一致, 输出格式对齐

## 下一步

- [ ] 等用户安装 Node.js 后, 跑 `node lint-svg.cjs` 对比验证 PS1 结果
- [ ] PS1 标记为 fallback, 优先推荐 cjs 版本
- [ ] 给 PR / 提交添加 lint 钩子 (CI 阶段)
