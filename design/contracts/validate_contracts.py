#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
契约校验器 (contract validator) — 零外部依赖，纯标准库。

校验 HLD §4.6 / §4.7 / §4.9 / §4.10 的接口契约是否自洽且可用：
  1) 所有 *.schema.json 为合法 JSON（可加载为对象）；
  2) samples.json 中的「正向样本」全部通过校验、「反向样本」全部失败（证伪）；
  3) 注册表文件（error-codes.json / agent-server-rpc.methods.json）经各自 schema 自洽校验；
  4) 错误码注册表无重复 code，且 error-envelope 正向样本所用 code 均已登记。

退出码非 0 即 CI / pre-commit 钩子拦截本次提交。
支持 JSON Schema Draft 2020-12 子集：type/enum/const/required/properties/
additionalProperties/items/minItems/maxItems/minimum/maximum/exclusive*
/minLength/maxLength/pattern/format/$ref/$defs/anyOf/oneOf/allOf/not/
nullable(OpenAPI)。其余关键字（title/description/$id/$schema/default/...）忽略。
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


class SchemaError(Exception):
    """校验失败，携带 JSON 路径信息。"""


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_ref(root, ref):
    if not isinstance(ref, str) or not ref.startswith("#/"):
        raise SchemaError("仅支持文档内 $ref，收到: %r" % (ref,))
    node = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise SchemaError("无法解析 $ref: %s" % ref)
        node = node[part]
    return node


def type_matches(inst, t):
    if isinstance(t, list):
        return any(type_matches(inst, x) for x in t)
    if t == "string":
        return isinstance(inst, str)
    if t == "integer":
        return isinstance(inst, int) and not isinstance(inst, bool)
    if t == "number":
        return isinstance(inst, (int, float)) and not isinstance(inst, bool)
    if t == "boolean":
        return isinstance(inst, bool)
    if t == "object":
        return isinstance(inst, dict)
    if t == "array":
        return isinstance(inst, list)
    if t == "null":
        return inst is None
    return True


def validate(inst, schema, path="$", root=None):
    if root is None:
        root = schema
    if not isinstance(schema, dict):
        raise SchemaError("schema 节点非对象 @ %s" % path)
    # $ref 优先（始终相对文档根解析）
    if "$ref" in schema:
        return validate(inst, resolve_ref(root, schema["$ref"]), path, root)
    # nullable (OpenAPI 3.0)
    if schema.get("nullable") is True and inst is None:
        return
    # const
    if "const" in schema and inst != schema["const"]:
        raise SchemaError("%s: 期望 const %r，实际 %r" % (path, schema["const"], inst))
    # enum
    if "enum" in schema and inst not in schema["enum"]:
        raise SchemaError("%s: %r 不在 enum %r" % (path, inst, schema["enum"]))
    # type
    if "type" in schema and not type_matches(inst, schema["type"]):
        raise SchemaError("%s: 类型应为 %s，实际 %s" % (path, schema["type"], type(inst).__name__))
    # 组合
    if "allOf" in schema:
        for i, sub in enumerate(schema["allOf"]):
            validate(inst, sub, path + "/allOf[%d]" % i, root)
    if "anyOf" in schema:
        ok = False
        for i, sub in enumerate(schema["anyOf"]):
            try:
                validate(inst, sub, path + "/anyOf[%d]" % i, root)
                ok = True
                break
            except SchemaError:
                pass
        if not ok:
            raise SchemaError("%s: 未匹配 anyOf 任一分支" % path)
    if "oneOf" in schema:
        matched = 0
        for i, sub in enumerate(schema["oneOf"]):
            try:
                validate(inst, sub, path + "/oneOf[%d]" % i, root)
                matched += 1
            except SchemaError:
                pass
        if matched != 1:
            raise SchemaError("%s: oneOf 需恰好匹配 1 个，实际 %d" % (path, matched))
    if "not" in schema:
        try:
            validate(inst, schema["not"], path + "/not", root)
            raise SchemaError("%s: 不应匹配 not" % path)
        except SchemaError:
            pass
    # object 约束
    if isinstance(inst, dict):
        if "properties" in schema:
            for k, v in schema["properties"].items():
                if k in inst:
                    validate(inst[k], v, path + "." + k, root)
        for k in schema.get("required", []):
            if k not in inst:
                raise SchemaError("%s: 缺必需字段 %s" % (path, k))
        ap = schema.get("additionalProperties", True)
        allowed = set(schema.get("properties", {}).keys())
        if ap is False:
            for k in inst:
                if k not in allowed:
                    raise SchemaError("%s: 不允许额外字段 %s" % (path, k))
        elif isinstance(ap, dict):
            for k in inst:
                if k not in allowed:
                    validate(inst[k], ap, path + "." + k, root)
    # array 约束
    if isinstance(inst, list):
        if "items" in schema:
            for i, it in enumerate(inst):
                validate(it, schema["items"], path + "[%d]" % i, root)
        if "minItems" in schema and len(inst) < schema["minItems"]:
            raise SchemaError("%s: 数组长度 < minItems(%d)" % (path, schema["minItems"]))
        if "maxItems" in schema and len(inst) > schema["maxItems"]:
            raise SchemaError("%s: 数组长度 > maxItems(%d)" % (path, schema["maxItems"]))
    # 数值约束
    if isinstance(inst, (int, float)) and not isinstance(inst, bool):
        if "minimum" in schema and inst < schema["minimum"]:
            raise SchemaError("%s: < minimum(%s)" % (path, schema["minimum"]))
        if "maximum" in schema and inst > schema["maximum"]:
            raise SchemaError("%s: > maximum(%s)" % (path, schema["maximum"]))
        if "exclusiveMinimum" in schema and inst <= schema["exclusiveMinimum"]:
            raise SchemaError("%s: <= exclusiveMinimum(%s)" % (path, schema["exclusiveMinimum"]))
        if "exclusiveMaximum" in schema and inst >= schema["exclusiveMaximum"]:
            raise SchemaError("%s: >= exclusiveMaximum(%s)" % (path, schema["exclusiveMaximum"]))
    # 字符串约束
    if isinstance(inst, str):
        if "minLength" in schema and len(inst) < schema["minLength"]:
            raise SchemaError("%s: 长度 < minLength(%d)" % (path, schema["minLength"]))
        if "maxLength" in schema and len(inst) > schema["maxLength"]:
            raise SchemaError("%s: 长度 > maxLength(%d)" % (path, schema["maxLength"]))
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            raise SchemaError("%s: 不匹配 pattern %s" % (path, schema["pattern"]))
    # format 基础检查
    if schema.get("format") == "int64" and not isinstance(inst, int):
        raise SchemaError("%s: format int64 需为整数" % path)


