# LLD：数据库设计（ER + 表结构 + 索引）

> 上游：HLD §5.1（核心实体 ER 图 5-1，14 实体）/ §5.2（核心表与关键字段概要）/ §5.3（数据一致性规则）/ §6.15（分片键预留与冷热分离）/ §6.16 G7-1/2/3（面试域实体补全）/ §1426（统一审计日志字段）。
> 机器可读契约：`design/contracts/`（interview-* / crawler-result / b01–b11 等，schema 30 / 注册表 6 已校验闭环）。
> 关联模块：[LLD-本机Agent与投递执行-模块设计.md](./LLD-本机Agent与投递执行-模块设计.md) §8（本机 SQLite 权威 DDL）；[LLD-面试模拟域-模块设计.md](./LLD-面试模拟域-模块设计.md)（interview-* schema 字段来源）；[LLD-密钥与凭证工程-模块设计.md](./LLD-密钥与凭证工程-模块设计.md)（KEK/DEK 版本化，不直接落业务库）。
> 本文档闭合 HLD §10「数据库设计（ER + 表结构 + 索引）」由「下一步」翻为「已闭环」。

---

## 1. 范围与双存储架构

本系统数据**分两处存储**，职责与合规边界严格分离（落实 HLD §2.6 ④ / ADR-002 / §C.5）：

| 存储 | 引擎 | 归属 | 承载 | 是否上云 |
|------|------|------|------|----------|
| **Store A 服务端 MySQL 8.0** | InnoDB，utf8mb4_0900_ai_ci，主从 + 只读副本 | 后端 Java 直连（Python 经 REST `/internal/*` 或 MQ） | 全部多用户业务数据 | 是（云） |
| **Store B 本机 SQLite（WAL）** | SQLite，单文件，原子事务 | 用户本机 Agent 进程 | 任务队列 / 去重 key / 配置缓存 / Cookie 金库引用 | **否**，仅本机 |

**关键合规边界（§C.5 / ADR-018）**：
- 平台账号 **Cookie 密文只存在于 Store B**（经 OS 安全区 `device_vault` + 信封加密，明文永不出本机、永不进日志）；服务端 `platform_account` **仅存账号元信息与登录态**（ok / need_login / disabled），绝无 Cookie 列。
- 简历原文走 OSS 外链（`raw_file_ref`），库内只存解析后结构化 `snapshot`（AES-256-GCM 加密，§6.14.2）；密钥与业务库分离、定期轮换。

> 说明：HLD §5.1 图 5-1（fig-5-1-er.svg，14 实体 4 域）已是**概念级 ER 图**；本文件在其之上产出**逻辑/物理级 DDL + 索引**，二者互补，不重画 SVG。

---

## 2. ER 模型（文字图信息说明书）

### 2.1 实体与关系总览

四域（沿用 §5.1）：**用户域 / 平台域 / 投递域枢纽 / 面试域**。主链路 ①→②→③→⑨→⑩→⑪→⑫→⑭ 绿色加粗。

