# LLD：解析质量（简历导入解析质量与边界）

> 文档版本：2026-08-16 · v1.0（交付级 LLD；闭环 HLD §9.4 §25.3 / PRD v4.5 §25.3 G4）
> 关联上游：HLD v3.22（§9.4 §25.3 / §6.13.5.2 简历多版本绑定）× PRD v4.5 §25.3（G4 需求）
> 关联 LLD：`LLD-数据库设计-模块设计.md`（resume.snapshot / job.jd_keywords_coverage）、`LLD-密钥与凭证工程-模块设计.md`（snapshot 加密轮转）

---

## 1. 范围与定位

- **主对象**：简历导入解析（PDF / DOCX / TXT / 图片-OCR），输出结构化 `snapshot`。
- **通用框架**：本文定义的五维质量评估模型（§4）与质量门禁（§6）**同时适用于**岗位解析（JD→结构化画像）、投递意图解析（自然语言→结构化投递条件）。本版优先落简历解析，框架预留 `job / intent` 扩展点。
- **边界（不做）**：
  - 不含简历采集（采集结果走 `crawler-result.schema.json` + HLD §6.14 采集契约）；
  - 不含 AI 匹配（B01 匹配走 `ai-orchestrator.registry`，本文只输出 `snapshot` 供其消费）；
  - 不含面试模拟解析（面试域独立，见 `LLD-面试模拟域-模块设计.md`）。

---

## 2. 解析对象与输入入口

| 输入类型 | 入口 | 解析路径 | 降级 / 边界 |
| --- | --- | --- | --- |
| PDF | 上传 / 采集 | 优先文本层提取 → 结构映射 | 无文本层 → 图像化 OCR |
| DOCX | 上传 | XML 解析 → 结构映射 | — |
| TXT | 上传 | 纯文本 → 结构映射 | — |
| 图片（PNG/JPG 等） | 上传 | OCR → 结构映射 | OCR 不可用 → 提示上传可编辑文本版（不静默失败） |

> 多版本绑定：同一候选人多份简历版本由 HLD §6.13.5.2 管理，本模块对**每一版本**独立产出 `snapshot` 与质量报告，不参与版本选型。

---

## 3. 解析管线（pipeline）

```
[输入] → ① 格式判定 + 文本提取（PDF 优先文本层，缺失转 OCR）
       → ② 版式分析（检测表格 / 多栏等乱版式）→ 布局解析 + 规则兜底
       → ③ 字段映射（映射到简历 schema：姓名/联系方式/教育/工作/技能/项目/…）
       → ④ 字段级置信度打分（每字段 0~1）
       → ⑤ 缺失处理（必填关键字段缺失 → 标记 "待补"，绝不臆造）
       → ⑥ 结构校验（版式合法 / 无乱码 / 字段类型合法）
       → ⑦ 输出 snapshot（结构化 JSON，含 per-field confidence + status）+ quality 报告
```

- **乱版式处理**（PRD §25.3）：表格 / 多栏采用布局解析（layout analysis）+ 规则兜底；coverage 可能下降，降级提示用户核对而非报错阻断。
- **OCR 降级**：图片简历优先 OCR；OCR 服务不可用（provider 熔断 / 离线）→ 返回 `PARSE-002`，提示用户上传可编辑文本版。

---

## 4. 质量维度（五维模型）

| 维度 | 标识 | 定义 | 目标 / 约束 | 性质 |
| --- | --- | --- | --- | --- |
| D1 字段填充率 | `coverage` | 已填关键字段数 / 必填关键字段数 | **≥ 95%**（PRD §25.3 SLA） | 实时可算 |
| D2 关键信息准确率 | `accuracy` | 关键信息（姓名/联系方式/最高学历等）抽取正确率 | **≥ 98%**（PRD §25.3 SLA） | **实测值**，需 v0.9 灰度回填（H1） |
| D3 字段级置信度 | `confidence` | AI 对每字段打分均值 / 最低关键字段分 | 门禁阈值默认 0.70（T1 可配） | 实时可算（accuracy 代理） |
| D4 结构有效性 | `validity` | 版式合法 / 无乱码 / 字段类型合法率 | 门禁阈值默认 0.90（T1 可配） | 实时可算 |
| D5 不臆造合规 | `no_hallucination` | 缺失 / 低置信字段是否全部标记 `missing`/`low_conf` | **硬约束 100%** | 实时可算（fail-closed） |

