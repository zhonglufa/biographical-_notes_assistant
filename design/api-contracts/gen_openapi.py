# -*- coding: utf-8 -*-
"""
零依赖生成器：把 design/contracts/ 下的机器可读契约导出为 OpenAPI 3.1 文档 + Mock 示例。

输入（design/contracts/）：
  - external-api.registry.json        A 层（公共 REST，25 端点，outlined/fully-detailed）
  - ai-orchestrator.methods.json      B 层（内部 REST，b01-b05，机器可读 b0X schema）
  - interview-domain.methods.json     面试模拟域（内部 REST，6 facade 方法）
  - agent-server-rpc.methods.json     C 层（WSS RPC，仅 device/* 与 payment/callback 是 HTTP）
  - *.schema.json / *.event.schema.json  全部机器可读 schema（注册为 components.schemas）
  - samples.json                      正向/反向样本（用于 Mock 示例）
  - error-codes.json                  错误码注册表

输出：
  - openapi.json  （OpenAPI 3.1.0）
  - 生成后自检：所有 $ref 目标必须可解析，否则抛错。

约定：
  - 契约 schema 用 draft 2020-12（nullable + $defs）。转为 OAS 3.1 时：
      * nullable:true -> type 联合 ["X","null"]，删除 nullable
      * 内部 $ref "#/$defs/x" -> "#/components/schemas/<compName>/$defs/x"
  - A 层 operation 级 `x-contract-status` 取 registry `contractStatus`（2026-08-16 v3.29 后 A 层 25 端点全 fully-detailed，表示严格 JSON Schema 已落盘 design/contracts/ 并经双闸门校验）；内联 request/response body 仍由 registry 字段大纲 best-effort 生成（投影），**权威严格契约见各 operation 的 `x-ref` 指向 design/contracts/*.schema.json**。面试 facade / device 端点仍为 outlined 投影。
  - B 层直引机器可读 b0X schema（严格）。
  - WSS RPC 方法不放 HTTP paths，挂在 info.x-agent-rpc 扩展，供文档查阅。
"""
import json
import os
import re

CONTRACTS = os.path.join(os.path.dirname(__file__), "..", "contracts")
OUT = os.path.join(os.path.dirname(__file__), "openapi.json")


def load(name):
    with open(os.path.join(CONTRACTS, name), encoding="utf-8") as f:
        return json.load(f)


def comp_name_of(filename):
    """b01-match.request.schema.json -> b01-match-request（点统一转杠，避免 $ref 键不一致）"""
    base = filename
    if base.endswith(".schema.json"):
        base = base[: -len(".schema.json")]
    return base.replace(".", "-")


# ---------------------------------------------------------------------------
# 契约 schema 转换：nullable -> 联合类型；内部 $ref 改写
# ---------------------------------------------------------------------------
def transform_schema(obj, comp_name):
    if isinstance(obj, dict):
        if obj.get("nullable") is True:
            obj.pop("nullable", None)
            t = obj.get("type")
            if isinstance(t, list):
                if "null" not in t:
                    t.append("null")
                    obj["type"] = t
            elif isinstance(t, str):
                obj["type"] = [t, "null"]
            else:
                obj["type"] = ["null"]
        for k, v in list(obj.items()):
            if k == "$ref" and isinstance(v, str) and v.startswith("#/$defs/"):
                # "#/$defs/x" -> "#/components/schemas/<compName>/$defs/x"
                obj[k] = "#/components/schemas/%s/%s" % (comp_name, v[2:])
            else:
                transform_schema(v, comp_name)
    elif isinstance(obj, list):
        for it in obj:
            transform_schema(it, comp_name)
    return obj


# ---------------------------------------------------------------------------
# best-effort 字段大纲解析器（用于 outlined 端点）
# ---------------------------------------------------------------------------
def split_top(s):
    """按顶层逗号切分，忽略 () {} 内部逗号。"""
    res, depth, cur = [], 0, ""
    for ch in s:
        if ch in "({":
            depth += 1
        elif ch in ")}":
            depth -= 1
        if ch == "," and depth == 0:
            res.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        res.append(cur)
    return res


