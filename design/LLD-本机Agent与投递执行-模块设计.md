# LLD 详细设计：本机 Agent 与投递执行

> 文档版本：2026-08-15 · v1.2（交付级 LLD，首选模块；v1.1 修复 F-1/F-2/F-3；v1.2 修复评审 F-4~F-14 + 收口 R-09）
> 编写依据：LLD 交付标准（IEEE 1016-2009 设计视图 / GB-T 8567—2006 详细设计 / Amazon LLD 模板 / 中文《详细设计说明书》共识）
> 关联上游：HLD v3.10（§2 / §3.4 / §4.6 / §6.14）× PRD v4.5
> 定位：LLD 序列的**首选模块**（资深架构师排程：风险最高、最中心，内置 PoC 验证门）
> 作者：资深架构师（AI 协作）

---

## 0. 为什么这个模块第一个做

- **最中心**：投递执行是产品的核心价值链路（收集信息 → 半自动投递 → 通知），其余模块（AI 编排、支付、分析）都挂在它之上。
- **风险最高**：反封禁命门（账号安全）、本机进程稳定性、适配器 DOM 漂移，全在这里。
- **与图重绘强相关**：C2 容器图、2-2 时序图、2-3 部署图的核心要素都落在本机 Agent 侧，先定模块设计能反向校对图。
- **PoC 门先行**：最危险的两条假设（反封号有效性、适配器 DOM 稳定性）必须先实测，通过后才进全量开发——不拿用户账号赌设计。

---

## 1. 引言与范围

### 1.1 目的
为"本机 Agent 与投递执行"模块提供可直接编码的详细设计：类职责与签名、关键流程时序（含错误分支）、实体状态机（含转移守卫）、核心算法（含前置/后置/边界）、错误码分类与恢复矩阵、本地数据模型、配置与密钥管理、可追溯性与测试策略。本文件是后续单元测试与实现分工的权威依据。

### 1.2 范围
**属于本模块（In）**
- 本机 Agent 桌面守护进程（supervisor / worker / gui 三层）
- 浏览器实例池（Playwright，≤3）与本地加密 Cookie 加载
- 投递任务拉取、执行、状态回写（含断网补传）
- 速率整形引擎（防检测的核心）
- 验证码人机协同闭环
- 平台适配器框架与 SelectorBundle（配置化、签名、热更）
- 与 10 状态机（HLD §3.4）/ 幂等键（HLD §4.6）的衔接

**不属于本模块（Out）**
- AI 匹配/评分（Python LLM 编排服务，独立模块）
- 服务端业务状态机持久化（Java 业务服务，接口契约已定）
- 通知双通道（Signaling/Notification 子系统，独立模块）
- 支付/商业化（独立模块，R-04 待闭环）

### 1.3 引用文档
- HLD v3.10（§2 架构图与部署 / §3.4 投递状态机 / §4.6 幂等与 MQ / §6.14 机制补强）
- PRD v4.5（§3.4 状态机 / §3.6-§3.7 本机执行侧 / §4.6 幂等 / §6.2 投放策略与频率 / §20.5 密钥 / §31.2 离线同步 / §31.4 本机 Agent 信令）
- HLD 风险登记表 v1（R-03 已拍板、R-09 / R-11 关联）

### 1.4 术语与缩写
- **Agent**：本机桌面守护进程（supervisor+worker+gui），运行在用户 PC。
- **WAL**：SQLite Write-Ahead Logging，崩溃可恢复持久化模式。
- **SelectorBundle**：平台 DOM 选择器外置配置文件（YAML + JSON Schema + Ed25519 签名）。
- **PoC 门**：Proof-of-Concept 验证闸门，未过不进全量开发。
- **fail-closed**：异常时"宁可停、不硬推"的安全哲学。
- **KEK / DEK**：密钥加密密钥 / 数据加密密钥（信封加密）。

---

## 2. 模块分解与类设计

### 2.1 包/组件层次
```
agent.core        Supervisor, Worker, IpcChannel
agent.browser     BrowserPool, BrowserInstance, CookieVault
agent.delivery    DeliveryExecutor, RateShaper
agent.captcha     CaptchaLoop
agent.adapter     AdapterManager, PlatformAdapter, SelectorBundle
agent.persist     LocalStore(SQLite WAL)
agent.security    DeviceVault, KeyDerivation
```

### 2.2 关键类设计（类型化属性 + 方法签名）

