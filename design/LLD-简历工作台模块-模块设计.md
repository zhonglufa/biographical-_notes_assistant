# LLD 详细设计：简历工作台模块（服务端 Java）

> 文档版本：2026-08-16 · v1.0（交付级 LLD；闭合审查报告 P2「简历工作台」业务子域真缺失项）
> 编写依据：LLD 交付标准（IEEE 1016-2009 / GB-T 8567—2006 / Amazon LLD 模板）
> 关联上游：HLD v3.26（§3.2 简历工作台模块 / §4.1 A 层 / §6.13.5.2 简历多版本绑定 / ADR-012 快照版本 / ADR-003 原文不落库）× PRD v4.5 模块 1（简历内容与版本）/ §7.3（ATS 评分）
> 定位：LLD 序列之**简历工作台模块**（服务端 Java）；简历内容与版本资产存取、快照 diff、ATS 评分触发；不做文本润色（交 Python）、不管理模板 CSS 视觉（前端）
> 作者：资深架构师（AI 协作）

---

## 0. 模块定位与边界

- **职责**（HLD §3.2）：简历内容与版本资产的存取、快照 diff、ATS 评分触发、导出。
- **边界**：不调 LLM 做文本润色（交 Python 引擎经 B04）；不管理模板 CSS 视觉细节（前端/模板服务）；不触发投递（状态机模块 §3.4）。
- **依赖**：MySQL（`resume` / `resume_version` / `ats_report`）、OSS（导出文件原文外链，ADR-003）、AI 编排（B05 ATS，`resume-ats` → `b05-ats`）。
- **职责补充（显式登记）**：HLD §3.2.1 提及 `POST /resumes/{id}/diff`，但外部 API 注册表 A 层仅登记 A05（列表）与 A06（ATS）。本 LLD 将 diff 作为 A05 资源下的动作处理（路径 `POST /resumes/{id}/diff`），并登记 T-RW-3 在编码期显式拆分 A28 入注册表。

## 1. 简历内容与版本资产（A04 / A05）

- **内容与样式分离存储**（[Data-backed] PRD 模块 1）：`resume` 存头部（title / preferred_version_id）；`resume_version` 存 `snapshot`（解析后结构化简历 JSON，`is_encrypted` AES-256-GCM，§6.14.2）+ `raw_file_ref`（OSS 原文外链，不落库，ADR-003）。
- **快照式版本管理（ADR-012）**：每次保存/导入生成新 `resume_version`（version_no 递增），历史不可变；`resume.preferred_version_id` 指向默认投递版本；投递时锁定当时 `resume_version_id`（数据库设计 LLD `application.resume_version_id`）。
- **A04 创建**：`resume-create.request/response.schema.json`；创建即落首个版本（version_no=1），`preferred_version_id` 默认指向它。
- **A05 版本列表**：`resume-versions.response.schema.json`，返回版本元信息 + `diffAvailable`（版本数≥2）。

## 2. 结构化 diff（ADR-012）

- **动作**：`POST /resumes/{id}/diff`（`resume-diff.request/response.schema.json`），对任意两版本 `snapshot` 做字段级比对，输出 `changes[]`（field / op∈{added,removed,modified} / from / to）。
- **算法**：递归比对两 JSON（section→field 路径为 key），缺失/新增/值变更分别标 added/removed/modified；不比对 `created_at` 等元数据。O(节点数)，版本快照通常 <1000 节点，单次 diff <50ms。
- **冲突消解（LWW，[Data-backed] PRD 模块 8）**：并发编辑以**最后保存版本为准**；前端用乐观锁（`resume_version.version_no` 或 `updated_at` 校验），提交时若基础版本已变则提示「版本已过时需刷新」，服务端拒绝覆盖陈旧写入。

## 3. ATS 评分触发（A06 → B05）

- **动作**：`POST /resumes/ats-score`（`resume-ats.request/response.schema.json`，异步）：请求锁 `resumeVersionId`（评分中内容不可漂移），返回 `taskId` + `status(pending|running|done|failed)`。
- **下游**：经 AI 编排 `/internal/ai/ats-score`（B05，`b05-ats.request/response.schema.json`）同步返回评分报告（atsScore 0–100 + suggestions[]）；LLM 不可用时降级纯规则仍返回（[Data-backed] PRD §7.3）。
- **结果持久化（本 LLD 闭合的真实缺口）**：评分结果回填 `ats_report(resume_version_id, ats_score, suggestions, model, created_at)`（见 §6），供版本列表/投递前自检查询；不每次重算。

## 4. 导出（OSS PDF/HTML）

- 导出文件落 OSS 后返回下载 URL（不落业务库，ADR-003）；`raw_file_ref` 仅存外链。导出为同步生成 + 异步大文件两种模式，超阈值转后台任务（T-RW-2 登记具体任务表/OSS key 保留期）。

## 5. 数据表对齐（数据库设计 LLD 收口）

- 复用 `resume` / `resume_version`（§1/§2 字段已对齐）。
- **本 LLD 发现并闭合的真实缺口**：ATS 评分报告在数据库设计 LLD 中无持久化表。已在 `LLD-数据库设计-模块设计.md` §3.2 新增 `ats_report` 表（resume_version_id 主键 + 评分 + 建议 + 模型 + 时间）+ ER/索引登记。
- 导出任务表（OSS key / 状态）按 T-RW-2 待编码期补，不阻塞本版。

## 6. 事件契约

- 发布：`resume.version.created {userId, resumeId, versionId, versionNo}`（触发 §3.3 匹配重算若为新首选版本）、`resume.preferred.changed {userId, resumeId, versionId}`（§3.3 异步匹配管道重算依据）、`resume.ats.done {userId, resumeVersionId, atsScore}`。
- 订阅：无（本模块为数据供给侧）。

## 7. 错误码映射（复用 A 命名空间）

- `RESOURCE_NOT_FOUND` / `NOT_FOUND`：简历/版本不存在。
- `INVALID_PARAM`：标题空 / diff 两版本非同一 resume / ATS 版本不存在。
- `QUOTA_EXCEEDED`：免费版版本数上限（策略配置 §3.5 限额）。
- `LLM_DEGRADED`：ATS LLM 降级为纯规则（响应仍成功，标 degradeFlag）。

## 8. 待决项登记（非静默）

| 项 | 说明 |
|----|------|
| T-RW-1 ATS 报告表已补 | `ats_report` 已落数据库设计 LLD §3.2；评分回填/查询路径由编码期落实 |
| T-RW-2 导出任务表 / OSS key 保留期 | 大文件异步导出任务状态与 OSS key 保留策略（建议 7 天），关联 ADR-003 |
| T-RW-3 拆分 A28（diff）入注册表 | `POST /resumes/{id}/diff` 当前作为 A05 子动作；编码期显式登记 A28 并补 schema |

## 9. 契约索引

| 端点/契约 | 文件 | 状态 |
|----------|------|------|
| A04 创建请求/响应 | `contracts/resumes-create.request/response.schema.json` | fully-detailed |
| A05 版本列表响应 | `contracts/resume-versions.response.schema.json` | fully-detailed |
| A05 diff 请求/响应 | `contracts/resume-diff.request/response.schema.json` | fully-detailed |
| A06 ATS 触发请求/响应 | `contracts/resume-ats.request/response.schema.json` | fully-detailed |
| B05 ATS（复用） | `contracts/b05-ats.*.schema.json` | fully-detailed |