def parse_spec(spec):
    spec = spec.strip()
    m = re.match(r"^enum\((.+)\)$", spec)
    if m:
        return {"type": "string", "enum": [x.strip() for x in m.group(1).split("|")]}
    m = re.match(r"^(.+?)\[\]$", spec)
    if m:
        return {"type": "array", "items": parse_spec(m.group(1))}
    m = re.match(r"^\[(.+)\]$", spec, re.S)
    if m:
        inner = m.group(1).strip()
        if inner.startswith("{"):
            return {"type": "array", "items": parse_object_literal(inner)}
        return {"type": "array", "items": best_effort_type(inner)}
    if spec.startswith("{") and spec.endswith("}"):
        return parse_object_literal(spec)
    m = re.match(r"^(int|integer|float|number)\(([^)]*)\)$", spec)
    if m:
        base, rng = m.group(1), m.group(2)
        typ = "integer" if base in ("int", "integer") else "number"
        sch = {"type": typ}
        if ".." in rng:
            lo, hi = rng.split("..")
            try:
                if lo:
                    sch["minimum"] = float(lo)
            except ValueError:
                pass
            try:
                if hi and hi.upper() != "N":
                    sch["maximum"] = float(hi)
            except ValueError:
                pass
        if "maximum" not in sch and "minimum" not in sch:
            sch["description"] = "范围(%s)" % rng
        return sch
    m = re.match(r"^(string|str)\(([^)]*)\)$", spec)
    if m:
        return {"type": "string", "description": m.group(2)}
    if spec in ("int64", "long"):
        return {"type": "integer", "format": "int64"}
    if spec in ("string", "str"):
        return {"type": "string"}
    if spec in ("int", "integer"):
        return {"type": "integer"}
    if spec in ("float", "number", "double"):
        return {"type": "number"}
    if spec in ("bool", "boolean"):
        return {"type": "boolean"}
    if spec in ("void", "null"):
        return {"type": "null"}
    if spec in ("object", "obj"):
        return {"type": "object"}
    if spec == "interviewEvaluation":
        return {"$ref": "#/components/schemas/interview-evaluation"}
    if "|" in spec:
        return {"type": "string", "description": "one of: " + spec}
    return {"type": "string", "description": "(%s, outlined)" % spec}


def best_effort_type(name):
    return {"type": "object", "additionalProperties": True, "description": "%s (outlined)" % name}


def parse_object_literal(spec):
    inner = spec[1:-1].strip()
    props, required = {}, []
    for p in split_top(inner):
        p = p.strip()
        if not p:
            continue
        n, s, r = parse_field(p)
        props[n] = s
        if r:
            required.append(n)
    obj = {"type": "object", "properties": props, "additionalProperties": True}
    if required:
        obj["required"] = required
    return obj


def parse_field(token):
    optional = token.endswith("?")
    t = token[:-1] if optional else token
    if ":" in t:
        name, spec = t.split(":", 1)
    else:
        name, spec = t, "string"
    name, spec = name.strip(), spec.strip()
    return name, parse_spec(spec), (not optional)


def build_object_schema(fields, contract_status):
    props, required = {}, []
    for f in fields or []:
        n, s, r = parse_field(f)
        props[n] = s
        if r:
            required.append(n)
    obj = {
        "type": "object",
        "properties": props,
        "additionalProperties": True,
        "x-contract-status": contract_status,
    }
    if required:
        obj["required"] = required
    return obj


def dict_to_schema(d):
    props = {k: parse_spec(str(v)) for k, v in (d or {}).items()}
    obj = {"type": "object", "properties": props, "additionalProperties": True}
    if props:
        obj["required"] = list(props.keys())
    return obj