| 实体（表名） | 域 | 主键 | 主要外键 / 唯一约束 | 关系（基数） |
| --- | --- | --- | --- | --- |
| `user` | 用户 | id | uk(email), uk(phone) | 1:N 拥有 resume / platform_account / application / interview_session / strategy_config / member_order |
| `resume` | 用户 | id | idx(user_id) | 1:N resume_version；1:1 preferred_version |
| `resume_version` | 用户 | (user_id, id) | uk(resume_id, version_no) | N:1 resume；被 application.resume_version_id 引用 |
| `platform_account` | 用户/平台 | id | uk(user_id, platform_id) | N:1 user；提供投递身份（登录态） |
| `member_order` | 用户 | id | uk(order_no) | N:1 user；权益判定 |
| `strategy_config` | 用户 | id | uk(user_id) | 1:1 user；投递策略快照 |
| `job` | 平台 | id | uk(platform_id, external_id) | 被 application 引用（投递对象） |
| `adapter_registry` | 平台 | (platform_id, version) | — | 执行投递动作（代码包元信息） |
| `application` | 投递枢纽 | (user_id, id) | uk(idempotency_key), uk(user_id,platform_id,job_id,apply_date) | N:1 user / job / platform_account；1:1 application_task；1:N application_event；触发 interview_question_set |
| `application_task` | 投递枢纽 | (user_id, task_id) | uk(idempotency_key) | 1:1 application（执行单元） |
| `application_event` | 投递枢纽 | (user_id, id) | idx(application_id) | N:1 application（状态流水） |
| `interview_question_set` | 面试 | (user_id, id) | idx(application_id) | N:1 application（可选）；1:N interview_session / interview_question |
| `interview_session` | 面试 | (user_id, id) | idx(question_set_id) | N:1 question_set；可选 N:1 application；1:1 interview_evaluation；1:N interview_session_event / interview_question / interview_answer |
| `interview_question` | 面试 | id | idx(session_id) | N:1 session / question_set |
| `interview_answer` | 面试 | id | idx(session_id, turn) | N:1 session / question |
| `interview_evaluation` | 面试 | session_id | — | 1:1 session（报告） |
| `interview_session_event` | 面试 | (user_id, id) | idx(session_id) | N:1 session（审计） |
| `daily_report` | 运营 | (user_id, report_date) | — | N:1 user；每日一条 |
| `audit_log` | 合规 | id | idx(object_type,object_id) | 跨实体统一审计 |
| `notification`（草案） | 通知 | id | idx(user_id, read_flag) | N:1 user（待通知模块 LLD 收口） |

### 2.2 关系语义要点

- **投递幂等**：`application.idempotency_key` 与 `application_task.idempotency_key` 双唯一键 + Redis SETNX 前置（§5.3）。四元组 `(user_id, platform_id, job_id, apply_date)` 唯一约束，杜绝重复投递。
- **状态机一致性**：`application` 状态变更与 `application_event` 写入在**同一事务**内；Redis 分布式锁防并发推进（ADR-008）。投递 10 态无回退边（§3.4）。
- **面试会话溯源**：`interview_session` 每态变更写 `interview_session_event`（类比 `application_event`），供重跑 / 申诉（G7-1）。
- **分片预留**：高增 / 用户维度表 `application` / `application_task` / `application_event` / `daily_report` / `resume_version` / `interview_question_set` / `interview_session` 主键或首列分区键**必含 `user_id`**（§6.15），后期按 `user_id` 哈希分片零迁移。
- **冷热分离**：`application_event` / `daily_report` / `interview_session_event` / `audit_log` 时序表按月分区，>24 月匿名化转冷层（§6.15 / §8.2）。

---

## 3. Store A：服务端 MySQL 8.0 表结构（DDL）

### 3.0 全局约定

```sql
-- 引擎/字符集：InnoDB / utf8mb4_0900_ai_ci
-- 时间戳：业务行用 DATETIME(3)；事件/审计流水同 contracts 的 integer epoch(ms) 等价，落库转 DATETIME(3)
-- 分片预留：用户维度高增表 PK 首列含 user_id；AUTO_INCREMENT 列须为某索引首列，故对 (user_id,id) 表额外建 UNIQUE(id)
-- 大字段隔离：简历原文走 OSS 外链，JSON 仅存结构化快照/配置（ADR-003）
```

### 3.1 用户域

