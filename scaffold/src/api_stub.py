"""
api_stub.py — 契约优先的接口分发骨架（D 阶段奠基切片）

演示「请求入参 + 响应出参 都必须过契约校验」的 contract-first 模式。
这是一个传输无关的「端点」抽象：生产环境把它挂到 FastAPI/Flask/本机 Agent 的
HTTP 层即可，但「校验规则」与这里完全一致 —— 换 Web 框架不改契约逻辑。

本切片已落地 **Auth 模块 (A01 登录 + A02 刷新令牌)**、**Jobs 模块
(A07 岗位搜索 + A08 收藏/忽略)**、**User 模块 (A03 当前用户与权益)** 与
**Resume 模块 (A04 创建简历 + A05 版本列表 + A06 触发 ATS 评分)**
共八个端点，证明模块级 contract-first 落地模式可行；后续 A 层端点按同模式
逐一对齐 schema 即可（见 README §3 脚手架顺序）。每个端点都是一个 `Endpoint`
实例，统一由 `API_STUB` 注册表按 id 分发。

`Endpoint` 同时支持「有请求体」与「无请求体（GET 类，request_schema=None）」
两类端点：无请求体时跳过入参校验、只校验响应，覆盖 A 层大量 GET 端点
(A03/A05/A09/A11/A12/A14/A16-A23/A25)，避免为它们造空请求 schema。

⚠️ 安全边界（REVIEW-3 红线规避）：本文件所有 handler 均为 **demo / mock 桩**，
只返回符合响应契约结构的占位数据，**不实现任何真实业务逻辑**
（不含密码校验、令牌签发/签名、凭据存储、会话策略、真实查询/写库）。
真实实现在 B 阶段由服务端各业务模块完成，本脚手架仅演示「契约校验」机制本身。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contract_runtime import validate_payload


class Endpoint:
    """一个契约优先的端点：请求/响应均先校验，再执行 handler。"""

    def __init__(self, name: str, request_schema: str, response_schema: str, handler):
        self.name = name
        self.request_schema = request_schema
        self.response_schema = response_schema
        self._handler = handler

    def dispatch(self, request: dict) -> tuple[int, dict]:
        """分发一次调用。

        返回 (HTTP 状态码, body)。
          - 请求不合规 -> 422（fail-closed，绝不执行业务）
          - 响应不合规 -> 500（实现偏离契约，暴露而非吞掉）
          - 正常        -> 200 + handler 结果

        无请求体端点（如 GET，`request_schema is None`）跳过入参校验，
        只校验响应 —— 覆盖 A 层大量 GET 端点。
        """
        if self.request_schema is not None:
            ok, err = validate_payload(self.request_schema, request)
            if not ok:
                return 422, {"error": "request_schema_violation", "detail": err}

        resp = self._handler(request)

        ok2, err2 = validate_payload(self.response_schema, resp)
        if not ok2:
            return 500, {"error": "response_schema_violation", "detail": err2}
        return 200, resp


class ApiStub:
    """端点注册表 + 按 id 分发。生产环境可挂 HTTP 层，此处仅演示契约校验。"""

    def __init__(self):
        self._endpoints = {}

    def register(self, endpoint: Endpoint) -> Endpoint:
        self._endpoints[endpoint.name] = endpoint
        return endpoint

    def dispatch_id(self, endpoint_id: str, request: dict) -> tuple[int, dict]:
        ep = self._endpoints.get(endpoint_id)
        if ep is None:
            return 404, {"error": "unknown_endpoint", "endpoint": endpoint_id}
        return ep.dispatch(request)

    def endpoint_ids(self) -> list[str]:
        return list(self._endpoints.keys())


# ---- Auth 模块 demo 桩（仅演示契约，不含真实鉴权）----

def _login_handler(req: dict) -> dict:
    # 真实实现会校验密码 + 派发令牌；此处只回一个符合响应契约的结构
    # （响应契约要求 accessToken/refreshToken/expiresIn/userId/plan，且 additionalProperties:false）
    return {
        "accessToken": "demo-access-token",
        "refreshToken": "demo-refresh-token",
        "expiresIn": 3600,
        "userId": "U-demo",
        "plan": "free",
    }


def _refresh_handler(req: dict) -> dict:
    # 真实实现会用 refreshToken 换发新 accessToken，并视策略轮转 refreshToken；
    # 此处只回符合响应契约的占位结构（refreshToken 未轮转时可为 null）
    return {
        "accessToken": "demo-access-token-renewed",
        "expiresIn": 3600,
        "refreshToken": None,
    }


AUTH_LOGIN = Endpoint(
    name="A01 auth-login",
    request_schema="auth-login.request.schema.json",
    response_schema="auth-login.response.schema.json",
    handler=_login_handler,
)

AUTH_REFRESH = Endpoint(
    name="A02 auth-refresh",
    request_schema="auth-refresh.request.schema.json",
    response_schema="auth-refresh.response.schema.json",
    handler=_refresh_handler,
)

# ---- Jobs 模块 demo 桩（仅演示契约，不含真实查询/写库业务逻辑）----

def _jobs_search_handler(req: dict) -> dict:
    # 真实实现会按 keyword/location/platform/salaryMin/page/pageSize 查询岗位库；
    # 此处只回符合响应契约的占位结构。jobStub 必填字段：
    # jobId/title/company/platformId/source/collectedAt（其余字段可空，已含演示值）。
    return {
        "items": [
            {
                "jobId": "J-demo-001",
                "title": "Java 开发工程师",
                "company": "示例科技有限公司",
                "platformId": "boss-1001",
                "salaryMin": 15000,
                "salaryMax": 25000,
                "location": "深圳",
                "source": "search",
                "matchScore": 88,
                "matchBand": "green",
                "matchReason": "技能匹配度高",
                "favorited": False,
                "collectedAt": 1760000000000,
            }
        ],
        "total": 1,
        "page": req.get("page", 1),
        "pageSize": req.get("pageSize", 20),
    }


def _jobs_favorite_handler(req: dict) -> dict:
    # 真实实现会按 jobId(path) + action 写收藏/忽略状态（action 幂等）；
    # 此处只回符合响应契约的占位结构。path 参数 {id} 不在请求体契约内（仅 body 过契约）。
    action = req.get("action")
    if action == "favorite":
        return {"ok": True, "favoriteId": "F-demo-001", "status": "favorited"}
    return {"ok": True, "favoriteId": None, "status": "ignored"}


JOBS_SEARCH = Endpoint(
    name="A07 jobs-search",
    request_schema="jobs-search.request.schema.json",
    response_schema="jobs-list.response.schema.json",
    handler=_jobs_search_handler,
)

JOBS_FAVORITE = Endpoint(
    name="A08 jobs-favorite",
    request_schema="jobs-favorite.request.schema.json",
    response_schema="jobs-favorite.response.schema.json",
    handler=_jobs_favorite_handler,
)

# ---- User 模块 demo 桩（仅演示契约，不含真实查询/权限判定业务逻辑）----

def _user_me_handler(req: dict) -> dict:
    # 真实实现会按 Bearer 令牌解析当前用户、回权益上下文（plan/quota/preferences）；
    # 此处只回符合响应契约的占位结构。响应契约 required：userId/plan/quotaUsed/quotaLimit；
    # plan 枚举 free|pro|team；email/preferences 可空（nullable）。无请求体（request_schema=None）。
    return {
        "userId": "U-demo",
        "email": "user@x.com",
        "plan": "free",
        "quotaUsed": 0,
        "quotaLimit": 100,
        "preferences": {"pushTime": "09:00", "doNotDisturb": False},
    }


USER_ME = Endpoint(
    name="A03 users-me",
    request_schema=None,  # GET /users/me 无请求体
    response_schema="user-me.response.schema.json",
    handler=_user_me_handler,
)


# ---- Resume 模块 demo 桩（仅演示契约，不含真实写库/ATS 业务逻辑）----

def _resumes_create_handler(req: dict) -> dict:
    # 真实实现会落库结构化 content、生成首个版本快照(version_no=1)、回填 resumeId/versionId；
    # 此处只回符合响应契约的占位结构。响应契约 required：resumeId/versionId/createdAt；
    # createdAt 为 epoch 毫秒（minimum:0）；additionalProperties:false。
    return {
        "resumeId": "R-demo-001",
        "versionId": "RV-demo-001",
        "createdAt": 1760000000000,
    }


def _resume_versions_handler(req: dict) -> dict:
    # 真实实现会按 {id} 查该简历的全部版本快照；此处只回符合响应契约的占位结构。
    # 响应契约 required：versions[]/diffAvailable；versionStub required：
    # versionId/versionNo/createdAt/isPreferred；note 可空(nullable)。
    # 单版本场景 diffAvailable=false（版本数<2 不可 diff）。
    return {
        "versions": [
            {
                "versionId": "RV-demo-001",
                "versionNo": 1,
                "createdAt": 1760000000000,
                "note": "初始版本",
                "isPreferred": True,
            }
        ],
        "diffAvailable": False,
    }


def _resume_ats_handler(req: dict) -> dict:
    # 真实实现会锁版本(resumeVersionId)并派发异步 ATS 评分任务(经 AI 编排 b05)；
    # 此处只回符合响应契约的占位结构。响应契约 required：taskId/status；
    # status 枚举 pending|running|done|failed（占位取 pending）。
    return {
        "taskId": "T-ats-demo-001",
        "status": "pending",
    }


RESUMES_CREATE = Endpoint(
    name="A04 resumes-create",
    request_schema="resumes-create.request.schema.json",
    response_schema="resumes-create.response.schema.json",
    handler=_resumes_create_handler,
)

RESUME_VERSIONS = Endpoint(
    name="A05 resumes-versions",
    request_schema=None,  # GET /resumes/{id}/versions 无请求体
    response_schema="resume-versions.response.schema.json",
    handler=_resume_versions_handler,
)

RESUME_ATS = Endpoint(
    name="A06 resumes-ats",
    request_schema="resume-ats.request.schema.json",
    response_schema="resume-ats.response.schema.json",
    handler=_resume_ats_handler,
)


# 全局注册表：已落地 Auth 模块（A01/A02）+ Jobs 模块（A07/A08）+ User 模块（A03）
# + Resume 模块（A04/A05/A06），后续端点按同模式注册即可。
API_STUB = ApiStub()
API_STUB.register(AUTH_LOGIN)
API_STUB.register(AUTH_REFRESH)
API_STUB.register(JOBS_SEARCH)
API_STUB.register(JOBS_FAVORITE)
API_STUB.register(USER_ME)
API_STUB.register(RESUMES_CREATE)
API_STUB.register(RESUME_VERSIONS)
API_STUB.register(RESUME_ATS)


if __name__ == "__main__":
    code, body = AUTH_LOGIN.dispatch({"channel": "email", "deviceId": "dev-001",
                                       "email": "user@x.com", "password": "secret123"})
    print("合法登录 ->", code, body)

    code2, body2 = AUTH_LOGIN.dispatch({"channel": "email", "deviceId": "dev-001",
                                         "foo": "bar"})  # 含禁止额外字段
    print("非法登录 ->", code2, body2)

    code3, body3 = API_STUB.dispatch_id("A02 auth-refresh", {"refreshToken": "rt-abc"})
    print("合法刷新 ->", code3, body3)

    code4, body4 = API_STUB.dispatch_id("A02 auth-refresh", {})  # 缺 refreshToken
    print("非法刷新 ->", code4, body4)

    code5, body5 = API_STUB.dispatch_id("A07 jobs-search",
                                        {"page": 1, "pageSize": 20, "keyword": "Java"})
    print("合法岗位搜索 ->", code5, "items=", len(body5.get("items", [])))

    code6, body6 = API_STUB.dispatch_id("A07 jobs-search",
                                        {"foo": "bar"})  # 缺 page/pageSize + 额外字段
    print("非法岗位搜索 ->", code6)

    code7, body7 = API_STUB.dispatch_id("A08 jobs-favorite", {"action": "favorite"})
    print("合法收藏 ->", code7, body7)

    code8, body8 = API_STUB.dispatch_id("A08 jobs-favorite", {"action": "bad"})  # 非法枚举
    print("非法收藏(枚举外) ->", code8)

    # ---- A03 当前用户与权益（无请求体 GET 端点）----
    code9, body9 = USER_ME.dispatch({})  # 无请求体，跳过入参校验
    print("合法当前用户 ->", code9, "plan=", body9.get("plan"))

    code10, body10 = API_STUB.dispatch_id("A03 users-me", {})  # 注册表分发
    print("注册表分发 A03 ->", code10, "userId=", body10.get("userId"))

    # ---- Resume 模块（A04/A05/A06）----
    code11, body11 = RESUMES_CREATE.dispatch(
        {"title": "Java 工程师简历", "content": {"sections": {}}, "templateId": "tpl-01"})
    print("合法创建简历 A04 ->", code11, "resumeId=", body11.get("resumeId"))

    code12, _ = RESUMES_CREATE.dispatch({"foo": "bar"})  # 缺 required + 额外字段
    print("非法创建简历 A04(缺 title/content) ->", code12)

    code13, body13 = RESUME_VERSIONS.dispatch({})  # 无请求体 GET 端点
    print("合法版本列表 A05 ->", code13,
          "versions=", len(body13.get("versions", [])),
          "diffAvailable=", body13.get("diffAvailable"))

    code14, body14 = RESUME_ATS.dispatch({"resumeVersionId": "RV-demo-001"})
    print("合法触发 ATS A06 ->", code14, "status=", body14.get("status"))

    code15, _ = RESUME_ATS.dispatch({})  # 缺 resumeVersionId
    print("非法触发 ATS A06(缺 resumeVersionId) ->", code15)

    code16, _ = API_STUB.dispatch_id("A04 resumes-create",
                                     {"title": "x", "content": {}})
    print("注册表分发 A04 ->", code16)
    code17, _ = API_STUB.dispatch_id("A05 resumes-versions", {})
    print("注册表分发 A05 ->", code17)
    code18, _ = API_STUB.dispatch_id("A06 resumes-ats",
                                     {"resumeVersionId": "RV-demo-001"})
    print("注册表分发 A06 ->", code18)