**Supervisor（监督父进程，唯一常驻）**
| 属性 | 类型 | 说明 |
|------|------|------|
| `worker_pid` | int | 被监督 worker 进程号 |
| `heartbeat_timeout` | Duration | 心跳节拍 10s；**fail-closed 触发阈值 = 连续丢失 3 拍(>30s) 或 CPU 持续 100%>60s**（对齐 HLD §6.14.1，单次丢拍不触发） |
| `crash_restart_limit` | int | 连续崩溃上限 N，超则 break-glass |
| 方法 | 签名 | 说明 |
| `start()` | `-> None` | 拉起 worker，监听本地 IPC |
| `monitor_heartbeat()` | `-> bool` | 丢失→`enter_break_glass()` |
| `restart_worker()` | `-> None` | 异常退出后重启 |
| `enter_break_glass()` | `-> None` | 挂起新任务、保留现场、报用户 |

**Worker（无 GUI，执行投递/采集）**
| 属性 | 类型 | 说明 |
|------|------|------|
| `task_queue` | Queue[Task] | 待执行任务 |
| `browser_pool` | BrowserPool | 浏览器实例池 |
| `cookie_vault` | CookieVault | 本地加密凭证 |
| 方法 | 签名 | 说明 |
| `run_task(t: Task)` | `-> ExecResult` | 拉起实例→填表→提交→回写 |
| `report_heartbeat()` | `-> None` | 每 10s 上报 supervisor |
| `handle_failure(e)` | `-> RecoveryAction` | 按错误码分类恢复 |

**BrowserPool / BrowserInstance**
| 类 | 属性 | 方法 |
|----|------|------|
| `BrowserPool` | `max_instances:int=3`, `per_platform_count:Map` | `acquire(platform,account)->BrowserInstance`, `release(i)`, `cool_down(platform)`, `reap_orphans()->List[i]` |
| `BrowserInstance` | `state`, `platform`, `account`, `cookie_ref`, `pid:int` | `launch()`, `navigate(url)`, `fill_form(sel,val)`, `detect_captcha()->bool`, `force_kill()` |

> **F-6 孤儿进程回收（崩溃恢复缺口）**：worker 被杀/崩溃时，`BrowserPool.reap_orphans()` 必须级联回收该 worker 持有的全部 Playwright 子进程（`force_kill()` 按 `pid` 树终止），释放实例槽位（`max_instances` 占用）并清理 `per_platform_count`；携未完幂等键的任务标记 `执行中断`，由服务端按 HLD §3.4 孤儿清扫回收，**绝不遗留浏览器进程导致实例池耗尽**（对齐 HLD §6.14.1 supervisor 强制 kill + 孤儿级联回收）。正常释放路径 `release(i)` 不受影响。

**RateShaper（防封号命门）**
| 方法 | 签名 | 说明 |
|------|------|------|
| `acquire(platform)` | `-> Permit \| BLOCKED` | token bucket 匀速放出 |
| `jitter_interval()` | `-> Duration` | 高斯裁剪 μ5.5s σ1.5s，**上限 8s**（对齐 HLD §6.14.3 的 2–8s，F-5 原 12s 超限）；**须叠加贝塞尔轨迹 + 随机滚动拟人动作**，不可仅做固定间隔抖动 |
| `warmup_factor(account_age_days)` | `-> float` | <7d 返回 0.3，否则 1.0；**注**：HLD §6.14.3 为"前 N 份(5–10)降速至 30–50%"份数模型(⚠建议值)，本实现采用时间窗近似，偏离 HLD 份数模型，待 PoC P1 校准（F-4） |
| `backoff(platform, n_fail)` | `-> Duration` | `min(2^n·base, cap)+jitter`，**base=15min, cap=6h**（回声 HLD §6.14.3，F-14） |

**CaptchaLoop**
| 方法 | 签名 | 说明 |
|------|------|------|
| `suspend_task(task)` | `-> None` | 进入 awaiting_user |
| `notify_user(deeplink)` | `-> None` | gui 弹窗+深链 |
| `wait_with_timeout(task, 30min)` | `-> CaptchaOutcome` | 超时→rollback，记异常 |
| `degrade_if_needed(account, 24h)` | `-> None` | ≥3 次→平台降速/暂停 |

**AdapterManager / SelectorBundle**
| 类 | 属性 | 方法 |
|----|------|------|
| `AdapterManager` | `bundles:Map[platform,Bundle]` | `load(signed_yaml)`, `validate_schema()`, `verify_signature(pubkey)`, `hot_update(gray_pct)`, `detect_selector_miss()->bool` |
| `SelectorBundle` | `platform`, `version`, `selectors:Map`, `signature:hex64` | `match(name, dom)->str` |