```sql
CREATE TABLE user (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email         VARCHAR(255) NOT NULL,
  phone         VARCHAR(32),
  password_hash VARCHAR(255) NOT NULL COMMENT 'BCrypt strength>=10 (ADR-018)',
  plan          ENUM('free','pro','enterprise') NOT NULL DEFAULT 'free',
  status        ENUM('active','disabled','deleted') NOT NULL DEFAULT 'active',
  created_at    DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at    DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_email (email),
  UNIQUE KEY uk_phone (phone)
) COMMENT='系统根实体：谁在投递';

CREATE TABLE platform_account (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id       BIGINT UNSIGNED NOT NULL,
  platform_id   VARCHAR(32) NOT NULL COMMENT 'boss/liepin/zhaopin/51job/lagou...',
  account_label VARCHAR(64) DEFAULT '' COMMENT '多账号标签',
  login_state   ENUM('ok','need_login','disabled') NOT NULL DEFAULT 'need_login',
  last_login_at DATETIME(3),
  created_at    DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at    DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_platform (user_id, platform_id),
  KEY idx_user (user_id)
) COMMENT='仅存账号元信息与登录态；Cookie 密文仅本机 Agent 本地，不上云(§C.5)';

CREATE TABLE resume (
  id                   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id              BIGINT UNSIGNED NOT NULL,
  title                VARCHAR(255) NOT NULL,
  preferred_version_id BIGINT UNSIGNED COMMENT '默认投递版本',
  created_at           DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at           DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_user (user_id)
) COMMENT='简历头部；一份简历多个版本(§6.13.5.2)';

CREATE TABLE resume_version (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  resume_id       BIGINT UNSIGNED NOT NULL,
  user_id         BIGINT UNSIGNED NOT NULL COMMENT '分片预留首列',
  version_no      INT UNSIGNED NOT NULL,
  snapshot        JSON NOT NULL COMMENT '解析后结构化简历(JSON)',
  raw_file_ref    VARCHAR(512) COMMENT 'OSS 外链，原文不落库(ADR-003)',
  is_encrypted    TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'AES-256-GCM(§6.14.2)',
  created_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (user_id, id),
  UNIQUE KEY uk_id (id),
  UNIQUE KEY uk_resume_ver (resume_id, version_no),
  KEY idx_resume (resume_id)
) COMMENT='简历版本快照；投递锁定当时版本';

CREATE TABLE member_order (
  id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_no  VARCHAR(64) NOT NULL,
  user_id   BIGINT UNSIGNED NOT NULL,
  plan      ENUM('pro','enterprise') NOT NULL,
  status    ENUM('pending','paid','refunded','closed') NOT NULL DEFAULT 'pending',
  amount    DECIMAL(10,2) NOT NULL,
  paid_at   DATETIME(3),
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_order_no (order_no),
  KEY idx_user (user_id)
) COMMENT='会员订单(支付对账 PRD §12)';

CREATE TABLE strategy_config (
  id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id           BIGINT UNSIGNED NOT NULL,
  daily_limit       INT UNSIGNED NOT NULL DEFAULT 30 COMMENT '免费30/角色100(§6.13.5.4)',
  match_threshold   DECIMAL(3,2) NOT NULL DEFAULT 0.60 COMMENT '匹配阈值',
  time_windows      JSON COMMENT '时段窗口',
  enabled_platforms JSON COMMENT '启用平台列表',
  created_at        DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at        DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_user (user_id)
) COMMENT='投递策略快照';
```

### 3.2 平台域

```sql
CREATE TABLE job (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  platform_id  VARCHAR(32) NOT NULL,
  external_id  VARCHAR(128) NOT NULL COMMENT '平台岗位原始 id',
  title        VARCHAR(300) NOT NULL,
  company      VARCHAR(200) NOT NULL,
  url          VARCHAR(1024),
  salary_min   INT UNSIGNED,
  salary_max   INT UNSIGNED,
  location     VARCHAR(128),
  description  MEDIUMTEXT,
  requirements JSON,
  source       ENUM('search','detail') NOT NULL DEFAULT 'search',
  jd_raw       JSON COMMENT '匹配用 JD 原文',
  collected_at BIGINT NOT NULL COMMENT 'epoch ms（契约对齐）',
  created_at   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  UNIQUE KEY uk_platform_ext (platform_id, external_id)
) COMMENT='适配器采集去重(§4.5 B10/B11；crawler-result schema)';

CREATE TABLE adapter_registry (
  platform_id VARCHAR(32) NOT NULL,
  version     VARCHAR(32) NOT NULL,
  status      ENUM('active','deprecated','disabled') NOT NULL DEFAULT 'active',
  checksum    VARCHAR(128),
  signature   VARCHAR(256) COMMENT 'Ed25519(§6.14.5)',
  created_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (platform_id, version)
) COMMENT='平台适配器元数据(§3.4/§6.13.3)';
```

### 3.3 投递域枢纽（10 状态机）

