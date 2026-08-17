"""
test_smoke.py — D 阶段奠基切片冒烟测试（零外部依赖，仅标准库）

验证三件事：
  1) 契约加载/校验可用（contract_runtime）
  2) 事件发布前的契约校验 fail-closed（event_bus）
  3) 接口分发的契约校验 fail-closed（api_stub）

运行：
  cd scaffold && python tests/test_smoke.py
（需 Python 3.10+；复用仓库 design/contracts/ 的零依赖校验器）
"""
import os
import sys
import traceback

# 让 import 能找到 src 下的模块
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))

from contract_runtime import validate_payload
from event_bus import EventBus, build_payment_status_event
from api_stub import (AUTH_LOGIN, AUTH_REFRESH, JOBS_SEARCH, JOBS_FAVORITE, USER_ME,
                      RESUMES_CREATE, RESUME_VERSIONS, RESUME_ATS, API_STUB)


def _check(name: str, cond: bool):
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}")
    if not cond:
        raise AssertionError(name)


def test_contract_runtime():
    print("· contract_runtime")
    ok, _ = validate_payload("auth-login.request.schema.json",
                             {"channel": "email", "deviceId": "dev-001",
                              "email": "user@x.com", "password": "secret123"})
    _check("合法登录请求通过", ok is True)

    bad, err = validate_payload("auth-login.request.schema.json",
                                {"channel": "email", "deviceId": "dev-001",
                                 "foo": "bar"})  # additionalProperties:false 禁止额外字段
    _check("非法登录请求被拒", bad is False and len(err) > 0)


def test_event_bus():
    print("· event_bus")
    bus = EventBus()
    got = []
    bus.subscribe("payment.status.changed", lambda p: got.append(p))

    ok, msg = bus.publish(build_payment_status_event("O1", "U1", "paid", 29900))
    _check("合法支付事件发布成功", ok is True and len(got) == 1)

    ok2, msg2 = bus.publish(build_payment_status_event("O2", "U1", "paid", -1))
    _check("非法支付事件被拒(fail-closed)", ok2 is False and len(got) == 1)


def test_api_stub():
    print("· api_stub (Auth 模块 A01/A02)")
    # ---- A01 登录 ----
    code, body = AUTH_LOGIN.dispatch({"channel": "email", "deviceId": "dev-001",
                                       "email": "user@x.com", "password": "secret123"})
    _check("合法登录 200 + 响应合规", code == 200 and body.get("plan") == "free")

    code2, _ = AUTH_LOGIN.dispatch({"channel": "email", "deviceId": "dev-001",
                                     "foo": "bar"})  # 含禁止额外字段
    _check("非法登录 422(fail-closed)", code2 == 422)

    # ---- A02 刷新令牌 ----
    code3, body3 = AUTH_REFRESH.dispatch({"refreshToken": "rt-demo"})
    _check("合法刷新 200 + 响应含新 accessToken",
           code3 == 200 and isinstance(body3.get("accessToken"), str)
           and body3["accessToken"])

    code4, _ = AUTH_REFRESH.dispatch({})  # 缺必需字段 refreshToken
    _check("非法刷新(缺 refreshToken) 422(fail-closed)", code4 == 422)

    # ---- 注册表按 id 分发 ----
    code5, _ = API_STUB.dispatch_id("A01 auth-login",
                                    {"channel": "email", "deviceId": "dev-001",
                                     "email": "user@x.com", "password": "secret123"})
    _check("注册表分发 A01 -> 200", code5 == 200)

    code6, _ = API_STUB.dispatch_id("A02 auth-refresh", {"refreshToken": "rt-demo"})
    _check("注册表分发 A02 -> 200", code6 == 200)

    code7, _ = API_STUB.dispatch_id("ZZZ-unknown", {"x": 1})
    _check("未注册端点 -> 404", code7 == 404)

    _check("注册表含 A01/A02 两端点",
           set(API_STUB.endpoint_ids()) >= {"A01 auth-login", "A02 auth-refresh"})


def test_api_stub_jobs():
    print("· api_stub (Jobs 模块 A07/A08)")
    # ---- A07 岗位搜索 ----
    code, body = JOBS_SEARCH.dispatch({"page": 1, "pageSize": 20, "keyword": "Java"})
    _check("合法岗位搜索 200 + 响应含 items/total/page/pageSize",
           code == 200 and body.get("total") == 1
           and body.get("page") == 1 and body.get("pageSize") == 20
           and isinstance(body.get("items"), list) and len(body["items"]) == 1)

    # jobStub 必填字段齐全 + 枚举合法（matchBand=green 在枚举内）
    stub = body["items"][0]
    _check("jobStub 必填字段齐全",
           all(k in stub for k in
               ("jobId", "title", "company", "platformId", "source", "collectedAt")))
    _check("jobStub matchBand 在枚举内",
           stub.get("matchBand") in ("green", "blue", "gray"))

    code2, _ = JOBS_SEARCH.dispatch({"foo": "bar"})  # 缺 page/pageSize + 额外字段
    _check("非法岗位搜索(缺 page/pageSize) 422(fail-closed)", code2 == 422)

    # ---- A08 收藏/忽略 ----
    code3, body3 = JOBS_FAVORITE.dispatch({"action": "favorite"})
    _check("合法收藏 200 + status=favorited + favoriteId 非空",
           code3 == 200 and body3.get("status") == "favorited"
           and isinstance(body3.get("favoriteId"), str) and body3["favoriteId"])

    code4, body4 = JOBS_FAVORITE.dispatch({"action": "ignore"})
    _check("合法忽略 200 + status=ignored + favoriteId=null",
           code4 == 200 and body4.get("status") == "ignored"
           and body4.get("favoriteId") is None)

    code5, _ = JOBS_FAVORITE.dispatch({"action": "bad"})  # 枚举外值
    _check("非法收藏(枚举外 action) 422(fail-closed)", code5 == 422)

    # ---- 注册表按 id 分发 ----
    code6, _ = API_STUB.dispatch_id("A07 jobs-search",
                                    {"page": 1, "pageSize": 20})
    _check("注册表分发 A07 -> 200", code6 == 200)

    code7, _ = API_STUB.dispatch_id("A08 jobs-favorite", {"action": "favorite"})
    _check("注册表分发 A08 -> 200", code7 == 200)

    _check("注册表含 A07/A08 两端点",
           set(API_STUB.endpoint_ids()) >= {"A07 jobs-search", "A08 jobs-favorite"})