> **D2 说明**：`accuracy` 是事后实测指标，设计期无法在单次解析中计算；线上以 `confidence`（D3）作为其**代理信号**驱动门禁，灰度阶段用人工抽样回填真实 `accuracy` 校验代理有效性（见 §11 H1）。

---

## 5. 质量评分模型

综合质量分（线上实时，0~100）：

```
Q = 100 × ( w1·coverage + w2·confidence + w3·validity + w4·no_hallucination )
```

- 默认权重 `w1=0.40, w2=0.30, w3=0.20, w4=0.10`（可配置，约束 `∑w = 1`）。
- `no_hallucination` 为 0/1 离散（违例即 0）；`coverage/confidence/validity` 取 [0,1]。
- **`accuracy`（D2）不计入实时公式**，仅作为上线后监控项与灰度验收项（§11 / §12）。
- 评分仅用于排序 / 提示，**不替代门禁**（门禁见 §6，为硬规则）。

---

## 6. 质量门禁与降级策略

| 判定 | 条件 | 行为 |
| --- | --- | --- |
| **PASS** | `coverage ≥ 0.95` 且 `min(关键字段 confidence) ≥ 0.70` | 自动通过，snapshot 进入可用池 |
| **WARN（低质量，不阻断）** | 未达 PASS 但 `validity ≥ 0.90` 且 `no_hallucination = 1` | 结果可预览编辑；高亮"待补"项引导手工补全关键字段；不阻断使用 |
| **FAIL（阻断）** | `validity < 0.90`（乱码 / 类型全错）**或** `no_hallucination = 0`（臆造违例） | 解析失败，标记 `degraded`，提示重新上传 / 换格式 |
| **OCR 不可用** | 图片简历且 OCR provider 熔断 | 返回 `PARSE-002`，提示上传可编辑文本版 |

- 阈值（`coverage` 门禁、`confidence` 门禁、`validity` 门禁）由编码期配置中心确定（T1），缺失配置时启用上表默认值。
- **不阻断原则**（PRD §25.3）：WARN 态仍允许使用并人工补全，绝不因解析质量差而卡死导入流程。

---

## 7. 不臆造原则（硬约束，D5）

- 任何缺失 / 低置信字段 → 标记 `missing` 或 `low_conf`，**绝不填充伪造值**。
- 违反 → **fail-closed**：整条 resume 标记 `degraded`，触发 `PARSE-006`，提示人工核对。
- 对齐 R-10 幻觉硬熔断（HLD §9.4）：本模块"不臆造"是更前置的结构性约束，与 AI 编排服务的幻觉熔断构成双层防护。

---

## 8. 错误码（新增 `PARSE` 域，命名风格对齐 `error-codes.json`）

| 错误码 | 语义 | 严重度 | 行为 |
| --- | --- | --- | --- |
| `PARSE-001` | 格式不支持（非 PDF/DOCX/TXT/图片） | 阻断 | FAIL，提示支持格式 |
| `PARSE-002` | OCR 服务不可用（图片简历） | 阻断 | 提示上传可编辑文本版 |
| `PARSE-003` | 文本层缺失且无 OCR 兜底 | 阻断 | FAIL，提示重传 |
| `PARSE-004` | 低置信度需人工补全（WARN） | 非阻断 | 引导补全，结果可编辑 |
| `PARSE-005` | 结构校验失败（validity 违例） | 阻断 | FAIL，提示重传 / 换格式 |
| `PARSE-006` | 臆造违例（no_hallucination 违例） | 阻断（fail-closed） | 标记 degraded，提示人工核对 |

> 错误码注册到 `design/contracts/error-codes.json`（PARSE 域）为**建议收口项**（见 §10 R-parse-1），本版 LLD 先固化语义，契约化在后续迭代落地。

---

## 9. 数据存储对齐（数据库设计 LLD）

**`resume` 表**（服务端 MySQL，详见数据库设计 LLD）：

- `raw_file_ref`：简历原文 OSS 外链（库内**不存明文**）。
- `snapshot`：`JSON NOT NULL`，解析后结构化简历，**每个字段携带三元组**：
  ```json
  {
    "name":        { "value": "张三", "confidence": 0.98, "status": "filled" },
    "email":       { "value": "zhang@x.com", "confidence": 0.95, "status": "filled" },
    "phone":       { "value": null, "confidence": 0.0, "status": "missing" },
    "education":   { "value": "...", "confidence": 0.62, "status": "low_conf" }
  }
  ```
  - `status ∈ { filled, missing, low_conf }`；`missing`/`low_conf` 即"待补"标记（§7 不臆造）。
  - 加密：AES-256-GCM（§6.14.2），密钥与业务库分离、定期轮换（密钥工程 LLD §3）。
