# UML 状态机图 (UML State Machine Diagram)

> **来源**: 拆分自 作图大全标准.md v1.6 §3.8 + 补充
> **拆分日期**: 2026-08-15
> **关联文档**: [作图-01-通用规范.md](./作图-01-通用规范.md) | [作图-README.md](./作图-README.md)
> **UML 版本**: 2.5
> **新增**: 完整补充原 §3.8 待补充章节 (本次重点)

---

## 3.8.1 决策目标

状态机图 (State Machine Diagram) 是 UML 行为图中专门用于描述**对象生命周期内状态变化**的图。它关注"对象在什么状态下、能响应什么事件、转换到什么状态",而不是"对象做了什么活动"——这一点必须与活动图严格区分。

| 问题 | 答案 |
|------|------|
| 支持什么决策 | 对象生命周期有哪些状态?什么事件触发状态转换?守卫条件是什么? |
| 谁读 | 后端开发、状态机实现者、业务方 |
| 决策后果 | 状态遗漏 → 死循环 / 状态机实现错 → 业务 bug |

### 适用场景
- **业务对象生命周期**: 订单状态(待支付/已支付/已发货/已完成/已取消)
- **审批流程**: 审批单状态流转
- **任务/作业调度**: 投递任务、解析任务的状态机
- **资源生命周期**: 连接池对象、线程、token 的状态
- **协议状态机**: TCP 连接状态、设备握手状态
- **复合状态**: 包含子状态机的复杂状态(如 "运行中" 内含多个子状态)

### 不适用场景
- 仅展示业务流程(用 BPMN 或活动图)
- 描述对象结构(用类图)
- 描述对象协作(用时序图)

### 关键术语

| 术语 | 英文 | 定义 |
|------|------|------|
| **状态** | State | 对象生命周期中的一个阶段, 在该阶段对象满足某些条件、等待某些事件 |
| **事件** | Event | 触发状态转换的输入, 可以是信号、调用、时间等 |
| **转换** | Transition | 源状态 → 目标状态的有向关系, 由事件触发 |
| **守卫条件** | Guard | 转换前的布尔判断条件, 写在方括号内 `[condition]` |
| **动作** | Action | 转换时执行的行为, 写在斜杠后 `/action` |
| **内部活动** | Internal Activity | 状态内部响应事件但不离开状态, 写法 `event/action` |
| **进入动作** | Entry Action | 进入状态时自动执行, 关键字 `entry` |
| **退出动作** | Exit Action | 离开状态时自动执行, 关键字 `exit` |
| **do 活动** | Do Activity | 处于该状态时持续执行, 关键字 `do` |
| **复合状态** | Composite State | 包含子状态机的状态 |
| **历史状态** | History State | 记住上次退出时所在的子状态, 标记 `H` |
| **起始伪状态** | Initial Pseudostate | 状态机入口, 实心圆 |
| **终止伪状态** | Final Pseudostate | 状态机出口, 牛眼(同心圆) |
| **选择伪状态** | Choice Pseudostate | 动态分支决策, 空心菱形 |
| **连接伪状态** | Junction Pseudostate | 静态连接点, 实心小圆 |
| **深历史** | Deep History | 记住所有嵌套层级的子状态, `H*` |
| **浅历史** | Shallow History | 只记住当前复合状态的直接子状态, `H` |

---

## 3.8.2 UML 2.5 语法合规

下表对照 UML 2.5 OMG 规范、SVG 实现细节、常见错误, 是绘图与审查的统一基准。

