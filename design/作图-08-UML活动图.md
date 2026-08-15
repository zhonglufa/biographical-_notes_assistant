# UML 活动图 (UML Activity Diagram)

> **来源**: 拆分自 作图大全标准.md v1.6 §3.7 + 补充
> **拆分日期**: 2026-08-15
> **关联文档**: [作图-01-通用规范.md](./作图-01-通用规范.md) | [作图-README.md](./作图-README.md)
> **UML 版本**: 2.5
> **新增**: 完整补充原 §3.7 待补充章节

## 3.7.1 决策目标

| 问题 | 答案 |
|------|------|
| 支持什么决策 | 业务流程如何流转?分支/并发/异常如何处理?谁负责哪一步? |
| 谁读 | 产品经理、业务方、流程 owner |
| 决策后果 | 流程画错 → 实际实现错 |

活动图是 UML 中唯一能完整描述业务流程的图,涵盖顺序、分支、并发、异常四类语义。绘制前需明确:

- 流程的起点与终点在哪里
- 哪些步骤可以并行,哪些必须串行
- 异常路径与重试策略
- 各角色在流程中的职责边界

## 3.7.2 UML 2.5 语法合规

| 元素 | UML 2.5 规范 | SVG 实现 | 常见错误 |
|------|-------------|----------|----------|
| **起始节点** | 实心圆 | `<circle>` r=10 fill=#333 | 用空心圆 |
| **结束节点** | 牛眼 (内圆+外圆) | 2 个同心圆 | 单圆 |
| **活动节点** | 圆角矩形 | `<rect rx=10>` | 直角矩形 |
| **决策节点** | 空心菱形 | `<polygon>` fill=white stroke=#333 | 实心菱形 |
| **合并节点** | 空心菱形 (粗) | `<polygon>` stroke-width=2.5 | 与决策节点混淆 |
| **分叉节点** | 粗水平条 | `<rect>` 高=10px | 用菱形代替 |
| **汇合节点** | 粗水平条 | `<rect>` 高=10px | 用菱形代替 |
| **泳道** | 垂直分区 | `<rect>` 背景色 + 名称 | 缺名称 |
| **对象流** | 虚线带对象 | stroke-dasharray="6,4" | 用实线 |
| **控制流** | 实线带箭头 | stroke 实线 + 箭头 | 无箭头 |
| **监护条件** | 转换上 [条件] | `<text>` [x>0] | 漏方括号 |
| **异常流** | 闪电图标 + 路径 | 自定义 marker | 用普通箭头 |

**关键规范点**:

- 起始节点:每个活动图**只能有 1 个**起始节点(UML 2.5 严格规则)
- 结束节点:可以有**多个**,表示不同的退出路径(成功/失败/取消)
- 决策节点:出口数量与分支数量一致,每条出口必须标注监护条件
- 分叉/汇合:粗条宽度必须 ≥ 60px,便于视觉识别
- 泳道:每个泳道**必须有名称**,且名称与该角色职责对齐
- 监护条件:必须用方括号包裹,例如 `[简历有效]` `[职位匹配]`

## 3.7.3 元素完备性

| 元素 | 必须 | 说明 |
|------|------|------|
| 起始节点 | ✅ | 每个流程 1 个 |
| 结束节点 | ✅ | 每个流程 1+ 个 |
| 活动节点 | ✅ | 业务活动 |
| 控制流 | ✅ | 箭头方向 = 执行顺序 |
| 决策/合并 | ✅ | 分支逻辑 |
| 分叉/汇合 | 可选 | 并发场景 |
| 泳道 | 推荐 | 角色分工 |
| 监护条件 | ✅ | 决策分支必须标注 |
| 异常处理 | 推荐 | try-catch 路径 |

**最小完备集合**:起始节点 + 至少 1 个活动节点 + 至少 1 个结束节点 + 控制流箭头 = 最小合法活动图。

## 3.7.4 布局规范

- **泳道**: 垂直分区,每个泳道宽度 120-200px
- **活动节点间距**: 水平 ≥ 40px, 垂直 ≥ 30px
- **决策菱形**: 边长 50-60px
- **分叉/汇合**: 粗条宽 ≥ 60px,高 10px
- **流程方向**: 默认 TB (Top-to-Bottom)
- **控制流**: 不可交叉,需要交叉时用分叉/汇合

**布局原则**:

1. 主流程从左到右或从上到下,保持一致方向
2. 决策节点之后的分支应**水平展开**,避免垂直堆叠
3. 异常路径使用**不同颜色或虚线**,与正常路径视觉区分
4. 复杂流程拆分为多个子活动图,通过调用节点引用

## 3.7.5 颜色与字体

| 元素 | 色值 | 字号 |
|------|------|------|
| 起始/结束 | #333333 | — |
| 活动节点 fill | #DBEAFE stroke #1A73E8 | 13px Bold |
| 决策菱形 | #FFFFFF stroke #F59E0B | 12px |
| 分叉/汇合 | #333333 | — |
| 泳道背景 | #F8F9FA | 13px Bold |
| 控制流 | #666666 | — |
| 监护条件 | #333333 | 11px Italic |

