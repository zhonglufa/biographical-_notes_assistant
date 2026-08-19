#!/usr/bin/env python3
# DPIRA 状态驱动 CLI（零依赖：仅标准库）
# 用法见 DPIRA.md §5。状态存于仓库根 DPIRA-STATE.json（纳入 git，本地不 push 外）。
import json, os, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(ROOT, "DPIRA-STATE.json")

BATCH_PHASES = ["DEFINING", "PLAN_REVIEW", "IMPLEMENTING", "AUDITING", "DONE"]
ITEM_STATES = ["TODO", "IN_PROGRESS", "DRAFT_REVIEW", "DRAFT_COMPLETE"]
AUDIT_RESULTS = ["PASS", "FAIL_A_I", "FAIL_A_DP"]

DEFAULT_STATE = {
    "batch_id": "DPIRA-BATCH-001",
    "batch_phase": "DEFINING",
    "created_at": "",
    "updated_at": "",
    "items": {
        "W1": {"state": "TODO", "title": "Flyway MySQL 真实迁移闭环", "role": "Eng"},
        "W2": {"state": "TODO", "title": "验证并提交在途工作", "role": "Eng+QA"},
        "W3": {"state": "TODO", "title": "本地全栈运行时实证", "role": "Eng+QA"},
        "W4": {"state": "TODO", "title": "上线手册阶段二", "role": "Docs+Arch"},
        "W5": {"state": "TODO", "title": "QA 上线前全量验证", "role": "QA"},
        "W6": {"state": "TODO", "title": "push→PR→gates绿→合并master", "role": "Lead"},
    },
    "audit": {"result": None, "note": "", "at": ""},
}


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(st):
    st["updated_at"] = now()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


def init(batch_id):
    if os.path.exists(STATE_FILE):
        print(f"[warn] {STATE_FILE} 已存在，跳过 init（如需重置请先删除该文件）")
        return
    st = dict(DEFAULT_STATE)
    st["batch_id"] = batch_id
    st["created_at"] = now()
    st["updated_at"] = now()
    save(st)
    print(f"[ok] 初始化批次 {batch_id} -> {STATE_FILE}")


def status():
    st = load()
    if not st:
        print("[err] 状态文件不存在，请先运行 init")
        return
    print(f"批次: {st['batch_id']}  阶段: {st['batch_phase']}")
    print(f"创建: {st['created_at']}  更新: {st['updated_at']}")
    print("-" * 60)
    all_done = True
    for k, v in st["items"].items():
        flag = "OK" if v["state"] == "DRAFT_COMPLETE" else "  "
        if v["state"] != "DRAFT_COMPLETE":
            all_done = False
        print(f"  [{flag}] {k}  {v['state']:<14} ({v['role']})  {v['title']}")
    print("-" * 60)
    a = st["audit"]
    print(f"审计: result={a['result']}  at={a['at']}  note={a['note'] or '-'}")
    if st["batch_phase"] == "AUDITING" and all_done:
        print("[info] 全部工作项 DRAFT_COMPLETE，可进入 A（批级审计）")
    elif all_done and st["batch_phase"] != "DONE":
        print("[info] 全部工作项 DRAFT_COMPLETE，建议 phase AUDITING")


def set_phase(phase):
    st = load()
    if not st:
        print("[err] 请先 init"); return
    if phase not in BATCH_PHASES:
        print(f"[err] 非法阶段 {phase}，可选: {BATCH_PHASES}"); return
    st["batch_phase"] = phase
    save(st)
    print(f"[ok] 批次阶段 -> {phase}")


def set_item(item, state):
    st = load()
    if not st:
        print("[err] 请先 init"); return
    if item not in st["items"]:
        print(f"[err] 未知工作项 {item}，可选: {list(st['items'].keys())}"); return
    if state not in ITEM_STATES:
        print(f"[err] 非法状态 {state}，可选: {ITEM_STATES}"); return
    st["items"][item]["state"] = state
    save(st)
    print(f"[ok] {item} -> {state}")


def audit(result, note):
    st = load()
    if not st:
        print("[err] 请先 init"); return
    if result not in AUDIT_RESULTS:
        print(f"[err] 非法审计结果 {result}，可选: {AUDIT_RESULTS}"); return
    st["audit"] = {"result": result, "note": note, "at": now()}
    if result == "PASS":
        st["batch_phase"] = "DONE"
    elif result == "FAIL_A_I":
        st["batch_phase"] = "IMPLEMENTING"  # A↩I
    elif result == "FAIL_A_DP":
        st["batch_phase"] = "DEFINING"      # A↺D/P
    save(st)
    print(f"[ok] 审计结果={result} 回路={('A↩I' if result=='FAIL_A_I' else 'A↺D/P' if result=='FAIL_A_DP' else '完成')}  note={note}")


def snapshot():
    st = load()
    if not st:
        print("[err] 请先 init"); return
    print(json.dumps(st, ensure_ascii=False, indent=2))


def usage():
    print(__doc__)


def main():
    argv = sys.argv[1:]
    if not argv:
        usage(); return
    cmd = argv[0]
    if cmd == "init" and len(argv) >= 2:
        init(argv[1])
    elif cmd == "status":
        status()
    elif cmd == "phase" and len(argv) >= 2:
        set_phase(argv[1])
    elif cmd == "item" and len(argv) >= 3:
        set_item(argv[1], argv[2])
    elif cmd == "audit" and len(argv) >= 2:
        note = argv[2] if len(argv) >= 3 else ""
        audit(argv[1], note)
    elif cmd == "snapshot":
        snapshot()
    else:
        usage()


if __name__ == "__main__":
    main()