| 元素 | UML 2.5 规范 | SVG 实现 | 常见错误 |
|------|-------------|----------|----------|
| **状态** | 圆角矩形 + 状态名 | `<rect rx=10 ry=10>` | 直角矩形 (违反规范) |
| **状态名分区** | 状态名 / 内部活动 (entry/exit/do) | `<line>` 在状态内部分隔 | 缺分隔线, 内部活动与名字混排 |
| **起始伪状态** | 实心圆, 黑色填充 | `<circle>` r=8 fill=#333 | 漏起始 (状态机无入口) |
| **终止伪状态** | 牛眼(实心圆 + 外环) | 2 同心圆, 内 r=6 外 r=10 | 单圆 (与起始混淆) |
| **转换箭头** | 实线 + 普通箭头 (三角箭头) | stroke 实线 + marker-end 箭头 | 无箭头 (方向不明) |
| **事件标签** | `event` 或 `event[guard]/action` | `<text>` 多行, 事件顶, 守卫中, 动作底 | 缺格式 / 三段混一行 |
| **内部转换** | 状态内的事件, 写法 `event/action` | `<text>` 在状态内 (无箭头) | 与外部转换混 (误带箭头) |
| **进入动作** | `entry / action` | 状态内顶部第一行 | 漏 `entry` 关键字 |
| **退出动作** | `exit / action` | 状态内底部最后一行 | 漏 `exit` 关键字 |
| **do 活动** | `do / activity` | 状态内中间行 | 漏 `do` 关键字 |
| **复合状态** | 大状态包含子状态, 视觉上嵌套 | 大 rect 内嵌子状态 + 子状态之间的转换 | 缺嵌套视觉 (用并列表示) |
| **历史状态** | 圆圈带 H | `<circle>` + `<text>H</text>` | 用普通起始代替 (语义错误) |
| **选择伪状态** | 空心菱形 | `<polygon>` fill=#fff stroke=#333 | 与活动图菱形混 (无区分) |
| **连接伪状态** | 实心圆, 较小 | `<circle>` r=6 fill=#333 | 与起始混 (大小一致) |
| **深历史** | 圆圈带 H* | `<circle>` + `<text>H*</text>` | 缺星号 (深浅不分) |
| **转换优先级** | 守卫为 true 的转换 | 多个守卫按声明顺序 | 隐式依赖顺序 (无声明) |

### 状态的内部结构

一个完整的状态可以分成 3 个分区, 用横线分隔:

```
┌─────────────────────────┐
│ 状态名 / State Name     │  ← 必选
├─────────────────────────┤
│ entry / 进入动作        │  ← 可选
│ do / 持续活动           │  ← 可选
│ exit / 退出动作         │  ← 可选
│ event / 内部转换        │  ← 可选
└─────────────────────────┘
```

**说明**:
- 分区从上到下顺序固定: 名字 → entry → do → exit → 内部转换
- 每个分区内容用 `关键字 / 动作` 格式
- 内部转换不离开状态, 适合 "鼠标悬停" 等响应

### 状态名命名约束

- 必须用**名词或名词短语** (描述对象处于什么阶段)
- 不能是动词 (动词属于活动图)
- 不能含 "状态" 后缀 (图本身就是状态机)
- 推荐中英双语: `待解析(Pending)` 或 `解析中(Parsing)`

---

## 3.8.3 转换语法

### UML 2.5 标准格式

```
event-name [guard-condition] / action-list
```

**示例**:
```
按下按钮 [金额>0] / 余额扣减
```

### 三段说明

| 部分 | 必选 | 含义 | 格式 |
|------|------|------|------|
| event-name | ✅ | 触发事件名 | 名词或动词短语, 如 `click`、`start_parse` |
| guard-condition | 可选 | 布尔表达式, true 才转换 | 方括号包裹, 如 `[x>0]` `[retry<3]` |
| action-list | 可选 | 转换时执行的动作 | 斜杠后空格分隔, 如 `/ 余额扣减; 通知` |

### 多事件触发

同一转换可由多个事件触发, 用逗号分隔:

```
click, double_click [enabled] / handle
```

### 延迟事件

事件可标注延迟, 用 `after` 关键字:

```
after(10s) [still_pending] / 触发告警
```

### 触发器类型

| 类型 | 语法 | 示例 |
|------|------|------|
| 信号事件 | `signal-name` | `doorOpened` |
| 调用事件 | `operation-name()` | `submit()` |
| 时间事件 | `after(duration)` | `after(30s)` |
| 变化事件 | `when(condition)` | `when(temp>100)` |
| 发送者 | `sender-object.event-name` | `controller.timeout` |

### 转换的完整标注顺序

```
event [guard1, guard2] / action1; action2
```

**注意**:
- 多个守卫用逗号分隔, 必须**全部**为 true 才转换
- 多个动作按顺序执行, 用分号或换行分隔
- action 不能影响 guard 判定结果 (避免循环依赖)

---

## 3.8.4 元素完备性

