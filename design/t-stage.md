# T 阶段 · 真实测试闭环交付说明

> 角色：QA(`software-qa-engineer`) 主导；工程师配合修 bug；Team Lead 汇总。
> 对应 PROJECT_BRAIN §1 V/T/O 七阶段之 **T 阶段（T1/T2/T3）**。
> 本文是「真实测试闭环」的权威交付说明，区别于早期 B 阶段的「冒烟 + 设计一致性」测试。

## 0. 闭环边界（诚实声明）
T 阶段验证的是**本地可构建、过门禁、带测试的系统代码**，不是「已在跑真人数据的线上系统」。
所有被测对象均运行在 `scaffold/`（零外部依赖桩）+ `frontend/`（生产前端骨架，本地不部署）上。
部署上线 / 真实用户 / 真实凭据属用户独有动作，不在本阶段范围。

## 1. 交付物
- **`scaffold/tests/test_t_stage.py`**（新增，T 阶段权威收敛文件）：覆盖 T1/T2/T3 三件套，44 条断言全 PASS。
- **A22 后端桩修复**（真实集成 gap 修复）：`scaffold/src/stubs/notifications.py` 的 `notifications-list` handler 原缺 `body`/`channel` 字段，而响应 schema（`notifications-list.response.schema.json`）已声明、前端 U8 `Notifications.jsx` 实际读取。已补齐，使后端 ↔ schema ↔ 前端三方字段对齐。

## 2. 测试内容（T1 / T2 / T3）
### T1 · 功能测试（9 类安全/护栏属性）
- 本机 Agent 投递编排核心：**半自动确认闸门**（未确认绝不执行 → `skipped_unconfirmed`）、**当日限额**（`skipped_quota`）、**幂等去重**（二次同岗 → `skipped_duplicate`）、**验证码暂停**（`pending_captcha`，不失败不卡死）、**low 匹配规划过滤**。
- 服务端投递状态机：`create→autofilling`、`record_submission→submitted`、`record_failure→closed`、已 submitted 自环跃迁被拒绝（防误触发、事件与合法跃迁一一对应）。
- 事件总线 **fail-closed**：非法金额事件被拒且不入审计日志。
- **护栏 2（LLM 成本硬上限 + 熔断）**：默认日硬上限 ¥500 装配到位；累计超帽后熔断器打开、剩余额度 ≤0。
- **护栏 3（封号率监控）**：封号率 1% 不告警、3% 触发 `ban_rate_high`；投递成功率 <80% 触发 `apply_success_low`。

### T2 · 集成测试（本机 Agent + 服务端 + 前端三联调一致性）
- **端点契约对齐**：后端注册表 25 个 A 编号集合 == 前端 `frontend/src/lib/api.js` `ENDPOINTS` 25 个 A 编号集合（精确相等，无缺漏/无多余）。
- **字段契约对齐**：前端组件实际读取的字段，后端 example 响应必须提供——
  - A22：`items[].{id,level,title,body,read,createdAt,channel}` + `unread`；
  - A24：`stats.{appliedTotal,success,failed,byPlatform,hrViews,interviewInvites,newQuestions,trend7d}`，`byPlatform[].{platformId,count}`；
  - A01：`accessToken`；A03：`{userId,plan,quotaUsed,quotaLimit}`。

### T3 · 契约回归
- **25 端点 example_request 全过 `response_schema`**（契约优先，fail-closed 500 暴露「实现偏离契约」）——0 偏离。
- 响应侧 fail-closed 机制本身可用：构造响应契约违规探针端点，验证 `Endpoint.dispatch` 返回 `500 + response_schema_violation`（暴露而非吞掉）。

## 3. 运行方式与结果
- 运行：`python scaffold/tests/test_t_stage.py`（零外部依赖，仅标准库）。
- 结果：**44 条断言全部 PASS**（T1 功能 / T2 集成 / T3 契约回归）。
- 全量回归：`scaffold/tests/` 下 **13 个测试文件全部 PASS**（含原 B 阶段 12 个 + 本阶段 1 个），无回归。
- 双闸门（REVIEW-1）：契约校验（gate1）+ PRD/HLD 追溯（gate2）实跑全绿（见提交前校验记录）。

## 4. 已知事项 / 不伪造完成
- A22 字段缺失为本次 T2 主动发现的真实集成 gap，已在后端桩补齐（demo 数据，无安全红线）。前端 `api.js` mock 原已含 `body`/`channel`，真实后端补齐后 mock 与生产同形。
- T 阶段仅覆盖**本地代码级**功能/集成/契约测试；端到端（真实浏览器跑前端 + 真实后端 HTTP 层 + 真实平台）与真实用户反馈回路属用户独有动作，循环标「待用户触发」，不伪造已闭环。
- 护栏 4/5/6（灰度回滚 / PIPL crypto-shred+合规 / 法检复核）= 用户 2026-08-17 延后，不计入本次 /goal，如实标注「用户延后」。

## 5. 结论
T 阶段（真实测试闭环）**达成** ✅：功能安全属性、前后端契约对齐、25 端点契约回归三件套齐备且全绿。
下一步：O 阶段（运维就绪：CI/CD 配置 + 轻量 CD 脚本 + 监控接入代码）。