```sql
CREATE TABLE application (
  user_id           BIGINT UNSIGNED NOT NULL,
  id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  job_id            BIGINT UNSIGNED NOT NULL,
  platform_id       VARCHAR(32) NOT NULL,
  resume_version_id BIGINT UNSIGNED COMMENT '投递锁定版本',
  status            ENUM('pending_confirm','autofilling','submitted','viewed',
                         'contacting','interview_invited','interview_done','offer',
                         'rejected','closed') NOT NULL DEFAULT 'pending_confirm',
  idempotency_key   VARCHAR(64) NOT NULL COMMENT '全局幂等键(§6.13.2)',
  apply_date        DATE NOT NULL COMMENT 'YYYY-MM-DD，幂等四元组',
  platform_apply_id VARCHAR(128) COMMENT '平台侧投递 id',
  created_at        DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at        DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (user_id, id),
  UNIQUE KEY uk_id (id),
  UNIQUE KEY uk_idem (idempotency_key),
  UNIQUE KEY uk_quad (user_id, platform_id, job_id, apply_date),
  KEY idx_user_status (user_id, status),
  KEY idx_job (job_id)
) COMMENT='投递单枢纽(§3.4 ADR-008 10态无回退边)';

CREATE TABLE application_task (
  user_id         BIGINT UNSIGNED NOT NULL,
  task_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  application_id  BIGINT UNSIGNED NOT NULL,
  idempotency_key VARCHAR(64) NOT NULL COMMENT '与 application 双唯一',
  state           VARCHAR(32) NOT NULL COMMENT '执行态(本机 Agent 回写)',
  created_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (user_id, task_id),
  UNIQUE KEY uk_tid (task_id),
  UNIQUE KEY uk_tidem (idempotency_key),
  KEY idx_app (application_id)
) COMMENT='幂等执行单元，1:1 application';

-- ⚠ 分区落地约束：application_event 为写入极高时序表，按月分区（§6.15）。
-- MySQL 要求分区列 created_at 出现在所有唯一索引中；故以下 PK 含 (user_id, created_at, id)，
-- 且 AUTO_INCREMENT 列 id 作为某索引首列（uk_id）。编码期建表脚本落实此约束，避免运行期报错。
CREATE TABLE application_event (
  user_id      BIGINT UNSIGNED NOT NULL,
  created_at   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  application_id BIGINT UNSIGNED NOT NULL,
  from_state   VARCHAR(32),
  to_state     VARCHAR(32),
  reason       VARCHAR(255),
  actor        VARCHAR(32) DEFAULT 'system',
  PRIMARY KEY (user_id, created_at, id),
  UNIQUE KEY uk_id (id),
  KEY idx_app (application_id),
  KEY idx_user_created (user_id, created_at)
) ENGINE=InnoDB
  PARTITION BY RANGE (TO_DAYS(created_at)) (
    PARTITION p2026_08 VALUES LESS THAN (TO_DAYS('2026-09-01')),
    PARTITION pmax VALUES LESS THAN MAXVALUE
  )
  COMMENT='投递事件流水(审计/幂等)；按月分区(§6.15)';
```

### 3.4 面试域（G7-1/2/3）