| 元素 | 必须 | 说明 | 缺失后果 |
|------|------|------|----------|
| 起始伪状态 | ✅ | 状态机唯一入口 | 状态机无法启动 |
| 终止伪状态 | 可选 | 多个终止(成功/失败) | 业务终止状态不明 |
| 状态 | ✅ | 全部枚举 | 遗漏状态 → 实现 bug |
| 转换 | ✅ | 全部事件触发 | 事件丢失 → 死锁 |
| 事件名 | ✅ | 转换必带 | 行为不明 → 难实现 |
| 守卫条件 | 推荐 | 关键转换加 | 边界条件丢失 |
| 动作 | 可选 | 复杂业务加 | 副作用不明 |
| 复合状态 | 可选 | 状态 ≥ 7 用 | 图混乱不可读 |
| 历史状态 | 可选 | 复合状态内 | 进入复合态时丢失上下文 |
| 进入/退出动作 | 可选 | 资源管理 | 资源泄漏 |

### 完备性最低要求

- 每个状态机**至少 1 个起始伪状态**
- 每个状态机**至少 1 个终止伪状态** (除非永远循环, 如心跳)
- 每个状态**至少 1 条入转换** (除起始直接指向的状态)
- 每个状态**至少 1 条出转换** (除非终止状态或吸收态)
- 关键业务**全部路径**必须有对应状态 (含失败/超时/取消)

---

## 3.8.5 布局规范

### 状态矩形尺寸

| 类型 | 最小尺寸 | 推荐尺寸 | 圆角 |
|------|----------|----------|------|
| 简单状态 | 100×50px | 120×60px | rx=10 |
| 含内部活动状态 | 100×80px | 130×100px | rx=10 |
| 复合状态 | 200×120px | 240×150px | rx=12 |
| 复合状态(含 3+ 子状态) | 280×160px | 320×200px | rx=12 |

### 间距

| 维度 | 最小间距 | 推荐间距 |
|------|----------|----------|
| 水平 (状态之间) | 60px | 100px |
| 垂直 (状态之间) | 40px | 70px |
| 转换标签与线 | 4px | 8px |
| 起始/终止与状态 | 30px | 50px |
| 复合状态外边距 | 20px | 30px |

### 起始/终止伪状态尺寸

| 类型 | 半径 | 颜色 |
|------|------|------|
| 起始伪状态 | r=8px | #333333 |
| 终止伪状态 | 外环 r=10px, 内圆 r=6px | #333333 |
| 连接伪状态 | r=6px | #333333 |
| 历史状态 | r=10px | #333333 |
| 选择伪状态 | 边长 20px | 空心 #333 |

### 转换标签位置

- **位置**: 转换线中点上方 4px
- **对齐**: 居中于转换线
- **多行格式**: 事件名顶 / 守卫中 / 动作底, 三行
- **标签背景**: 白色矩形 + 1px 描边, 防止与转换线重叠

### 复合状态布局

- 外层 rect 与内嵌子状态之间至少 20px 内边距
- 子状态在外层 rect 内按子状态机布局
- 历史状态放在复合状态内**右上角**
- 起始伪状态放在复合状态**左上角**
- 终止伪状态放在复合状态**右下角**

### 转换方向策略

- **主流程**: 从左到右, 从上到下
- **重试/回退**: 向下走, 用虚线或红色标识
- **成功/失败分支**: 在状态右侧用选择伪状态分流
- **避免交叉**: 必要时用连接伪状态(`<junction>`) 跳转
- **回环转换**: 自转换(状态转换回自身)用弧形, 半径 ≥ 30px

---

## 3.8.6 颜色与字体

### 配色表

| 元素 | 填充 | 描边 | 字号 | 字重 | 备注 |
|------|------|------|------|------|------|
| 起始伪状态 | #333333 | 无 | — | — | 实心圆 |
| 终止伪状态 | #333333 | 无 | — | — | 牛眼 |
| 连接伪状态 | #333333 | 无 | — | — | 较小实心圆 |
| 历史状态 | #333333 | 无 | 10px | Bold | 圆圈带 H |
| 选择伪状态 | #ffffff | #333333 1.5px | — | — | 空心菱形 |
| 状态 fill | #DBEAFE | #1A73E8 1.5px | 13px | Bold | 主流程 |
| 状态名 | — | — | 13px | Bold | #1f2937 |
| 内部活动 (entry/exit/do) | — | — | 11px | Regular | #475569 |
| 转换线 | — | #64748b 1.5px | — | — | 实线 |
| 事件名 | — | — | 11px | Regular | #333333 |
| 守卫条件 | — | — | 10px | Italic | #1A73E8 蓝色斜体 |
| 动作 | — | — | 10px | Regular | #F59E0B 橙色 |
| 复合状态边框 | #EFF6FF | #1A73E8 2.5px | 13px | Bold | 视觉嵌套 |
| 复合状态内子状态 | #FFFFFF | #1A73E8 1px | 12px | Regular | 子状态样式 |
| 重试/回退转换 | — | #EF4444 1.5px | 11px | Regular | 虚线 (stroke-dasharray=4 2) |
| 异常转换 | — | #DC2626 1.5px | 11px | Regular | 红色实线 |