# ---------------------------------------------------------------------------
# 组件注册
# ---------------------------------------------------------------------------
def register_schemas(components):
    for fn in sorted(os.listdir(CONTRACTS)):
        if not (fn.endswith(".schema.json") or fn.endswith(".event.schema.json")):
            continue
        if fn == "error-codes.schema.json":
            continue
        obj = load(fn)
        name = comp_name_of(fn)
        transform_schema(obj, name)
        components[name] = obj
    # A 层 outlined 引用类型的轻量 stub（保证 $ref 可解析，标注未细化）
    stubs = {
        "job-stub": "岗位摘要（outlined，详见 HLD §4.2）",
        "job": "岗位详情（outlined，详见 HLD §4.2）",
        "hr-status": "HR 状态（outlined，详见 HLD §4.3）",
        "quota": "平台配额（outlined，详见 HLD §4.4）",
        "health-report": "适配器健康报告（outlined，详见 HLD §4.4）",
        "login-state": "登录态（outlined，详见 HLD §4.4）",
        "apply-result": "投递结果（outlined，详见 HLD §4.3）",
        "application-stub": "投递摘要（outlined，详见 HLD §4.3）",
        "notification": "通知（outlined，详见 HLD §4.6）",
        "question-sets": "题集列表（outlined，详见 HLD §6.16）",
    }
    for name, desc in stubs.items():
        components[name] = {
            "type": "object",
            "description": desc,
            "additionalProperties": True,
            "x-contract-status": "outlined",
        }
    # 错误码注册表（非 schema，挂 info.x-error-codes）


# ---------------------------------------------------------------------------
# 构建 paths
# ---------------------------------------------------------------------------
def add_error_response(responses):
    responses["default"] = {
        "description": "错误响应（统一错误信封 §4.7）",
        "content": {
            "application/json": {"schema": {"$ref": "#/components/schemas/error-envelope"}}
        },
    }


def build_a_layer(paths):
    ext = load("external-api.registry.json")
    for ep in ext["endpoints"]:
        op = {
            "operationId": "a.%s.%s" % (ep["id"], re.sub(r"[^a-zA-Z0-9]", "", ep["path"])),
            "summary": ep["purpose"],
            "tags": ["A 外部 API"],
            "x-auth": ep["auth"],
            "x-contract-status": ep["contractStatus"],
        }
        if ep.get("ref"):
            op["x-ref"] = ep["ref"]
        path = ep["path"]
        pp = re.findall(r"\{([^}]+)\}", path)
        if pp:
            op["parameters"] = [
                {"name": x, "in": "path", "required": True, "schema": {"type": "string"}}
                for x in pp
            ]
        if ep["method"] in ("POST", "PUT", "PATCH") and ep.get("requestFields"):
            op["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": build_object_schema(ep["requestFields"], ep["contractStatus"])
                    }
                },
            }
        responses = {}
        rf = ep.get("responseFields") or []
        if rf:
            items_field = next((f for f in rf if f.startswith("items")), None)
            if items_field:
                _, spec, _ = parse_field(items_field)
                item_schema = spec.get("items", best_effort_type("item"))
                sch = {
                    "type": "object",
                    "properties": {
                        "items": {"type": "array", "items": item_schema},
                        "total": {"type": "integer"},
                        "page": {"type": "integer"},
                        "pageSize": {"type": "integer"},
                    },
                    "required": ["items", "total", "page", "pageSize"],
                    "additionalProperties": True,
                }
                responses["200"] = {
                    "description": "成功（列表信封 §10 uniformEnvelope）",
                    "content": {"application/json": {"schema": sch}},
                }
            else:
                data = build_object_schema(rf, ep["contractStatus"])
                responses["200"] = {
                    "description": "成功（单项信封 §10 uniformEnvelope）",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {"data": data},
                                "required": ["data"],
                                "additionalProperties": True,
                            }
                        }
                    },
                }
        else:
            responses["200"] = {
                "description": "成功",
                "content": {
                    "application/json": {"schema": {"type": "object", "additionalProperties": True}}
                },
            }
        add_error_response(responses)
        op["responses"] = responses
        paths.setdefault(path, {})[ep["method"].lower()] = op


B_SEM = {"b01": "match", "b02": "questions", "b03": "evaluate", "b04": "optimize", "b05": "ats"}