- `quality` 报告可随 `snapshot` 同存或落独立 `resume_parse_quality` 表（建议，待 §16.4 单位经济 LLD 一并定夺）。

**`job` 表**（岗位解析复用同一框架）：

- `jd_keywords_coverage DECIMAL(4,3)`：岗位关键词覆盖率（PRD §7.2 成功标准 **≥ 0.8**），对应本框架 D1（coverage）。岗位解析同样适用 D3/D4/D5。

**解析成本**（单位经济 §16.4）：

- 解析调用（含 OCR / 布局解析）计费落成本日志 / 对账，本模块只上报 `cost_token` / `cost_amount`，**不新建核心表**（成本账建议 `cost_ledger`，待 §16.4 LLD）。

---

## 10. 与 contracts / 其他 LLD 对齐

- **采集契约**：`crawler-result.schema.json` 描述"采集结果"；本模块消费采集结果 → 产出 `snapshot`，二者互补（采集 ≠ 解析）。
- **AI 编排**：B01 匹配消费本模块 `snapshot`，本模块不反向依赖 B01。
- **密钥工程**：`snapshot` 加密 / 轮转对齐密钥工程 LLD §3。
- **契约化缺口（登记）**：
  - **R-parse-1**：建议新增 `resume-parse-result.schema.json`（定义 `snapshot` 字段契约 + 质量报告 schema），并注册到 `design/contracts/`，使解析质量纳入机器可校验契约基线。本版 LLD 先固化字段规格（§9），契约化在后续迭代。
- **错误码缺口（登记）**：`PARSE-*` 六码建议并入 `error-codes.json`（R-parse-1 一并处理）。

---

## 11. 待拍板 / 假设登记

| 编号 | 项 | 状态 | 说明 |
| --- | --- | --- | --- |
| **H1（Hypothesis）** | 关键信息准确率 ≥ 98% | PRD 目标值，**非已拍板最终值** | 实测需 v0.9 灰度人工抽样回填；设计期以 `confidence` 代理 |
| **T1** | 门禁阈值（coverage 0.95 / confidence 0.70 / validity 0.90） | 编码期配置中心确定 | 缺失配置启用默认值；fail-closed 最严档 |
| **T2** | OCR 厂商选型（具体云端 / 端侧） | 编码期确定 | 已固化抽象 `OCRProvider` + 降级链（cloud→不可用提示） |
| — | 综合分权重 w1~w4 | 默认可配置，`∑=1` | 默认 0.4/0.3/0.2/0.1 |

> H1 的 `accuracy` 实测值回填前，本模块质量评估以 D1/D3/D4/D5 实时四维驱动门禁，D2 仅作监控，不阻塞发布。

---

## 12. 测试验收

| 场景 | 输入 | 期望 |
| --- | --- | --- |
| 缺失字段不臆造 | 简历缺 phone | `phone.status = missing`，无伪造值；D5 = 1 |
| 门禁 PASS | coverage 0.96 + min(conf) 0.75 | PASS，snapshot 入可用池 |
| 门禁 WARN | coverage 0.94（仅差一项） | WARN，高亮"待补"，可编辑不阻断 |
| 门禁 FAIL | validity 0.85（乱码） | FAIL，`PARSE-005`，提示重传 |
| OCR 降级 | 图片简历 + OCR 不可用 | `PARSE-002`，提示上传文本版 |
| 臆造违例 | 注入伪造字段 | `PARSE-006`，fail-closed，degraded |
| 准确率回填（H1 验证） | 灰度样本人工标注 | 实测 `accuracy` 回填，校验 `confidence` 代理有效性 |

---

## 13. 自检（与 HLD/PRD/数据库设计 LLD 对齐）

- [x] PRD §25.3 G4 五条需求全覆盖：格式支持 / OCR 降级 / 乱版式兜底 / 不臆造 / 置信度引导补全 / 可预览编辑 / SLA 数值。
- [x] 数据库设计 LLD：`resume.snapshot`（per-field 三元组）、`job.jd_keywords_coverage` 对齐。
- [x] 密钥工程 LLD：snapshot 加密 / 轮转对齐。
- [x] R-10 幻觉熔断：不臆造（D5）为前置结构性约束，双层防护。
- [x] 待数据项（H1 accuracy）显式登记，未静默覆盖为"已闭环"。