**LocalStore（SQLite WAL）**
| 方法 | 签名 | 说明 |
|------|------|------|
| `save_task(t)` | `-> None` | upsert |
| `append_event(task_id, type, payload)` | `-> None` | 审计事件 |
| `get_pending_sync()` | `-> List[Event]` | 断网补传队列 |
| `mark_synced(ids)` | `-> None` | 回写确认 |
| `integrity_check()` | `-> bool` | 每 30min 跑 `PRAGMA integrity_check`（对齐 HLD §6.14.1）；失败→`enter_safe_mode()` |
| `snapshot()` | `-> Path` | 每日轻量快照（WAL checkpoint + 拷贝） |
| `enter_safe_mode()` | `-> None` | corruption 时停止写入、仅可读/导出，**绝不静默放行**（F-7，与 HLD §6.14.1 受限安全模式一致） |

**IpcChannel（supervisor↔worker/gui 本地 IPC，HLD §6.14.1）**
| 属性 | 类型 | 说明 |
|------|------|------|
| `transport` | enum | `UDS`(Unix Domain Socket) / `NamedPipe`(Windows)；**不监听网络端口** |
| `frame_fmt` | str | 长度前缀帧：`[4B len][1B ver][1B op][payload]`，接收端按 len 读满防粘包/截断 |
| `auth` | str | 启动期一次性握手：supervisor 派发 ephemeral token，worker/gui 启动时校验签名，防本机其他进程注入 |
| `ver` | int | 协议版本号，握手协商，不匹配拒连 |
| 方法 | 签名 | 说明 |
| `send(msg)` | `-> None` | 序列化 + 帧封装 + 写入 |
| `recv()` | `-> Msg \| None` | 读帧 + 校验 ver/auth + 反序列化 |

> **F-9 IPC 通道规格**：本地 IPC 虽不暴露网络，但仍需防本机其他进程注入——故强制 `auth` 启动握手 + `ver` 版本协商；消息以 `frame_fmt` 长度前缀帧封装。这与 HLD §6.14.1「supervisor↔worker/gui 经 UDS/Named Pipe（不监听网络端口）」一致。

**DeviceVault / KeyDerivation（安全，§6.14.8）**
| 方法 | 签名 | 说明 |
|------|------|------|
| `get_device_master_key()` | `-> Key` | 从 OS 安全区（CNG/TPM / DPAPI / Keychain）取，不可导出 |
| `derive_kek(passphrase_key)` | `-> KEK` | `HKDF-SHA256(master ‖ passphrase_key)` |
| `unlock_with_platform_auth()` | `-> None` | Windows Hello / Touch ID 或 Argon2id 口令 |

### 2.3 设计模式
- **Supervisor/Worker（进程监督）**：崩溃自愈 + break-glass 挂起。
- **Strategy（速率整形）**：per-platform 桶策略可配。
- **Adapter（平台适配）**：SelectorBundle 外置，平台差异即插即用。
- **Factory（浏览器实例）**：按平台/账号建池。
- **Circuit Breaker（fail-closed）**：连续失败→平台挂起，不硬推。

### 2.4 依赖
- 内部：gui（IPC）、LocalStore、DeviceVault。
- 外部：Playwright（浏览器）、OS 安全区 API（CNG/TPM/DPAPI/Keychain）、SQLite、服务端 MQ（§4.6 幂等四元组）。

---

## 3. 交互时序（含错误分支）

> 图形化 SVG 时序图（图 2-2 / 2-4 等）按《图交付标准》另出；下表为权威文本规格，每条均含失败分支。

### 3.1 单投递任务全生命周期
1. supervisor 拉起 worker；worker 从 LocalStore/服务端拉取 `pending_confirm` 任务。
2. **成功路径**：`pending_confirm→autofilling`（worker 解密 Cookie→acquire 实例→navigate→fill_form→submit）。
3. **失败分支 A（Cookie 解密失败 AGENT-2001）**：re-prompt 解锁，明文不落日志；仍失败→任务挂起报用户。
4. **失败分支 B（SelectorMiss AGENT-3001）**：AdapterManager 检测→该平台适配器 `pending_fix`，触发 R-09 失效检测。
5. **失败分支 C（平台限流 AGENT-3002）**：RateShaper 退避冷却，不阻塞其他平台。
6. submit 成功→`submitted`→状态事件经 LocalStore 回写服务端；断网→缓存 `get_pending_sync()`，恢复后 `mark_synced()`。