```sql
CREATE TABLE interview_question_set (
  user_id        BIGINT UNSIGNED NOT NULL,
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  application_id BIGINT UNSIGNED COMMENT '可选(备战场景可无)',
  state          ENUM('generating','ready') NOT NULL DEFAULT 'generating',
  questions      JSON COMMENT '题集(JSON, 引 interview-question schema)',
  created_at     DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at     DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (user_id, id),
  UNIQUE KEY uk_id (id),
  KEY idx_user (user_id),
  KEY idx_app (application_id)
) COMMENT='题集(§6.16 G7-1)，驱动会话';

CREATE TABLE interview_session (
  user_id         BIGINT UNSIGNED NOT NULL,
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  question_set_id BIGINT UNSIGNED NOT NULL,
  application_id  BIGINT UNSIGNED COMMENT '可选',
  state ENUM('created','active','in_progress','paused','completed','scored','archived','abandoned') NOT NULL DEFAULT 'created',
  mode  ENUM('text','voice') NOT NULL DEFAULT 'text',
  current_turn INT UNSIGNED NOT NULL DEFAULT 0,
  started_at DATETIME(3),
  ended_at   DATETIME(3),
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (user_id, id),
  UNIQUE KEY uk_id (id),
  KEY idx_user (user_id),
  KEY idx_qs (question_set_id)
) COMMENT='面试会话(§6.16 G7-1 7态+abandoned)';

CREATE TABLE interview_question (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id      BIGINT UNSIGNED NOT NULL,
  question_set_id BIGINT UNSIGNED NOT NULL,
  turn            INT UNSIGNED NOT NULL,
  text            TEXT NOT NULL,
  type            ENUM('behavior','tech','case') NOT NULL,
  expected_points JSON,
  jd_keywords_coverage DECIMAL(4,3) COMMENT '0..1 (PRD §7.2 成功标准>=0.8)',
  created_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_session (session_id),
  KEY idx_set (question_set_id)
) COMMENT='单道面试题(引 interview-question schema)';
-- 注：子表以 session_id 关联；物理共置由 session 的 user_id 分片键路由保证(§6.15)。

CREATE TABLE interview_answer (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id   BIGINT UNSIGNED NOT NULL,
  question_id  BIGINT UNSIGNED NOT NULL,
  turn         INT UNSIGNED NOT NULL,
  modality     ENUM('text','voice_asr') NOT NULL,
  asr_provider VARCHAR(32) COMMENT 'voice_asr 时记录实际供应商, 文本为 NULL(G7-3)',
  answer_text  MEDIUMTEXT,
  turn_score   DECIMAL(4,3) COMMENT '0..1 (驱动 B03)',
  rubric       JSON COMMENT '逐维分(1-5)',
  created_at   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_session_turn (session_id, turn),
  KEY idx_session (session_id)
) COMMENT='逐轮作答(驱动 B03)';

CREATE TABLE interview_evaluation (
  session_id     BIGINT UNSIGNED NOT NULL,
  weighted_score TINYINT UNSIGNED NOT NULL COMMENT '0-100 (rubric 加权聚合 G7-2)',
  dimensions     JSON NOT NULL COMMENT '维度集(>=4维, 引 interview-evaluation schema)',
  degrade_flag   TINYINT(1) NOT NULL DEFAULT 0 COMMENT '降级评估须标 true',
  appeal_entry   TINYINT(1) DEFAULT 0,
  rerun_entry    TINYINT(1) DEFAULT 0,
  created_at     DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (session_id),
  KEY idx_score (weighted_score)
) COMMENT='评估报告(G7-2 透明可申诉)';

-- interview_session_event 同 application_event 分区约束（会话量低，可选分区）。
CREATE TABLE interview_session_event (
  user_id   BIGINT UNSIGNED NOT NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id BIGINT UNSIGNED NOT NULL,
  from_state VARCHAR(32),
  to_state   VARCHAR(32),
  reason     VARCHAR(255),
  actor      VARCHAR(32) DEFAULT 'system',
  PRIMARY KEY (user_id, created_at, id),
  UNIQUE KEY uk_id (id),
  KEY idx_session (session_id),
  KEY idx_user_created (user_id, created_at)
) COMMENT='会话审计溯源(§6.16 G7-1)';
```

### 3.5 运营 / 合规

```sql
CREATE TABLE daily_report (
  user_id             BIGINT UNSIGNED NOT NULL,
  report_date         DATE NOT NULL,
  total_applications  INT UNSIGNED NOT NULL DEFAULT 0,
  successful          INT UNSIGNED NOT NULL DEFAULT 0,
  failed              INT UNSIGNED NOT NULL DEFAULT 0,
  hr_views            INT UNSIGNED NOT NULL DEFAULT 0,
  interview_invitations INT UNSIGNED NOT NULL DEFAULT 0,
  new_questions       INT UNSIGNED NOT NULL DEFAULT 0,
  platform_breakdown  JSON,
  sent_at             DATETIME(3),
  created_at          DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (user_id, report_date),
  KEY idx_user (user_id)
) COMMENT='日报快照, 每日一条(§5.1 ⑭)；按月分区可选';

CREATE TABLE audit_log (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  actor_type  ENUM('user','service','agent','system') NOT NULL,
  actor_id    VARCHAR(64) NOT NULL,
  action      VARCHAR(48) NOT NULL COMMENT 'LOGIN/APPLY/STATUS_CHANGE/PAYMENT/ADAPTER_DEPLOY/CONFIG_PUSH/KEY_ROTATE...',
  object_type VARCHAR(48),
  object_id   VARCHAR(64),
  before_state JSON,
  after_state  JSON,
  context     JSON COMMENT 'ip/device_id/platform/request_id',
  result      VARCHAR(16) COMMENT 'success/fail',
  trace_id    VARCHAR(64),
  created_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_object (object_type, object_id),
  KEY idx_created (created_at),
  KEY idx_actor (actor_type, actor_id)
) COMMENT='统一审计日志(§6.9/§1426)；按月分区(§6.15)';
-- ⚠ 分区落地约束同 application_event：分区列 created_at 须入所有唯一键；本表无唯一键冲突，直接 PARTITION BY RANGE(TO_DAYS(created_at))。

-- 草案：字段依据 PRD §11 / §3.11 双通道；最终以通知模块 LLD 收口，本表为建议结构。
CREATE TABLE notification (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id    BIGINT UNSIGNED NOT NULL,
  channel    ENUM('push','inbox','email','sms') NOT NULL,
  level      ENUM('L0','L1','L2','L3') NOT NULL DEFAULT 'L2',
  title      VARCHAR(255) NOT NULL,
  body       TEXT,
  read_flag  TINYINT(1) NOT NULL DEFAULT 0,
  sent_at    DATETIME(3),
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_user_read (user_id, read_flag),
  KEY idx_user_created (user_id, created_at)
) COMMENT='通知(草案, 待通知模块 LLD 收口)';
```