**颜色使用规范**:

- 活动节点使用蓝色系 (DBEAFE + 1A73E8),表示可执行动作
- 决策节点使用橙色边框 (#F59E0B),与活动节点视觉区分
- 控制流使用中性灰 (#666666),不抢视觉焦点
- 监护条件使用斜体,提示这是条件而非动作

## 3.7.6 审查清单

- 是否有起始节点 (实心圆)
- 是否有结束节点 (牛眼)
- 分支逻辑是否用决策菱形
- 并发是否用分叉/汇合粗条
- 控制流箭头方向是否正确
- 泳道是否覆盖所有角色
- 监护条件是否标注
- 异常路径是否画出

**审查步骤**:

1. **结构性检查**: 起始/结束节点是否存在且数量正确
2. **连接性检查**: 每个活动节点都有入边和出边(除起始/结束节点)
3. **语义性检查**: 决策节点的所有出口都有监护条件
4. **角色完整性**: 泳道覆盖流程涉及的所有角色
5. **异常完整性**: 关键步骤都有异常处理路径

## 3.7.7 反模式

| 反模式 | 错误表现 | 正确做法 |
|--------|----------|----------|
| 决策菱形过多 | 一个流程 10+ 菱形 | 拆子流程 |
| 缺监护条件 | 决策出去无线标签 | 必标 [条件] |
| 控制流交叉 | 多条线互相穿过 | 用分叉/汇合重排 |
| 缺泳道 | 所有活动在一列 | 按角色分泳道 |
| 异常路径缺失 | 只画正常流程 | 必画异常处理 |

**其他反模式**:

- **巨型活动图**: 超过 20 个活动节点,应拆为多个子图
- **无方向控制流**: 箭头方向混乱,无法判断执行顺序
- **泳道错位**: 活动节点画在错误的泳道内
- **决策节点无合并**: 多个分支汇合时直接连线,应使用合并节点
- **监护条件歧义**: 条件描述不清,需明确布尔表达式或业务规则

## 3.7.8 完整示例 (简历投递流程)

**场景描述**: 用户上传简历后,系统解析简历内容,匹配职位库中的职位,并发投递到多个招聘平台,最后通知用户投递结果。

**流程步骤**:

1. **用户** 上传简历文件
2. **系统** 解析简历,提取关键信息
3. **决策**: 简历是否有效?
   - 否 → 通知用户重新上传 → 结束
   - 是 → 继续
4. **系统** 匹配职位库
5. **决策**: 是否匹配到职位?
   - 否 → 通知用户无匹配职位 → 结束
   - 是 → 继续
6. **分叉**: 并发投递到多个招聘平台
7. **系统** 依次调用: Boss直聘、拉勾、猎聘、LinkedIn
8. **汇合**: 等待所有平台返回结果
9. **系统** 汇总投递结果
10. **系统** 通知用户投递结果 → 结束

**SVG 示例代码**:

```svg
<svg width="800" height="700" xmlns="http://www.w3.org/2000/svg">
  <!-- 泳道背景 -->
  <rect x="0" y="0" width="800" height="700" fill="#F8F9FA"/>
  
  <!-- 泳道分隔线 -->
  <line x1="200" y1="0" x2="200" y2="700" stroke="#CCCCCC" stroke-width="1"/>
  <line x1="500" y1="0" x2="500" y2="700" stroke="#CCCCCC" stroke-width="1"/>
  
  <!-- 泳道名称 -->
  <text x="100" y="30" text-anchor="middle" font-size="13" font-weight="bold">用户</text>
  <text x="350" y="30" text-anchor="middle" font-size="13" font-weight="bold">系统</text>
  <text x="650" y="30" text-anchor="middle" font-size="13" font-weight="bold">招聘平台</text>
  
  <!-- 起始节点 -->
  <circle cx="100" cy="80" r="10" fill="#333333"/>
  
  <!-- 活动节点: 上传简历 -->
  <rect x="60" y="120" width="120" height="50" rx="10" 
        fill="#DBEAFE" stroke="#1A73E8" stroke-width="2"/>
  <text x="120" y="150" text-anchor="middle" font-size="13" font-weight="bold">上传简历</text>
  
  <!-- 控制流: 起始 → 上传简历 -->
  <line x1="100" y1="90" x2="100" y2="120" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  
  <!-- 活动节点: 解析简历 -->
  <rect x="290" y="120" width="120" height="50" rx="10" 
        fill="#DBEAFE" stroke="#1A73E8" stroke-width="2"/>
  <text x="350" y="150" text-anchor="middle" font-size="13" font-weight="bold">解析简历</text>
  
  <!-- 控制流: 上传 → 解析 -->
  <line x1="180" y1="145" x2="290" y2="145" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  
  <!-- 决策节点: 简历是否有效? -->
  <polygon points="350,210 400,245 350,280 300,245" 
           fill="#FFFFFF" stroke="#F59E0B" stroke-width="2"/>
  <text x="350" y="248" text-anchor="middle" font-size="11">简历有效?</text>
  
  <!-- 控制流: 解析 → 决策 -->
  <line x1="350" y1="170" x2="350" y2="210" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  
  <!-- 否分支: 通知重新上传 -->
  <rect x="60" y="320" width="120" height="50" rx="10" 
        fill="#DBEAFE" stroke="#1A73E8" stroke-width="2"/>
  <text x="120" y="350" text-anchor="middle" font-size="11">通知重新上传</text>
  
  <!-- 否分支控制流 -->
  <line x1="300" y1="245" x2="180" y2="245" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  <line x1="120" y1="245" x2="120" y2="320" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  <text x="200" y="238" font-size="11" font-style="italic" fill="#333333">[否]</text>
  
  <!-- 是分支: 匹配职位 -->
  <rect x="290" y="320" width="120" height="50" rx="10" 
        fill="#DBEAFE" stroke="#1A73E8" stroke-width="2"/>
  <text x="350" y="350" text-anchor="middle" font-size="13" font-weight="bold">匹配职位</text>
  
  <!-- 是分支控制流 -->
  <line x1="350" y1="280" x2="350" y2="320" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  <text x="360" y="305" font-size="11" font-style="italic" fill="#333333">[是]</text>
  
  <!-- 分叉节点 -->
  <rect x="320" y="400" width="60" height="10" fill="#333333"/>
  
  <!-- 控制流: 匹配 → 分叉 -->
  <line x1="350" y1="370" x2="350" y2="400" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  
  <!-- 并发投递到多平台 -->
  <rect x="540" y="440" width="120" height="40" rx="10" 
        fill="#DBEAFE" stroke="#1A73E8" stroke-width="2"/>
  <text x="600" y="465" text-anchor="middle" font-size="11">Boss直聘</text>
  
  <rect x="540" y="490" width="120" height="40" rx="10" 
        fill="#DBEAFE" stroke="#1A73E8" stroke-width="2"/>
  <text x="600" y="515" text-anchor="middle" font-size="11">拉勾</text>
  
  <rect x="540" y="540" width="120" height="40" rx="10" 
        fill="#DBEAFE" stroke="#1A73E8" stroke-width="2"/>
  <text x="600" y="565" text-anchor="middle" font-size="11">猎聘</text>
  
  <!-- 分支控制流 -->
  <line x1="380" y1="405" x2="540" y2="460" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  <line x1="380" y1="405" x2="540" y2="510" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  <line x1="380" y1="405" x2="540" y2="560" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  
  <!-- 异常处理: 投递失败重试 -->
  <text x="600" y="600" text-anchor="middle" font-size="11" font-style="italic" fill="#DC2626">⚡ 失败重试</text>
  
  <!-- 汇合节点 -->
  <rect x="320" y="620" width="60" height="10" fill="#333333"/>
  
  <!-- 汇合控制流 -->
  <line x1="540" y1="480" x2="380" y2="625" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  <line x1="540" y1="530" x2="380" y2="625" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  <line x1="540" y1="580" x2="380" y2="625" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  
  <!-- 通知结果 -->
  <rect x="290" y="650" width="120" height="40" rx="10" 
        fill="#DBEAFE" stroke="#1A73E8" stroke-width="2"/>
  <text x="350" y="675" text-anchor="middle" font-size="11">通知用户结果</text>
  
  <!-- 控制流: 汇合 → 通知 -->
  <line x1="350" y1="630" x2="350" y2="650" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  
  <!-- 结束节点 -->
  <circle cx="350" cy="710" r="10" fill="#333333"/>
  <circle cx="350" cy="710" r="6" fill="#FFFFFF"/>
  
  <!-- 控制流: 通知 → 结束 -->
  <line x1="350" y1="690" x2="350" y2="700" stroke="#666666" stroke-width="2" 
        marker-end="url(#arrow)"/>
  
  <!-- 箭头标记定义 -->
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" 
            orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#666666"/>
    </marker>
  </defs>
</svg>
```

**示例要点说明**:

1. **3 个泳道**: 用户、系统、招聘平台,清晰划分职责
2. **1 个决策菱形**: 简历是否有效?出口标注 `[是]` / `[否]`
3. **1 个分叉/汇合**: 匹配职位后并发投递到 Boss直聘/拉勾/猎聘
4. **1 个异常路径**: 投递失败时触发重试 (⚡ 闪电图标)
5. **监护条件**: `[是]` / `[否]` 标注在分支出口
6. **起始/结束节点**: 1 个实心圆起始,1 个牛眼结束

---

**返回**: [作图-README.md](./作图-README.md) | [作图-01-通用规范.md](./作图-01-通用规范.md)