### 字体栈

```
font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
```

### 颜色语义

- **蓝色 (#1A73E8)**: 状态主色、守卫条件, 表示"业务正常"
- **橙色 (#F59E0B)**: 动作, 表示"行为"
- **灰色 (#64748b)**: 转换线, 表示"连接"
- **红色 (#EF4444)**: 回退/异常, 表示"风险"
- **深灰 (#1f2937)**: 文字主色, 表示"标题"
- **中灰 (#475569)**: 文字次色, 表示"说明"

---

## 3.8.7 审查清单

### 基础结构审查

- [ ] 是否有起始伪状态 (实心圆)
- [ ] 是否所有状态都标注了名字
- [ ] 状态名是否用名词/名词短语 (非动词)
- [ ] 是否有终止伪状态 (业务允许的话)
- [ ] 起始到第一个状态之间是否有转换

### 转换完整性审查

- [ ] 所有转换是否带事件名
- [ ] 关键守卫条件是否用方括号 `[condition]`
- [ ] 守卫条件表达式是否明确 (无歧义)
- [ ] 动作是否用斜杠分隔 `/action`
- [ ] 转换箭头方向是否正确 (源 → 目标)
- [ ] 是否有未处理的异常状态 (失败/超时/取消)
- [ ] 同事件多守卫是否有优先级说明

### 状态完整性审查

- [ ] 每个状态是否都有入转换 (除起始直接指向)
- [ ] 每个状态是否都有出转换 (除终止或吸收态)
- [ ] 是否有死状态 (有入无出)
- [ ] 是否有不可达状态 (有出无入)
- [ ] 业务关键路径是否全部覆盖

### 复合状态审查 (如有)

- [ ] 复合状态是否用视觉嵌套表示
- [ ] 复合状态内是否有起始伪状态
- [ ] 历史状态是否放在右上角
- [ ] 内部转换是否标注在状态内 (非带箭头)
- [ ] entry/exit 动作是否标注完整

### 视觉规范审查

- [ ] 状态圆角是否为 10px
- [ ] 间距是否符合规范 (水平 ≥ 60px, 垂直 ≥ 40px)
- [ ] 颜色是否符合配色表
- [ ] 字体是否统一
- [ ] 转换标签是否在转换线中点上方
- [ ] 是否有交叉转换 (应避免)
- [ ] 状态机是否覆盖所有路径 (正常 + 异常)

### 业务正确性审查

- [ ] 状态机是否覆盖所有业务分支
- [ ] 重试逻辑是否标注守卫 `[重试次数<3]`
- [ ] 超时处理是否有对应状态或事件
- [ ] 并发/竞态场景是否考虑
- [ ] 状态机是否与代码实现一致 (可对照)

---

## 3.8.8 反模式

| 反模式 | 错误表现 | 正确做法 |
|--------|----------|----------|
| **缺起始状态** | 状态机没有入口, 多个状态不知从哪开始 | 必有起始伪状态 (实心圆) |
| **转换无线标签** | 转换无事件名, 只画箭头 | 必标 event (e.g. `start_parse`) |
| **状态过多** | 单状态机 15+ 状态平铺, 难以阅读 | 拆复合状态, 状态 ≥ 7 必须分层 |
| **死状态** | 状态有入无出, 永远卡住 | 删除状态, 或补出转换 |
| **不可达状态** | 状态有出无入, 永远进不去 | 删除状态, 或补入转换 |
| **状态与活动图混** | 用状态图元素画活动图 (用判定菱形) | 严格区分: 状态图菱形=选择伪状态, 活动图菱形=决策 |
| **守卫条件漏** | `[x>0]` 漏方括号, 写成 `x>0` | 必须 `[条件]`, 用方括号包裹 |
| **复合状态无嵌套视觉** | 状态并列, 无视觉包含关系 | 必须外层 rect 包含子状态, 用嵌套视觉 |
| **entry 漏关键字** | 状态内只写动作, 漏 `entry /` | 必须 `entry / 动作` |
| **自转换误用内部转换** | 在状态内画自循环箭头 | 自转换是外部转换, 内部转换不离开状态 |
| **多起始伪状态** | 状态机有 2+ 起始 (除复合状态内) | 状态机只 1 个起始 (复合状态可内嵌) |
| **无终止的循环** | 状态机画成无限循环无出口 | 必须有终止 (除非心跳/监听器) |
| **动作写成自然语言** | `/ 通知用户处理一下` | 必须用动词短语, `/ send_email` |
| **状态名含动词** | `正在处理` `已完成` 中 "已" 表示完成 | 状态是阶段, 用 `处理中` `完成` |
| **混用中英术语** | 同一文档 `State` 和 `状态` 混用 | 统一术语, 推荐中英双语 `状态名(English)` |
| **重试无限次** | 守卫缺失, 一直重试 | 必须 `[retry_count<3]`, 限制重试 |
| **超时无处理** | 状态机无超时状态 | 必须有 `超时(Timeout)` 状态或 `after()` 事件 |
| **守卫依赖动作结果** | 守卫中判断动作执行后的状态 | 守卫基于状态属性, 非动作副作用 |
| **转换标签跨线** | 多条转换标签互相覆盖 | 用连接伪状态或重新布局 |
| **过度细分状态** | 把 1 步操作拆成 3 个状态 | 状态是稳定阶段, 中间步骤可不建模 |

---

## 3.8.9 完整示例 (投递记录状态机)

### 业务背景

`ApplicationRecord` (投递记录) 是核心业务对象, 表示一次简历投递。投递记录从创建到结束会经历多个状态, 每个状态对应不同的处理逻辑。

### 状态清单

| 状态 | 中文 | 含义 |
|------|------|------|
| Pending | 待解析 | 记录已创建, 等待解析 |
| Parsing | 解析中 | 正在解析简历内容 |
| Matched | 已匹配 | 解析完成, 已匹配岗位 |
| Sending | 投递中 | 正在投递 (复合状态) |
| Waiting | 等待回调 | (Sending 内) 已发起请求, 等待对方响应 |
| Sent | 已投递 | 投递成功 |
| Failed | 失败 | 投递失败 (含多次重试) |
| Cancelled | 已取消 | 用户主动取消 |

### 事件清单

| 事件 | 触发时机 | 守卫 |
|------|----------|------|
| start_parse | 用户提交后, 系统开始解析 | — |
| parse_complete | 简历解析完成 | — |
| match_found | 匹配到岗位 | — |
| send_request | 发起投递请求 | `[匹配岗位存在]` |
| callback_received | 收到对方响应 | — |
| send_success | 投递成功响应 | — |
| send_failure | 投递失败响应 | `[重试次数<3]` |
| retry | 失败后人工/自动重试 | `[重试次数<3]` |
| timeout | 等待回调超时 (30s) | — |
| cancel | 用户取消 | — |
| max_retry_exceeded | 重试次数耗尽 | — |

### 守卫与动作

| 转换 | 守卫 | 动作 |
|------|------|------|
| Pending → Parsing | — | `entry / 记录开始时间` |
| Parsing → Matched | — | `entry / 保存解析结果` |
| Matched → Sending | `[匹配岗位存在]` | `entry / 初始化重试计数=0` |
| Sending → Sent | — | `exit / 关闭连接` |
| Sending → Failed | `[重试次数≥3]` | `exit / 记录失败原因` |
| Sending → Sending | `[重试次数<3]` | `entry / 重试次数+1; 重新发起请求` |
| 任意非终止态 → Cancelled | `[用户已认证]` | `exit / 清理资源` |

### 内部活动 (entry/exit)

| 状态 | entry | do | exit |
|------|-------|-----|------|
| Pending | `记录创建时间` | — | `删除临时文件` |
| Parsing | `启动解析任务` | `解析简历内容` | `保存解析结果` |
| Sending | `初始化重试计数=0` | `轮询回调状态` | `关闭连接, 释放资源` |
| Failed | `记录失败原因, 触发告警` | — | — |
| Cancelled | `记录取消原因` | — | `清理临时数据` |

### 状态机 SVG 示意 (文本描述版)

```
              [start_parse]
                   │
                   ▼
            ┌─────────────┐
            │  待解析     │ entry: 记录创建时间
            │  Pending    │ exit:  删除临时文件
            └──────┬──────┘
                   │ parse_complete
                   ▼
            ┌─────────────┐
            │  解析中     │ entry: 启动解析任务
            │  Parsing    │ do:    解析简历内容
            └──────┬──────┘
                   │ parse_complete
                   ▼
            ┌─────────────┐
            │  已匹配     │ entry: 保存解析结果
            │  Matched    │
            └──────┬──────┘
                   │ send_request [匹配岗位存在]
                   ▼
        ╔════════════════════╗
        ║ ┌──────────────┐   ║
        ║ │   投递中     │   ║   entry: 初始化重试计数
        ║ │   Sending    │   ║   do:    轮询回调
        ║ │ (复合状态)   │   ║   exit:  关闭连接
        ║ └──────┬───────┘   ║
        ║        │           ║
        ║        ▼           ║
        ║ ┌──────────────┐   ║
        ║ │  等待回调    │   ║
        ║ │  Waiting     │   ║
        ║ └─┬──────────┬─┘   ║
        ║   │          │     ║
        ║   │          │     ║
        ╚═══│══════════│═════╝
            │          │
   callback │          │ timeout (30s)
            ▼          ▼
       ┌─────────┐  ┌─────────┐
       │ 已投递  │  │  失败   │  entry: 记录失败原因
       │  Sent   │  │ Failed  │  exit:  释放资源
       └────┬────┘  └────┬────┘
            │           │ max_retry_exceeded
            │           │ 或 retry [重试次数<3]
            │           └──────┐
            │                  │
            │ cancel           ▼
            │  [用户已认证]   (回到 Sending 内部, 重试次数+1)
            ▼
       ┌──────────┐
       │ 已取消   │  entry: 记录取消原因
       │Cancelled │  exit:  清理临时数据
       └──────────┘
```

### 转换表 (Transition Table)

| 源状态 | 事件 | 守卫 | 目标状态 | 动作 |
|--------|------|------|----------|------|
| 起始 | start_parse | — | Pending | 记录创建时间 |
| Pending | parse_complete | — | Parsing | 启动解析任务 |
| Parsing | parse_complete | — | Matched | 保存解析结果 |
| Matched | send_request | `[匹配岗位存在]` | Sending.Waiting | 初始化重试计数=0 |
| Sending.Waiting | callback_received + send_success | — | Sent | 关闭连接 |
| Sending.Waiting | callback_received + send_failure | `[重试次数<3]` | Sending.Waiting | 重试次数+1, 重新发起 |
| Sending.Waiting | timeout | — | Sending | 触发重试判断 |
| Sending | max_retry_exceeded | — | Failed | 记录失败原因 |
| Sending | retry | `[重试次数<3]` | Sending | 重试次数+1 |
| 任意非终止 | cancel | `[用户已认证]` | Cancelled | 清理资源 |

### 实现代码对照 (Java enum + Spring StateMachine)

```java
public enum RecordState {
    PENDING, PARSING, MATCHED, SENDING, SENT, FAILED, CANCELLED
}

public enum RecordEvent {
    START_PARSE, PARSE_COMPLETE, SEND_REQUEST, CALLBACK_RECEIVED,
    SEND_SUCCESS, SEND_FAILURE, TIMEOUT, RETRY, MAX_RETRY_EXCEEDED, CANCEL
}

// Spring StateMachine 配置示例
@Configuration
@EnableStateMachineFactory
public class RecordStateMachineConfig
        extends EnumStateMachineConfigurerAdapter<RecordState, RecordEvent> {

    @Override
    public void configure(StateMachineStateConfigurer<RecordState, RecordEvent> states)
            throws Exception {
        states.withStates()
            .initial(RecordState.PENDING)
            .end(RecordState.SENT)
            .end(RecordState.FAILED)
            .end(RecordState.CANCELLED)
            .state(RecordState.SENDING);  // 复合状态, 内含子状态机
    }

    @Override
    public void configure(StateMachineTransitionConfigurer<RecordState, RecordEvent> transitions)
            throws Exception {
        transitions
            .withExternal()
                .source(PENDING).target(PARSING).event(START_PARSE)
                .action(recordStartTimeAction())
            .and()
            .withExternal()
                .source(PARSING).target(MATCHED).event(PARSE_COMPLETE)
                .guard(matchedGuard())
                .action(saveParseResultAction())
            .and()
            .withExternal()
                .source(MATCHED).target(SENDING).event(SEND_REQUEST)
                .guard(matchedGuard())
                .action(initRetryCountAction())
            .and()
            .withExternal()
                .source(SENDING).target(SENT).event(SEND_SUCCESS)
                .action(closeConnectionAction())
            .and()
            .withExternal()
                .source(SENDING).target(SENDING).event(RETRY)
                .guard(retryGuard())  // [重试次数<3]
                .action(incrementRetryAction())
            .and()
            .withExternal()
                .source(SENDING).target(FAILED).event(MAX_RETRY_EXCEEDED)
                .action(recordFailureAction());
    }
}
```

### 测试用例对照

| 测试场景 | 起始状态 | 事件序列 | 期望终止状态 |
|----------|----------|----------|--------------|
| 正常流程 | PENDING | START_PARSE → PARSE_COMPLETE → SEND_REQUEST → SEND_SUCCESS | SENT |
| 重试成功 | PENDING | ... → SEND_FAILURE × 2 → RETRY × 2 → SEND_SUCCESS | SENT |
| 重试超限 | PENDING | ... → SEND_FAILURE × 3 → MAX_RETRY_EXCEEDED | FAILED |
| 超时 | PENDING | ... → SEND_REQUEST → TIMEOUT → MAX_RETRY_EXCEEDED | FAILED |
| 用户取消 | PENDING | CANCEL | CANCELLED |
| 解析中取消 | PARSING | CANCEL | CANCELLED |
| 匹配不到岗位 | MATCHED | SEND_REQUEST (guard=false) | MATCHED (保持) |

### 关键设计决策

1. **SENDING 是复合状态**: 内部 Waiting 子状态可被 retry/timeout 反复触发, 复合状态封装了"重试"逻辑
2. **3 个终止状态**: Sent/Failed/Cancelled, 业务有明确终态, 不混用
3. **守卫 `[重试次数<3]`**: 防止无限重试, 资源安全
4. **任意状态可取消**: 业务允许用户中途取消, 通过全状态转换实现
5. **entry/exit 资源管理**: 进入解析启动任务, 退出释放资源, 避免泄漏

---

## 附录: SVG 代码片段

### 起始伪状态

```svg
<circle cx="50" cy="50" r="8" fill="#333333" />
```

### 终止伪状态 (牛眼)

```svg
<circle cx="50" cy="50" r="10" fill="none" stroke="#333333" stroke-width="1.5" />
<circle cx="50" cy="50" r="6" fill="#333333" />
```

### 简单状态

```svg
<rect x="40" y="30" width="120" height="60" rx="10" ry="10"
      fill="#DBEAFE" stroke="#1A73E8" stroke-width="1.5" />
<text x="100" y="55" text-anchor="middle"
      font-size="13" font-weight="bold" fill="#1f2937">待解析</text>
<text x="100" y="72" text-anchor="middle"
      font-size="11" fill="#475569">Pending</text>
```

### 含内部活动的状态

```svg
<rect x="40" y="30" width="140" height="90" rx="10" ry="10"
      fill="#DBEAFE" stroke="#1A73E8" stroke-width="1.5" />
<text x="110" y="50" text-anchor="middle"
      font-size="13" font-weight="bold" fill="#1f2937">解析中</text>
<line x1="40" y1="60" x2="180" y2="60" stroke="#1A73E8" stroke-width="0.5" />
<text x="50" y="75" font-size="11" fill="#475569">entry / 启动解析任务</text>
<text x="50" y="90" font-size="11" fill="#475569">do / 解析简历内容</text>
<text x="50" y="105" font-size="11" fill="#475569">exit / 保存解析结果</text>
```

### 历史状态

```svg
<circle cx="100" cy="100" r="10" fill="none" stroke="#333333" stroke-width="1.5" />
<text x="100" y="105" text-anchor="middle" font-size="10" font-weight="bold" fill="#333333">H</text>
```

### 转换箭头

```svg
<defs>
  <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3"
          orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L0,6 L9,3 z" fill="#64748b" />
  </marker>
</defs>
<line x1="100" y1="100" x2="200" y2="100" stroke="#64748b" stroke-width="1.5"
      marker-end="url(#arrowhead)" />
```

### 复合状态 (含子状态)

```svg
<!-- 外层复合状态 -->
<rect x="200" y="100" width="240" height="180" rx="12" ry="12"
      fill="#EFF6FF" stroke="#1A73E8" stroke-width="2.5" />
<text x="220" y="125" font-size="13" font-weight="bold" fill="#1f2937">投递中 (Sending)</text>

<!-- 内嵌子状态 -->
<rect x="230" y="160" width="100" height="50" rx="10" ry="10"
      fill="#FFFFFF" stroke="#1A73E8" stroke-width="1" />
<text x="280" y="190" text-anchor="middle" font-size="12" fill="#1f2937">等待回调</text>
```

### 选择伪状态 (空心菱形)

```svg
<polygon points="50,40 70,60 50,80 30,60"
         fill="#ffffff" stroke="#333333" stroke-width="1.5" />
```

### 完整转换标签 (三行)

```svg
<text x="150" y="80" text-anchor="middle" font-size="11" fill="#333333">send_request</text>
<text x="150" y="94" text-anchor="middle" font-size="10" font-style="italic" fill="#1A73E8">[匹配岗位存在]</text>
<text x="150" y="108" text-anchor="middle" font-size="10" fill="#F59E0B">/ 初始化重试计数</text>
```

---

## 附录: 状态机 vs 活动图 关键区别

很多同学会混淆状态图和活动图, 这里强调核心区别:

| 维度 | 状态机图 | 活动图 |
|------|----------|--------|
| **关注点** | 对象处于什么状态 | 对象做什么活动 |
| **节点** | 状态 (名词) | 活动 (动词) |
| **边** | 事件触发转换 | 控制流 (完成/决策) |
| **菱形** | 选择伪状态 (动态分支) | 决策节点 (静态条件) |
| **起点** | 起始伪状态 (实心圆) | 起始节点 (实心圆) |
| **终点** | 终止伪状态 (牛眼) | 结束节点 (牛眼/空心环) |
| **守卫** | 转换上的 `[condition]` | 决策菱形上的条件 |
| **泳道** | ❌ 不支持 | ✅ 支持 |
| **并发** | 复合状态/正交区 | 分叉/汇合 |
| **典型用途** | 对象生命周期 | 业务流程/算法 |

**简单记忆**:
- 状态图: "我是什么, 我能去哪里"
- 活动图: "我要做什么, 接下来做什么"

---

## 附录: 常见状态机框架对照

| 框架/库 | 语言 | 特点 | 适用场景 |
|---------|------|------|----------|
| Spring StateMachine | Java | 注解式配置, 支持复合状态/历史 | Spring 项目 |
| Stateless | C# | 轻量级, 流畅 API | .NET 项目 |
| XState | TypeScript | 可视化编辑, 嵌套状态机 | 前端 React/Vue |
| Stateless4j | Java | 极轻量, 无 Spring 依赖 | 嵌入式 |
| Squirrel | C++ | 高性能状态机 | 嵌入式/游戏 |
| Boost.Statechart | C++ | 模板元编程 | C++ 复杂状态机 |
| Pytransitions | Python | 简单装饰器 | Python 脚本 |
| Automat | Python | 基于协程 | 异步流程 |

**选型建议**:
- Java + Spring: Spring StateMachine (成熟)
- Java 嵌入式: Stateless4j (无依赖)
- TypeScript 前端: XState (生态完整)
- Python: Pytransitions (简单) 或 Automat (异步)

---

## 附录: 与其他图的关系

| 关系图 | 协同点 | 典型场景 |
|--------|--------|----------|
| **类图** | 状态机描述类的实例行为 | 一个 Order 类对应 Order 状态机 |
| **时序图** | 状态机刻画对象生命周期, 时序图展示对象间消息 | Order 状态机 + Order↔Payment↔Inventory 时序 |
| **活动图** | 状态机是状态视角, 活动图是动作视角 | 状态机看 Order 是什么状态, 活动图看 Order 怎么流转 |
| **用例图** | 状态机可标注在用例的 "事件流" 中 | 提交订单用例 → 创建 Order 状态机 |
| **组件图** | 状态机可作为组件内部行为文档 | 投递组件内嵌 ApplicationRecord 状态机 |

---

**参考资源**:
- UML 2.5 规范 (OMG): https://www.omg.org/spec/UML/2.5.1/
- Spring StateMachine 文档: https://docs.spring.io/spring-statemachine/docs/current/reference/
- XState 文档: https://xstate.js.org/docs/
- 团队内部: `design/作图大全标准.md` §3.8

---

**返回**: [作图-README.md](./作图-README.md) | [作图-01-通用规范.md](./作图-01-通用规范.md)
