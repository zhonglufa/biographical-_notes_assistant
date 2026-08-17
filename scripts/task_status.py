#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
task_status.py —— 自主任务机制的状态回看 CLI（零依赖，仅标准库）。

用法：
    python scripts/task_status.py queue     # 列出任务队列（按状态分组）
    python scripts/task_status.py log [N]   # 最近 N 条运行日志（默认 15）
    python scripts/task_status.py alerts    # 列出待拍板/已闭环告警
    python scripts/task_status.py health    # 总体健康：文件存在性 + 计数 + 末次运行

设计目标：让「状态回传 / 日志与告警」人机可读，用户没空时也能事后一眼看清。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "TASK-QUEUE.md")
ALERTS = os.path.join(ROOT, "TASK-ALERTS.md")
LOG = os.path.join(ROOT, "TASK-LOG.md")


def _parse_rows(text):
    """返回队列/告警表格数据行（去掉表头与图例），每行是清洗后的单元格列表。"""
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|") and re.search(r"待办|进行中|已完成|阻塞|待拍板|已闭环", s):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 2 and cells[0] and cells[0] != "ID":
                rows.append(cells)
    return rows


def _read(path):
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def _hr(title):
    print("=" * 60)
    print(title)
    print("=" * 60)


def cmd_queue():
    text = _read(QUEUE)
    if not text:
        print("[queue] TASK-QUEUE.md 不存在")
        return
    # 抓取表格行（| ID | ... | 状态 | ...）
    rows = []
    for line in text.splitlines():
        if line.strip().startswith("|") and re.search(r"待办|进行中|已完成|阻塞", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and cells[0] and cells[0] != "ID":
                rows.append(cells)
    print(text.split("---")[0].strip())  # 顶部说明
    _hr("任务队列（状态分组）")
    buckets = {}
    for r in rows:
        # 状态列：所有队列表（待办/阻塞）均为「… | 状态 | 备注」结构，状态恒为倒数第二格。
        status = r[-2] if len(r) >= 2 else "未知"
        buckets.setdefault(status, []).append(r)
    for status in ["待办", "进行中", "已完成", "阻塞(待用户拍板)", "阻塞(物理动作·用户)"]:
        items = buckets.get(status, [])
        print(f"\n◆ [{status}] {len(items)} 项")
        for r in items:
            # 阶段=倒数第三格，备注=最后一格（兼容待办表多一列「角色」的偏移）
            stage = r[-3] if len(r) >= 3 else (r[2] if len(r) > 2 else "")
            note = r[-1] if len(r) >= 2 else ""
            print(f"   - {r[0]} | {r[1]} | 阶段={stage}" + (f" | {note}" if note else ""))


def cmd_log(n=15):
    text = _read(LOG)
    if not text:
        print("[log] TASK-LOG.md 不存在")
        return
    entries = re.split(r"\n## \[", text)
    # 第一个元素是头部说明；其余以 "[" 还原
    blocks = []
    for i, e in enumerate(entries):
        if i == 0:
            continue
        blocks.append("## [" + e.rstrip())
    blocks = blocks[-n:]
    _hr(f"运行日志（最近 {len(blocks)} 条）")
    for b in blocks:
        # 仅打印标题行 + 前 3 行摘要，避免刷屏
        lines = b.splitlines()
        print("\n" + lines[0])
        for ln in lines[1:4]:
            print("   " + ln)
        if len(lines) > 4:
            print(f"   …（共 {len(lines)} 行，详见 TASK-LOG.md）")


def cmd_alerts():
    text = _read(ALERTS)
    if not text:
        print("[alerts] TASK-ALERTS.md 不存在")
        return
    _hr("告警与待决（需你拍板）")
    # 抓取表格行
    for line in text.splitlines():
        if line.strip().startswith("|") and re.search(r"待拍板|已闭环", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[0] and not cells[0].startswith("ID"):
                tag = cells[0]
                status = cells[-1]
                body = cells[1] if len(cells) > 1 else ""
                print(f" - {tag} [{status}] {body}")


def cmd_health():
    _hr("机制健康自检")
    for name, path in [("队列", QUEUE), ("告警", ALERTS), ("日志", LOG)]:
        ok = os.path.exists(path)
        print(f"   {'✅' if ok else '❌'} {name}文件 {os.path.basename(path)}: {'存在' if ok else '缺失'}")
    # 计数（仅统计真实表格数据行，排除图例/表头）
    q_rows = _parse_rows(_read(QUEUE))
    a_rows = _parse_rows(_read(ALERTS))
    l = _read(LOG)
    # 状态列：所有队列表均为「… | 状态 | 备注」，状态恒为倒数第二格（兼容待办表多一列「角色」）。
    q_pending = sum(1 for r in q_rows if len(r) >= 2 and "待办" in r[-2])
    q_blocked = sum(1 for r in q_rows if len(r) >= 2 and "阻塞" in r[-2])
    a_open = sum(1 for r in a_rows if "待拍板" in r[-1])
    a_closed = sum(1 for r in a_rows if "已闭环" in r[-1])
    log_runs = len(re.findall(r"^## \[", l, re.M))
    print(f"\n   队列: 待办 {q_pending} / 阻塞 {q_blocked}")
    print(f"   告警: 待拍板 {a_open} / 已闭环 {a_closed}")
    print(f"   日志: 累计运行 {log_runs} 条")
    # 末次运行时间
    m = re.search(r"^## \[([^\]]+)\]", l, re.M)
    if m:
        print(f"   末次运行: {m.group(1)}")
    print("\n   结论: 机制文件齐备 ✅；待拍板项请在 TASK-ALERTS.md 回答后由我沉淀规则。")


def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "health"
    if cmd == "queue":
        cmd_queue()
    elif cmd == "log":
        n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 15
        cmd_log(n)
    elif cmd == "alerts":
        cmd_alerts()
    elif cmd == "health":
        cmd_health()
    else:
        print("用法: task_status.py [queue|log|alerts|health]")
        sys.exit(2)


if __name__ == "__main__":
    main()