def test_api_stub_user():
    print("· api_stub (User 模块 A03 · 无请求体 GET 端点)")
    # ---- A03 当前用户与权益（GET，无请求体）----
    code, body = USER_ME.dispatch({})  # 无请求体，跳过入参校验
    _check("无请求体端点 200 + 响应合规",
           code == 200 and body.get("userId") == "U-demo")

    # 响应契约 required 字段齐全
    _check("A03 响应必填字段齐全(userId/plan/quotaUsed/quotaLimit)",
           all(k in body for k in
               ("userId", "plan", "quotaUsed", "quotaLimit")))
    # plan 枚举合法（free|pro|team）
    _check("A03 plan 在枚举内",
           body.get("plan") in ("free", "pro", "team"))
    # additionalProperties:false -> 不能含未声明字段（演示值均声明）
    _check("A03 响应未含未声明额外字段",
           set(body.keys()) <= {"userId", "email", "plan",
                                "quotaUsed", "quotaLimit", "preferences"})

    # ---- 注册表按 id 分发 ----
    code2, _ = API_STUB.dispatch_id("A03 users-me", {})
    _check("注册表分发 A03 -> 200", code2 == 200)

    _check("注册表含 A03 端点", "A03 users-me" in API_STUB.endpoint_ids())


def test_api_stub_resume():
    print("· api_stub (Resume 模块 A04/A05/A06)")
    # ---- A04 创建简历 ----
    code, body = RESUMES_CREATE.dispatch(
        {"title": "Java 工程师简历", "content": {"sections": {}}, "templateId": "tpl-01"})
    _check("合法创建简历 200 + 响应含 resumeId/versionId/createdAt",
           code == 200 and body.get("resumeId")
           and body.get("versionId") and isinstance(body.get("createdAt"), int)
           and body["createdAt"] >= 0)

    code2, _ = RESUMES_CREATE.dispatch({"foo": "bar"})  # 缺 title/content + 额外字段
    _check("非法创建简历(缺 title/content) 422(fail-closed)", code2 == 422)

    # ---- A05 版本列表（无请求体 GET 端点）----
    code3, body3 = RESUME_VERSIONS.dispatch({})  # 无请求体，跳过入参校验
    _check("无请求体版本列表 200 + 响应合规",
           code3 == 200 and isinstance(body3.get("versions"), list))
    # versionStub required 字段齐全 + diffAvailable 布尔
    v0 = body3["versions"][0] if body3.get("versions") else {}
    _check("A05 versionStub 必填字段齐全",
           all(k in v0 for k in
               ("versionId", "versionNo", "createdAt", "isPreferred")))
    _check("A05 diffAvailable 为布尔", isinstance(body3.get("diffAvailable"), bool))

    # ---- A06 触发 ATS 评分 ----
    code4, body4 = RESUME_ATS.dispatch({"resumeVersionId": "RV-demo-001"})
    _check("合法触发 ATS 200 + status 在枚举内",
           code4 == 200 and body4.get("taskId")
           and body4.get("status") in ("pending", "running", "done", "failed"))

    code5, _ = RESUME_ATS.dispatch({})  # 缺 resumeVersionId
    _check("非法触发 ATS(缺 resumeVersionId) 422(fail-closed)", code5 == 422)

    # ---- 注册表按 id 分发 ----
    code6, _ = API_STUB.dispatch_id("A04 resumes-create",
                                    {"title": "x", "content": {}})
    _check("注册表分发 A04 -> 200", code6 == 200)

    code7, _ = API_STUB.dispatch_id("A05 resumes-versions", {})
    _check("注册表分发 A05 -> 200", code7 == 200)

    code8, _ = API_STUB.dispatch_id("A06 resumes-ats",
                                    {"resumeVersionId": "RV-demo-001"})
    _check("注册表分发 A06 -> 200", code8 == 200)

    _check("注册表含 A04/A05/A06 三端点",
           set(API_STUB.endpoint_ids()) >=
           {"A04 resumes-create", "A05 resumes-versions", "A06 resumes-ats"})


def main():
    print("=== scaffold 冒烟测试 ===")
    try:
        test_contract_runtime()
        test_event_bus()
        test_api_stub()
        test_api_stub_jobs()
        test_api_stub_user()
        test_api_stub_resume()
    except AssertionError as e:
        print(f"\n冒烟测试失败：{e}")
        traceback.print_exc()
        sys.exit(1)
    print("\n全部冒烟测试通过 ✅")


if __name__ == "__main__":
    main()