---

## 4. Store B：本机 SQLite（WAL）

权威 DDL 见 [LLD-本机Agent与投递执行-模块设计.md](./LLD-本机Agent与投递执行-模块设计.md) §8.2。本文件仅列职责与关系，避免重复定义。

| 本地表 | 角色 | 备注 |
| --- | --- | --- |
| `task` | 投递任务队列（含幂等四元组 UNIQUE） | 与服务端 `application_task` 收敛（§8.2 UNIQUE 约束） |
| `task_event` | 本地任务事件流水 | 离线滞留，上线回写（§3.1） |
| `browser_instance` | 浏览器实例池状态 | 受 §6.14.1 进程监督 |
| `captcha_session` | 验证码人机协同会话 | §6.14.4 |
| `selector_bundle` | 适配器 DOM 选择器配置（Ed25519 签名） | §6.14.5 |
| `device_vault` | KDF 参数 + OS 安全区句柄引用（**主密钥不入 SQLite**） | §6.14.2/§6.14.8；Cookie 金库唯一落点 |

**本机 SQLite 不适用分片**（单用户本地库，§6.15 仅约束服务端高增表）；索引以 `user_id`/`account_id` 首列组织仅为本地检索便利（LLD-本机Agent §8.3）。

---

## 5. 索引设计总结（高频查询路径）

| 查询路径 | 表 | 索引 | 类型 |
| --- | --- | --- | --- |
| 用户投递列表（按状态筛选） | application | `idx_user_status(user_id, status)` | 二级索引 |
| 投递/任务幂等去重 | application / application_task | `uk_idem` / `uk_quad` / `uk_tidem` | 唯一 |
| 岗位采集去重 | job | `uk_platform_ext(platform_id, external_id)` | 唯一 |
| 账号按平台定位 | platform_account | `uk_user_platform(user_id, platform_id)` | 唯一 |
| 面试会话列表 | interview_session | `idx_user(user_id)` / `idx_qs(question_set_id)` | 二级 |
| 通知未读拉取 | notification | `idx_user_read(user_id, read_flag)` | 二级 |
| 投递事件溯源 | application_event | `idx_app(application_id)` / `idx_user_created` | 二级 |
| 会话审计溯源 | interview_session_event | `idx_session(session_id)` | 二级 |
| 审计检索（对象/操作人） | audit_log | `idx_object` / `idx_actor` | 二级 |
| 日报按日定位 | daily_report | `PRIMARY KEY(user_id, report_date)` | 主键 |

---

## 6. 分片键预留与冷热分离（§6.15 落地）

- **起步形态**：单主 + 只读副本，时序/大表按月分区；不提前分库分表（模块化单体，ADR-001）。
- **分片键预留**：`application` / `application_task` / `application_event` / `daily_report` / `resume_version` / `interview_question_set` / `interview_session` 主键或首列分区键含 `user_id`，后期按 `user_id` 哈希分片**零 schema 迁移**。
- **时间分区**：`application_event` / `daily_report` / `interview_session_event` / `audit_log` 按 `created_at` 月度分区；旧分区转冷（>24 月匿名化，§8.2）。
- **⚠ 分区物理约束**：MySQL 要求分区列 `created_at` 出现在所有唯一索引；对含 AUTO_INCREMENT 的分区表，PK 取 `(user_id, created_at, id)` 且 `id` 另建 `uk_id(id)` 满足自增首列要求（见 §3.3 / §3.4 DDL 注释）。编码期建表脚本须落实，避免运行期 `MAXVALUE`/唯一键冲突。
- **分片触发线**：用户过万时对高增表按 `user_id` 哈希分片，仅路由层 + 数据重分布，无应用层 schema 变更。