def build_b_layer(paths, samples):
    ai = load("ai-orchestrator.methods.json")
    for m, info in ai["methods"].items():
        sem = B_SEM[m]
        op = {
            "operationId": "ai.%s.%s" % (m, sem),
            "summary": "B 层 AI 编排：%s（%s）" % (m, sem),
            "tags": ["B AI 编排（内部 REST）"],
            "x-sync": info["sync"],
            "x-timeoutMs": info["timeoutMs"],
            "x-degradeTo": info["degradeTo"],
            "x-transport": ai["transport"],
            "x-auth": ai["auth"],
            "x-basePath": ai["basePath"],
        }
        req_comp = "%s-%s-request" % (m, sem)
        resp_comp = "%s-%s-response" % (m, sem)
        op["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/%s" % req_comp}
                }
            },
        }
        ex_req = get_sample(samples, "%s-%s.request.schema.json" % (m, sem))
        ex_resp = get_sample(samples, "%s-%s.response.schema.json" % (m, sem))
        req_content = op["requestBody"]["content"]["application/json"]
        if ex_req is not None:
            req_content["examples"] = {"sample": {"value": ex_req}}
        responses = {
            "200": {
                "description": "成功（B 层严格契约）",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/%s" % resp_comp}
                    }
                },
            }
        }
        if ex_resp is not None:
            responses["200"]["content"]["application/json"]["examples"] = {
                "sample": {"value": ex_resp}
            }
        add_error_response(responses)
        op["responses"] = responses
        paths["%s/%s" % (ai["basePath"], sem)] = {"post": op}


IV_MAP = {
    "createSession": ("/internal/v1/interview/session", "post", []),
    "getNextQuestion": ("/internal/v1/interview/session/{sessionId}/question", "post", ["sessionId"]),
    "submitAnswer": ("/internal/v1/interview/session/{sessionId}/answer", "post", ["sessionId"]),
    "evaluateSession": ("/internal/v1/interview/session/{sessionId}/evaluate", "post", ["sessionId"]),
    "endSession": ("/internal/v1/interview/session/{sessionId}/end", "post", ["sessionId"]),
    "getReport": ("/internal/v1/interview/session/{sessionId}/report", "get", ["sessionId"]),
}


def build_interview(paths, samples):
    iv = load("interview-domain.methods.json")
    for meth, info in iv["facadeMethods"].items():
        path, http, pp = IV_MAP[meth]
        op = {
            "operationId": "interview.%s" % meth,
            "summary": "面试域：%s" % meth,
            "tags": ["面试模拟域（内部 REST）"],
            "x-sync": info["sync"],
            "x-timeoutMs": info["timeoutMs"],
            "x-degradeTo": info["degradeTo"],
            "x-basePath": iv["basePath"],
            "description": "会话状态机：%s；rubric：%s；ASR 降级链：%s"
            % (
                " -> ".join(
                    ["%s(%s)" % (t["from"], t["to"]) for t in iv["sessionStateMachine"]["transitions"]]
                ),
                "/".join(iv["rubric"]["dimensions"]),
                " -> ".join(iv["asr"]["degradeChain"]),
            ),
        }
        if pp:
            op["parameters"] = [
                {"name": x, "in": "path", "required": True, "schema": {"type": "string"}}
                for x in pp
            ]
        if info.get("request"):
            op["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": build_object_schema(info["request"], "outlined")
                    }
                },
            }
        responses = {}
        if info.get("response"):
            data = build_object_schema(info["response"], "outlined")
            responses["200"] = {
                "description": "成功（面试域 outlined 契约）",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"data": data},
                            "required": ["data"],
                            "additionalProperties": True,
                        }
                    }
                },
            }
        else:
            responses["200"] = {
                "description": "成功",
                "content": {
                    "application/json": {"schema": {"type": "object", "additionalProperties": True}}
                },
            }
        if meth == "getReport":
            ex = get_sample(samples, "interview-evaluation.schema.json")
            if ex is not None:
                responses["200"]["content"]["application/json"]["examples"] = {
                    "sample": {"value": {"data": ex}}
                }
        add_error_response(responses)
        op["responses"] = responses
        paths.setdefault(path, {})[http] = op


def build_device(paths):
    rpc = load("agent-server-rpc.methods.json")
    eps = list(rpc["deviceEndpoints"]) + [rpc["handshake"], rpc["paymentCallback"]]
    for e in eps:
        op = {
            "operationId": "rpc.%s" % re.sub(r"[^a-zA-Z0-9]", ".", e["path"].strip("/")),
            "summary": "C 层设备/握手/支付回调端点（WSS 之外少数 HTTP 端点）",
            "tags": ["C 设备与支付（HTTP）"],
            "x-transport": rpc["transport"],
        }
        if e.get("auth"):
            op["x-auth"] = e["auth"]
        op["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": dict_to_schema(e.get("request"))}},
        }
        op["responses"] = {
            "200": {
                "description": "成功",
                "content": {"application/json": {"schema": dict_to_schema(e.get("response"))}},
            }
        }
        add_error_response(op["responses"])
        paths.setdefault(e["path"], {})[e["method"].lower()] = op