### 3.2 验证码人机协同
1. `detect_captcha()==true`→CaptchaLoop.suspend_task→投递单**回退至 `pending_confirm`**（需用户本机过码后重投；对齐 HLD §3.4，`captcha` 不等同 `contacting`——`contacting` 为 HR 主动沟通态，见 ADR-008）。
2. notify_user(deeplink)→gui 弹窗，用户本机手动过码。
3. **超时分支（30min，AGENT-4001）**：wait_with_timeout→任务 rollback，计入异常。
4. **降级分支（24h≥3 次）**：degrade_if_needed→该平台降速/暂停。

### 3.3 适配器失效检测与降级
detect_selector_miss→标记 pending_fix→AdapterManager 拉取修订 Bundle（灰度）→验签→热更；命中率连续 2 周 <95%→R-09 升级为阻断。

> **R-09 收口（失效检测 SLA + 单平台降级路径）**：
> - **失效检测 SLA**：`detect_selector_miss()` 须在页面解析后 **≤60s** 内判定选择器缺失并标 `pending_fix`；该平台立即进入**单平台降级**（暂停新投递、保留在途任务回写），**不影响其他平台**（非全局停摆）。
> - **单平台降级状态机**：见 §4.4 `active → pending_fix → fixed | retired`；`pending_fix` 期间仅该平台 `suspend(p)`，其余平台正常 `acquire`。
> - **升级阻断**：命中率 <95% 连续 2 周，或单平台降级超 **24h** 未修复，升级为 R-09 阻断并告警，触发人工介入（呼应 §10 P2 与 HLD §6.14.5 SelectorBundle 热更）。

### 3.4 凭证加解密加载
Worker 调 DeviceVault.unlock_with_platform_auth→get_device_master_key→derive_kek→CookieVault.decrypt(kek)→明文仅驻 worker 内存，不落盘不进日志。

### 3.5 断网补传 / 离线队列消费
1. 投递执行中若 LocalStore→服务端回写失败（网络中断），任务状态事件进入 `get_pending_sync()` 队列，**不阻塞本地执行**。
2. 网络恢复→`mark_synced(ids)` 批量回写；失败事件按指数退避重试（≤N 次），超限→挂起报用户。
3. **失败分支（离线超长 / 服务端拒收）**：事件滞留本地，`gui` 提示"待同步 N 条"，**不静默丢弃**；服务端按幂等四元组去重，重复回写安全（呼应 §3.1 步骤 6 与 §2.2 `get_pending_sync`）。
> 本时序补齐原 §14「≥5 时序」自检的真实覆盖（F-10）：§3.1–§3.5 共 5 条关键流程时序。

---

## 4. 状态机模型（含转移守卫）

### 4.1 投递单 10 状态机（HLD §3.4，本模块本地可执行部分）
`pending_confirm → autofilling → submitted` 由 worker 推进；服务端最终裁决 `submitted→viewed→contacting→interview_invited→interview_done→offer→(rejected|closed)`。
**守卫**：`autofilling→submitted` 仅当 `detect_captcha()==false` 且 `submit()` 返回 2xx；否则**回退 `pending_confirm`**（验证码需人工过码后重投）或挂起（`risk_blocked`）。**注意**：`captcha` 不得映射 `contacting`（该态为 HR 主动沟通，见 HLD §3.4 / ADR-008）。

### 4.2 浏览器实例状态机
`idle → busy → (cooling → idle) | (banned → retired)`。
**守卫**：`busy→banned` 当平台返回风控/封禁信号；`cooling→idle` 当冷却计时到期且未被 banned。

### 4.3 验证码协同子状态机
`pending → awaiting_user → resolved → (回 pending_confirm 重投) | timeout(30min) → task_rollback | degraded(≥3/24h) → platform_pause`。

### 4.4 适配器/SelectorBundle 状态机
`active → pending_fix(selector_miss) → fixed(hot_update) | retired(平台废弃)`。
**守卫**：`pending_fix→fixed` 需新 Bundle `verify_signature()` 通过且灰度回放命中率 ≥95%。

---

## 5. 算法规格（伪代码 + 前置/后置/边界 + 复杂度）