def main():
    failures = []
    schema_files = sorted(glob.glob(os.path.join(ROOT, "*.schema.json")))
    schemas = {}
    for sf in schema_files:
        name = os.path.basename(sf)
        try:
            s = load_json(sf)
            validate(s, {"type": "object"})
            schemas[name] = s
        except Exception as e:  # noqa: BLE001
            failures.append("SCHEMA-LOAD %s: %s" % (name, e))

    samples = load_json(os.path.join(ROOT, "samples.json"))
    for sname, grp in samples.get("schemas", {}).items():
        if sname not in schemas:
            failures.append("SAMPLE-NO-SCHEMA %s" % sname)
            continue
        sch = schemas[sname]
        for v in grp.get("valid", []):
            try:
                validate(v, sch)
            except SchemaError as e:
                failures.append("VALID-FAIL %s: %s" % (sname, e))
        for item in grp.get("invalid", []):
            payload = item.get("payload", item)
            try:
                validate(payload, sch)
                failures.append("INVALID-PASS %s (reason=%s)" % (sname, item.get("reason", "")))
            except SchemaError:
                pass

    reg = samples.get("registryFiles", {})
    for data_name, schema_name in reg.items():
        if schema_name not in schemas:
            failures.append("REG-NO-SCHEMA %s -> %s" % (data_name, schema_name))
            continue
        try:
            validate(load_json(os.path.join(ROOT, data_name)), schemas[schema_name])
        except Exception as e:  # noqa: BLE001
            failures.append("REG-FAIL %s: %s" % (data_name, e))

    # 错误码注册表一致性
    try:
        ec = load_json(os.path.join(ROOT, "error-codes.json"))
        codes = [e["code"] for e in ec["registry"]]
        dups = sorted({c for c in codes if codes.count(c) > 1})
        if dups:
            failures.append("ERRORCODE-DUP %s" % dups)
        code_set = set(codes)
        for sname, grp in samples.get("schemas", {}).items():
            if "error-envelope" in sname:
                for v in grp.get("valid", []):
                    if v.get("code") not in code_set:
                        failures.append("ERRORCODE-UNREG %s in %s" % (v.get("code"), sname))
    except Exception as e:  # noqa: BLE001
        failures.append("ERRORCODE-CHECK %s" % e)

    print("=== 契约校验结果 ===")
    print("schema 文件: %d | 注册表: %d" % (len(schemas), len(reg)))
    if failures:
        print("❌ 失败 %d 项:" % len(failures))
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("✅ 全部通过 (schemas 可加载 / 正向样本通过 / 反向样本证伪 / 注册表自洽 / 错误码唯一且已登记)")
    sys.exit(0)


if __name__ == "__main__":
    main()