# ---------------------------------------------------------------------------
# 示例取样
# ---------------------------------------------------------------------------
def get_sample(samples, filename):
    try:
        return samples["schemas"].get(filename, {}).get("valid", [None])[0]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 自检：所有 $ref 必须可解析
# ---------------------------------------------------------------------------
def resolve_pointer(doc, ptr):
    node = doc
    for part in ptr.lstrip("#/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            node = node[int(part)]
        else:
            if part not in node:
                return False
            node = node[part]
    return True


def self_check(doc):
    refs = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "$ref" and isinstance(v, str):
                    refs.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for it in o:
                walk(it)

    walk(doc)
    bad = []
    for r in refs:
        if not (r.startswith("#/") and resolve_pointer(doc, r)):
            bad.append(r)
    if bad:
        raise SystemExit("DANGLING $ref:\n" + "\n".join(bad))
    return len(refs)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    samples = load("samples.json")
    components = {}
    register_schemas(components)

    paths = {}
    build_a_layer(paths)
    build_b_layer(paths, samples)
    build_interview(paths, samples)
    build_device(paths)

    err = load("error-codes.json")

    doc = {
        "openapi": "3.1.0",
        "info": {
            "title": "简历自动投递与面试模拟 - API 契约（OpenAPI 3.1）",
            "version": "1.0.0",
            "description": (
                "由 design/contracts/ 机器可读契约自动导出（生成器：api-contracts/gen_openapi.py）。\n\n"
                "## 分层\n"
                "- **A 层（外部 API）**：公共 REST，basePath /api/v1，25 个端点（A01-A25）。严格机器可读 schema 已落盘 design/contracts/（request/response *.schema.json）并经双闸门校验（registry `contractStatus=fully-detailed`）。本文件为**概览投影视图**：内联 request/response body 由 registry 字段大纲 best-effort 生成（标 `x-contract-status` 仅表示投影粒度），**权威严格契约见各 operation 的 `x-ref` 指向 design/contracts/ 真实 schema**。\n"
                "- **B 层（AI 编排）**：内部 REST /internal/v1/ai，b01-b05 直引机器可读 b0X schema（严格）。\n"
                "- **面试模拟域**：内部 REST /internal/v1/interview，6 个 facade 方法（outlined）。\n"
                "- **C 层（本机 Agent↔服务端）**：WSS RPC，本文件仅收录 device/* 与 payments/callback 等少数 HTTP 端点；双向 RPC 方法见下方 x-agent-rpc。\n\n"
                "## 信封\n"
                "- 统一错误信封：components.schemas/error-envelope（§4.7）\n"
                "- 事件信封：event-envelope（§4.6）；RPC 信封：rpc-envelope（§4.9）\n\n"
                "## Mock\n"
                "本文件即为 Mock 数据源：`npx @stoplight/prism mock -s openapi.json`。"
            ),
            "x-error-codes": err["registry"],
            "x-agent-rpc": {
                "transport": load("agent-server-rpc.methods.json")["transport"],
                "heartbeatSec": load("agent-server-rpc.methods.json")["heartbeatSec"],
                "envelopes": {"rpc": "rpc-envelope", "event": "event-envelope"},
                "serverToAgent": load("agent-server-rpc.methods.json")["rpcMethods"]["serverToAgent"],
                "agentToServer": load("agent-server-rpc.methods.json")["rpcMethods"]["agentToServer"],
            },
        },
        "servers": [
            {"url": "https://api.example.com", "description": "A 层（外部 API）根；实际 basePath 见各 path"},
            {"url": "http://internal-gateway:8080", "description": "B/C 层（内部）根"},
        ],
        "paths": paths,
        "components": {"schemas": components},
    }

    n_refs = self_check(doc)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("OK openapi.json written:", OUT)
    print("paths:", sum(len(v) for v in paths.values()), " operations:",
          sum(len(m) for m in paths.values()))
    print("components.schemas:", len(components))
    print("$ref resolved (self-check):", n_refs)


if __name__ == "__main__":
    main()