### 5.1 速率整形 acquire（防封号核心）
```
pre:  platform ∈ 已注册; account 不在 cool-down
post: 返回 Permit 或 BLOCKED; 不耗尽桶
edge:  桶空→BLOCKED(不硬推); worker 飞行中崩溃→心跳丢失释放 permit
for each platform p:
  capacity[p]   = daily_limit(tier)            // 专业版 80–100 / 免费版 30 (§6.2)
  interval      = clip(gaussian(μ=5.5s, σ=1.5s), 2s, 8s)   # 上限对齐 HLD §6.14.3 的 2–8s（原 12s 超限）；并叠加贝塞尔轨迹 + 随机滚动拟人动作（见 F-5 修复）
  warmup        = if account_age_days < 7: 0.3 else 1.0   # 注：HLD §6.14.3 为"前 N 份(5–10)降速至 30–50%"的份数模型(⚠建议值)；本实现采用 account_age_days 时间窗近似，机制不同、偏离 HLD 份数模型，待 PoC P1 校准对齐（F-4）
  effective     = capacity[p] * warmup / active_window
  on failure:   backoff = min(2^n * base, cap) + jitter; n += 1   # base=15min, cap=6h（回声 HLD §6.14.3，避免实现时拍脑袋，F-14）
  on n_fail≥THRESHOLD: fail-closed → suspend(p)
complexity: O(1) per acquire
```

### 5.2 设备密钥派生与 Cookie 解密（落地 §6.14.8）
```
pre:  OS 安全区可用 或 已配置 DPAPI/Keychain 回退
post: 返回 worker 内存中的明文 Cookie（不落盘）
edge:  OS 安全区不可用→AGENT-2002 回退并告警; 口令错→重提示, 不入日志
master   = DeviceVault.get_device_master_key()        // CNG/TPM 或 Keychain, 不可导出
pass_k   = platform_auth() || argon2id(passphrase, m=64MB, t=3, p=1, salt=128bit)
kek      = HKDF-SHA256(master ‖ pass_k)
cookie   = AES-256-GCM.decrypt(kek, ciphertext)
```

### 5.3 选择器命中率回放校验
```
pre:  已录制平台 DOM 快照 fixture ≥5 页面
post: 返回命中率
edge:  fixture 缺失→跳过该平台; 命中率<95%连续2周→R-09 升级阻断
hit_rate = matched_selectors / total_selectors
```

### 5.4 多设备同账号调度冲突消解（闭合 HLD §27.1 / §30.4）
```
pre:  同账号检测到 ≥2 个 Agent 实例（device_id 不同 或 同机多开）
post: 全局仅 1 个"主投递者"执行自动投递；其余实例 standby（仅手动/查看）
edge:  后端不可达→本地选举；主失联>90s→重选举；恢复后端→按四元组幂等去重收敛

# 选举（离线多设备锁，HLD §30.4）
candidates = 本机可见的同账号实例(device_id, boot_ts)
primary    = min(candidates, by (device_id, boot_ts))   # 字典序最小者为主
renew      = 每 30s 主发 heartbeat{device_id, boot_ts, lease=90s}
on 非主:  standby(); 仅允许手动投递/查看；自动投递信令本地拒绝(不抢主)
on 主失联(>90s 无 heartbeat): 触发重选举(本地重新算 min)；原主恢复后若已非主则降级 standby

# 收敛（恢复后端）
on 后端可达: 所有实例上报在途任务 idempotency_key；服务端按 (user_id,platform,job_id,apply_date) 去重
             已投记录不重投；在途任务由当前主接管(仅未开始/可恢复态)

# 在途不抢占
executing_task 绑定 owner_device_id；主切换时 standby 仅接管 owner==null 或 owner==本机 的待执行任务
执行中任务由原 owner 完成或超时(heartbeat 释放 permit, §5.1)后释放

complexity: O(n) per election, n=实例数(通常≤3)
```
> 注：本机 Agent 不持有"全局锁"服务端组件；离线场景靠本地选举 + 后端恢复后的四元组幂等去重收敛（§8.2 UNIQUE 约束），确保"极少双投、绝不多扣"。

---

## 6. 错误处理设计

### 6.1 错误分类
- 浏览器层（启动/导航/检测）、加密层（解密/密钥）、适配器层（选择器/失效）、验证码层（超时/降级）、持久化层（WAL 损坏）、监督层（心跳丢失）。