---

## 7. 数据一致性规则（§5.3 落为约束）

| 规则 | 落库手段 |
| --- | --- |
| 投递幂等 | `uk_idem` + `uk_quad` 双唯一 + Redis SETNX 前置 |
| 状态机一致性 | `application`↔`application_event` 同事务写 + Redis 分布式锁 |
| 读写分离 | Java 写主读从；支付回调后强制读主 |
| 大字段隔离 | 简历原文 OSS 外链；JSON 仅结构化快照 |
| 跨服务一致 | Python 结果经 MQ 事件回写，Java 事务落库，幂等键收敛 |
| 本机↔服务端 | 服务端 10 态为权威；Agent 回写 + 孤儿清扫 + 上线补拉；Cookie 不参与跨端一致 |
| 保留期限 | 简历/面试注销后 30 天；Cookie 登出清除（§6.14.6 可验证删除） |
| 分片预留 | 高增表首列含 `user_id`（§6.15） |

---

## 8. 迁移与版本化策略

- **Store A（服务端）**：Flyway 版本化迁移（`V1__init.sql` → `Vn__*.sql`），前向-only、幂等（`IF NOT EXISTS` / 条件 ALTER）；分片表建表脚本内置 §6.15 分区约束；迁移在历史从库验证后上主。
- **Store B（本机 SQLite）**：内置 `user_version` 自管，向前兼容追加列（`ALTER TABLE ... ADD COLUMN`），不删改列；损坏按 §6.14.1 进安全模式 + 快照恢复，绝不静默。
- **密钥与版本化**：KEK/DEK 版本化轮换（§6.14.2 / LLD-密钥与凭证工程），历史密文用旧版解，轮换不重写历史；泄露吊销该 DEK 版本并重加密（RTO≤4h）。

---

## 9. 待拍板 / 缺口登记（显式，非静默覆盖）

| 项 | 现状 | 对 schema 影响 |
| --- | --- | --- |
| `notification` 表结构 | 草案，待通知模块 LLD 收口（PRD §11 / §3.11） | 字段可能调整 |
| 分区物理 DDL 的 MySQL 唯一键含 created_at 约束 | 已说明，编码期建表脚本落实 | 无 schema 语义变更 |
| T1 ASR 厂商 / T2 rubric 第5维 / T3 加权权重 | 已登记（LLD-面试模拟域 §10） | 不改变表结构，仅 `interview_question`/`interview_evaluation` 行数据 |
| 大字段 `snapshot`/`questions`/`dimensions` JSON 容量 | 受 ADR-003 大字段隔离约束 | 超阈转 OSS 外链 |

---

## 10. 与 HLD / contracts 追溯

| HLD / contracts 锚点 | 本 LLD 落点 |
| --- | --- |
| §5.1 核心实体 ER 图 5-1（14 实体） | §2 ER 文字说明书 + §3 DDL |
| §5.2 核心表与关键字段 | §3 全表 DDL |
| §5.3 数据一致性规则 | §7 |
| §6.15 分片键预留 / 冷热分离 | §6 |
| §3.4 / ADR-008 投递 10 态 | `application.status` ENUM（§3.3） |
| §6.16 G7-1/2/3 面试域 | `interview_*` 全表（§3.4） |
| §1426 统一审计日志字段 | `audit_log`（§3.5） |
| `crawler-result.schema.json` | `job` 字段（§3.2） |
| `interview-*` schema | `interview_session/question/evaluation` 字段（§3.4） |
| §C.5 / ADR-018 Cookie 本地化 | `platform_account` 无 Cookie 列；Cookie 仅 Store B（§1 / §4） |
| HLD §10 数据库设计项 | 由「下一步」翻「已闭环」（本文档） |