### 6.2 错误码表
| 错误码 | 类型 | 检测 | 恢复策略 |
|--------|------|------|----------|
| AGENT-1001 | BrowserLaunchFailed | launch() 抛异常 | 退避重试；N 次→break-glass |
| AGENT-2001 | CookieDecryptFailed | decrypt() 失败 | 重提示解锁；不记明文日志 |
| AGENT-2002 | KeychainUnavailable | OS 安全区不可达 | 回退 DPAPI/Keychain 并告警 |
| AGENT-3001 | SelectorMiss | detect_selector_miss() | 挂起适配器，触发 R-09 |
| AGENT-3002 | PlatformRateLimited | 平台返回限流 | 退避+冷却，不阻塞他平台 |
| AGENT-4001 | CaptchaTimeout | 30min 未过码 | 任务 rollback，计异常 |
| AGENT-5001 | WorkerHeartbeatLost | 连续丢失 3 次心跳(>30s) 或 CPU 持续 100%>60s | supervisor fail-closed（对齐 HLD §6.14.1，单次丢拍不触发） |
| AGENT-5002 | SQLiteCorrupt | `integrity_check()` 失败 / WAL 校验失败 | `enter_safe_mode()`（停止写入、仅可读/导出，绝不静默放行）+ 从最近 `snapshot()` 恢复（F-7，对齐 HLD §6.14.1 受限安全模式） |

### 6.3 异常层次
`AgentException` → `BrowserException` / `CryptoException` / `AdapterException` / `CaptchaException` / `PersistenceException` / `SupervisionException`。

### 6.4 恢复矩阵
- **retry+backoff**：1001 / 3002。
- **re-prompt**：2001。
- **fallback**：2002。
- **fail-closed（挂起）**：3001 / 5001（5001 须 >30s 或 CPU100%>60s，单次丢拍不触发，对齐 HLD §6.14.1）。
- **rollback**：4001。
- **受限安全模式（corruption 不静默放行）**：5002（`enter_safe_mode()` 停写、可导出、从 `snapshot()` 恢复，F-7）。
- **break-glass（报用户）**：1001 超限。

---

## 7. 数据验证规则

### 7.1 输入校验
- **SelectorBundle（JSON Schema）**：`platform`(enum)、`version`(semver)、`selectors`(非空字符串映射)、`signature`(64-hex Ed25519)；加载前必须 `verify_signature()` 通过。
- **任务参数**：`user_id`(非空)、`platform`(enum)、`job_id`(非空)、`apply_date`(YYYY-MM-DD)、`account_id`(非空)、`job_url`(https URL)、`resume_version_id`(引用存在)；幂等由四元组 `(user_id, platform, job_id, apply_date)` 唯一约束保证，**禁止以单 UUID 替代**（ADR-006 / HLD §6.13.2）。
- **配置**：`rate_limit`(int>0)、`timeout`(1..3600s)。

### 7.2 跨字段校验
- `warmup_factor` 仅在 `account_age_days` 存在时生效。
- `platform_pause` 须先有 ≥3 次 `CaptchaTimeout` 在 24h 窗口内。

---

## 8. 数据模型与持久化（SQLite WAL）

### 8.1 本地表（仅本机、可重建优先）
`task` / `task_event` / `browser_instance` / `captcha_session` / `selector_bundle` / `device_vault`(仅存 kdf 参数与 OS 安全区引用，主密钥不入 SQLite)。

### 8.2 表定义（DDL）
```sql
CREATE TABLE task (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  job_id TEXT NOT NULL,
  apply_date TEXT NOT NULL,          -- YYYY-MM-DD，与 user_id/platform/job_id 构成幂等四元组
  account_id TEXT NOT NULL,
  job_url TEXT NOT NULL,
  state TEXT NOT NULL,
  resume_version_id TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  UNIQUE (user_id, platform, job_id, apply_date)   -- ADR-006 幂等四元组，禁止全局 UUID 替代
);
CREATE INDEX idx_task_account_state ON task(account_id, state);
CREATE INDEX idx_task_idem ON task(user_id, platform, job_id, apply_date);

CREATE TABLE task_event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT,
  ts INTEGER NOT NULL
);
CREATE INDEX idx_event_task ON task_event(task_id, ts);

CREATE TABLE browser_instance (
  id TEXT PRIMARY KEY,
  platform TEXT NOT NULL,
  account_id TEXT NOT NULL,
  state TEXT NOT NULL,
  last_used_at INTEGER
);
CREATE INDEX idx_bi_platform_acct ON browser_instance(platform, account_id);

CREATE TABLE captcha_session (
  id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  state TEXT NOT NULL,
  started_at INTEGER NOT NULL,
  resolved_at INTEGER
);

CREATE TABLE selector_bundle (
  platform TEXT NOT NULL,
  version TEXT NOT NULL,
  bundle_yaml TEXT NOT NULL,
  signature TEXT NOT NULL,
  gray_pct INTEGER DEFAULT 0,
  active INTEGER DEFAULT 1,
  PRIMARY KEY (platform, version)
);

CREATE TABLE device_vault (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  kdf_params TEXT NOT NULL,        -- argon2id 参数 json
  secure_ref TEXT NOT NULL         -- OS 安全区句柄引用, 主密钥不落 SQLite
);
```

### 8.3 索引与迁移
- 索引以 `user_id`/`account_id` 首列组织，便于本机按账号检索；**注**：HLD §6.15 的分片预留针对**服务端 `application`/`application_task` 等高增表**，本机 SQLite 为单用户本地库，**不适用分片**，故此处仅为本地检索便利，非分片约束（F-8，删除原"呼应 §6.15 分片预留"的误导表述）。
- 迁移：本地表仅本机，版本号自管，向前兼容追加列。

### 8.4 本地存储治理（闭合 HLD §25.5）
单用户长期运行，本地 SQLite + 配套文件会膨胀，须主动治理，避免"存储膨胀→性能下降→崩溃"。

- **膨胀来源**：`task_event` 审计流水、历史 `captcha_session`、`selector_bundle` 旧版本、浏览器临时快照、本地日志。
- **软配额**：单库 ≤ 200MB（可配，默认 200）；配套文件（快照/日志）≤ 500MB（可配）。
- **膨胀监控**：启动 + 每 30min 测 SQLite 文件大小与配套目录；≥80% 软限触发主动清理；≥100% 暂停非紧急采集（不阻塞在途任务）。
- **清理策略**（按保留期滚动，**绝不删在途/未终态记录**——"不确定就停"，对齐 HLD §29.6）：
  - `task_event`：保留期默认 90 天，超期批量删（保留最近一条状态快照便于审计）；
  - `captcha_session`：完成/超时即删；
  - `selector_bundle`：仅留 `active=1` 当前版本，灰度历史版本超 30 天删；
  - 浏览器临时快照：任务结束即清（F-7 的 `snapshot()` 为恢复点，非长期快照）；
  - 本地日志：按 §29.4 append-only + 滚动（单文件 ≤ 20MB，保留 ≤ 7 份）。
- **关联**：清理不触达 `task` 终态记录（投递历史服务端持有，可恢复）；清理前先 `PRAGMA integrity_check`，损坏即停清理并告警，进 AGENT-5002 受限安全模式（§6.2），绝不静默放行。

---

## 9. 配置与环境

### 9.1 配置项
`rate_limits`(per-tier)、`heartbeat_timeout=10s`、`max_browser_instances=3`、`captcha_timeout=30min`、`argon2id_params(m=64MB,t=3,p=1)`。

### 9.2 Feature flags
`strict_unlock`（强制平台认证器/口令，默认开）、`adapter_gray_pct`（热更灰度比例）。

### 9.3 密钥管理
主密钥存 OS 安全区（CNG/TPM / DPAPI / Keychain），worker 运行时经 `unlock_with_platform_auth()` 取；明文 Cookie 仅驻内存。

---

## 10. PoC 验证门（必须 pass 才进全量开发）

> 本模块也是整个产品的**最高杠杆闸门**。两条假设不验证，全量开发就是在赌用户账号安全。

| 实验 | 假设 | 方法 | Pass 判据 | 失败处置 |
|------|------|------|-----------|----------|
| **P1 反封号有效性** | 速率整形 + 行为模拟 + ≤3 实例能在主流平台长期不被风控 | 单测试账号，按 §5.1 实跑 14 天，日投放≤额度，监控账号状态/验证码率/限流率 | 14 天内无封号、验证码率 <20%（**<20% 为 LLD 提议值，HLD/PRD 未规定，需 stakeholder 签字确认，F-13**）、无异常限流 | 调参后复测；仍不过则回到设计层重审反封禁模型 |
| **P2 适配器 DOM 稳定性** | SelectorBundle 在平台改版周期内可稳定解析 | 录制 3 平台 5 关键页面 DOM 快照建回放 fixture；每周回放校验命中率 | 选择器命中率 ≥95%（连续 2 周） | 触发 Bundle 修订+灰度；持续低则升级 R-09 为阻断 |

**Gate 出口**：P1 + P2 均 pass，且 R-09（适配器失效 SLA + 单平台降级）已在本模块收口，方可启动全量编码。任一不过 → 回到设计/参数层，不进全量。

---

## 11. 可追溯性矩阵（LLD → HLD → PRD → 测试）

| LLD 模块 | HLD 锚点 | PRD 需求 | 关联测试用例 |
|----------|----------|----------|--------------|
| Supervisor/Worker | §6.14.1 | §3.6 / §3.7 本机执行侧 | TC-SUP-01 |
| BrowserPool/RateShaper | §6.14.3 | §6.2 投放频率/上限、§3.7 | TC-RATE-01 |
| CookieVault/KeyDerivation | §6.14.2 / §6.14.8 | §20.5 密钥 | TC-CRYPTO-01 |
| CaptchaLoop | §6.14.4 | §4.5 / §3.7 | TC-CAPT-01 |
| AdapterManager/SelectorBundle | §6.14.5 | §494 模块 4：平台适配器系统 / §496 适配器接口契约（原 §15.x 为虚构锚点，已更正，F-11） | TC-ADAPT-01 |
| task/task_event 持久化 | §4.6 / §6.14.7 | §4.6 幂等、§31.2 同步 | TC-IDEM-01 |
| 状态机衔接 | §3.4 | §3.4 状态机 | TC-STATE-01 |

> 防漂移建议：可扩展 `check_prd_hld_traceability.py` 增加 LLD→HLD 行，把本矩阵转为 CI 自动校验（与 HLD↔PRD 双闸门对齐）。
>
> **F-12 关联测试用例状态**：上表「关联测试用例」列的 `TC-SUP-01` / `TC-RATE-01` / `TC-CRYPTO-01` / `TC-CAPT-01` / `TC-ADAPT-01` / `TC-IDEM-01` / `TC-STATE-01` 均为**占位 ID，对应测试用例文档尚待撰写**；可追溯性在「LLD→HLD→PRD 映射」层成立，但「→ 测试」链路未闭环，不暗示测试已完成。

---

## 12. 测试策略

- **单元**：RateShaper 桶空 BLOCKED/暖up 因子/退避封顶；KeyDerivation 往返；SelectorBundle 验签；状态机转移守卫。
- **集成**：单任务全生命周期（mock 平台 HTTP）、断网补传、验证码超时回滚。
- **E2E / PoC**：P1 反封号 14 天实跑、P2 选择器命中率回放（平台 Mock 录制 fixture）。
- **性能**：≤3 实例并发下 CPU/内存预算（§6.7）；心跳单拍 10s 上报，**fail-closed 阈值 >30s（3 拍）**，非单次丢拍即挂起（对齐 HLD §6.14.1）。

---

## 13. 开放项 / 关联风险

- **R-09（高，12）**：平台改版/风控升级致适配器失效——**已收口**：§3.3 补「失效检测 SLA（≤60s 判定 + 单平台降级非全局停摆）+ 单平台降级状态机 + 24h 升级阻断」，§4.4 单平台降级路径已落地；残余仅"HLD/PRD 未规定 SLA 数值"由本模块拍板（待 stakeholder 确认）。详见 §10 Gate 出口判据。
- **R-11（中，9）**：本机 Agent 进程崩溃/资源耗尽——§2.2 监督模型已覆盖自愈，细节在类图阶段定。
- **R-03（已拍板 v3.9）**：Cookie 设备密钥派生——§5.2 / §9.3 按 §6.14.8 落地。

---

## 14. LLD 交付自检清单（对照标准）

- [x] 每个 HLD 组件分解到 ≥1 LLD 模块并带类型化类表（§2.2）
- [x] 类表用类型化属性 + 参数化方法签名（§2.2）
- [x] ≥5 时序覆盖关键流程（happy+error 分支，§3.1–§3.5；§3.5 断网补传为 F-10 补的第 5 条）
- [x] 状态机含终态 + 转移守卫（§4.1–§4.4）
- [x] 算法含前置/后置/边界守卫 + 复杂度（§5.1–§5.4，§5.4 多设备调度冲突消解）
- [x] 错误码分类 + 异常层次 + 恢复矩阵（§6.2–§6.4）
- [x] 数据验证规则（类型/格式/范围/跨字段，§7）
- [x] 表 DDL + 索引（§8.2）
- [x] 可追溯性矩阵 LLD→HLD→PRD（§11）
- [x] 与 PoC 验证门衔接（§10）
- [ ] 图形化 SVG 类图/时序图（按《图交付标准》另出，文本规格已在 §2–§4 落地，不阻塞实现）

---

> 本文件为交付级 LLD v1.3（v1.1 修复 F-1/F-2/F-3：幂等四元组、心跳 fail-closed 阈值、验证码状态映射；v1.2 修复评审 F-4~F-14 + 收口 R-09；**v1.3 补 §5.4 多设备同账号调度冲突消解（闭合 HLD §27.1 / §30.4 离线多设备锁）+ §8.4 本地存储治理（闭合 HLD §25.5：膨胀监控/软配额/保留期清理/不确定就停）**，§14 自检同步）。下一步：先跑 §10 PoC 双实验。
