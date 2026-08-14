#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRD ↔ HLD 追溯与对齐校验器（防漂移门禁）。

作用：
  1. 解析 PRD 顶层章节（## N. / ## C.）；
  2. 对每个 MUST_TRACE 技术章节，检查 HLD 中是否至少一处引用（PRD §N 或 §N，带数字边界）；
  3. 检查 HLD §1.2 需求追溯矩阵是否覆盖全部 MUST_TRACE 章节；
  4. 检查 HLD 头部引用的 PRD 版本是否与 PRD 实际版本漂移；
  5. 对 OUT_OF_SCOPE 章节，检查是否在 §1.2 显式登记（防"沉默忽略"）。

退出码：0 = 通过；1 = 存在阻塞项（❌ 或版本漂移）。可接入 CI。

用法：
  python check_prd_hld_traceability.py [--prd PATH] [--hld PATH] [--prd-version vX.Y]
"""

import re
import sys
import os
import argparse

# ---------- 可调分类（与 PRD-HLD-对齐规范.md §7 保持一致） ----------
# HLD 必须追溯的技术/设计相关 PRD 章节
MUST_TRACE = {5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21,
              22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 34, 35}
# 产品/商业/背景类：HLD 不实现，但必须在 §1.2 显式标注"不在本档范围"
OUT_OF_SCOPE = {1, 2, 3, 4, 13, 14, 32, 33}
# 约束总览章节（PRD §C）
CONSTRAINT_SECTION = "C"

DEFAULT_PRD = "../prd/PRD-简历自动投递与面试模拟-最终版.md"
DEFAULT_HLD = "HLD-简历自动投递与面试模拟-概要设计.md"
DEFAULT_PRD_VERSION = "v4.5"


def parse_prd_sections(text):
    """返回 {num_or_C: title} 覆盖所有 ## N. 与 ## C. 顶层章节。"""
    sections = {}
    for m in re.finditer(r'^##\s+(\d+)\.\s+(.+?)\s*$', text, re.M):
        sections[int(m.group(1))] = m.group(2).strip()
    for m in re.finditer(r'^##\s+(C)\.\s+(.+?)\s*$', text, re.M):
        sections["C"] = m.group(2).strip()
    return sections


def count_citations(hld_text, n):
    """统计 HLD 中对 PRD §n 的引用次数（带数字边界，避免 §2 命中 §20）。"""
    # 形如 "PRD §23" / "PRD § 23" / "§23" / "§ 23"，且后面不紧跟数字（排除 §230）
    pat = r'(?:PRD\s*§\s*%s|§\s*%s)(?!\d)' % (n, n)
    return len(re.findall(pat, hld_text))


def extract_matrix_section(text):
    """抽取 HLD §1.2 需求追溯矩阵区域文本，到下一个 ## 为止。"""
    m = re.search(r'##\s*1\.2\s+需求追溯矩阵(.*?)(?=\n##\s)', text, re.S)
    if not m:
        return ""
    return m.group(1)


def matrix_mentions(matrix_text, n):
    """§1.2 矩阵中是否提及该章节（§N 或 PRD §N）。"""
    pat = r'(?:PRD\s*§\s*%s|§\s*%s)(?!\d)' % (n, n)
    return bool(re.search(pat, matrix_text))


def detect_hld_prd_version(hld_text):
    """从 HLD 头部提取其引用的 PRD 版本。"""
    m = re.search(r'PRD\s+(v[\d.]+)', hld_text)
    return m.group(1) if m else None


def detect_prd_version(prd_text):
    """从 PRD 头部提取实际版本（兜底：用参数）。"""
    m = re.search(r'v([\d.]+)\b', prd_text)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser(description="PRD↔HLD 追溯与对齐校验器")
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--prd", default=os.path.join(here, DEFAULT_PRD))
    ap.add_argument("--hld", default=os.path.join(here, DEFAULT_HLD))
    ap.add_argument("--prd-version", default=DEFAULT_PRD_VERSION)
    args = ap.parse_args()

    try:
        prd_text = open(args.prd, encoding="utf-8").read()
        hld_text = open(args.hld, encoding="utf-8").read()
    except FileNotFoundError as e:
        print("❌ 文件未找到:", e)
        sys.exit(1)

    prd_sections = parse_prd_sections(prd_text)
    matrix = extract_matrix_section(hld_text)

    print("=" * 64)
    print("PRD ↔ HLD 追溯与对齐校验")
    print("  PRD :", os.path.basename(args.prd))
    print("  HLD :", os.path.basename(args.hld))
    print("=" * 64)

    # ---- 覆盖检查 ----
    print("\n[1] MUST_TRACE 章节覆盖（HLD 须 ≥1 处引用）")
    print("-" * 64)
    blockers = []
    for n in sorted(MUST_TRACE):
        title = prd_sections.get(n, f"(PRD 未找到 §{n})")
        cnt = count_citations(hld_text, n)
        in_matrix = matrix_mentions(matrix, n)
        if cnt == 0:
            status = "❌ 缺失"
            blockers.append(n)
        elif not in_matrix:
            status = "⚠ 正文有引用但矩阵漏登"
        else:
            status = "✅"
        print(f"  §{n:<3} {status:<16} 引用={cnt:<3} 矩阵={'Y' if in_matrix else 'N':<3} | {title[:40]}")
    # 约束总览 C
    cnt_c = count_citations(hld_text, "C")
    in_matrix_c = matrix_mentions(matrix, "C")
    if cnt_c == 0:
        print(f"  §C   ❌ 缺失          引用={cnt_c:<3} 矩阵={'Y' if in_matrix_c else 'N':<3} | 核心约束总览")
        blockers.append("C")
    else:
        print(f"  §C   ✅               引用={cnt_c:<3} 矩阵={'Y' if in_matrix_c else 'N':<3} | 核心约束总览")

    # ---- OUT_OF_SCOPE 登记检查 ----
    print("\n[2] OUT_OF_SCOPE 章节是否显式登记（防沉默忽略）")
    print("-" * 64)
    for n in sorted(OUT_OF_SCOPE):
        title = prd_sections.get(n, f"(PRD 未找到 §{n})")
        mentioned = matrix_mentions(matrix, n)
        status = "✅ 已登记" if mentioned else "⚠ 未登记(建议补'不在本档范围')"
        print(f"  §{n:<3} {status:<22} | {title[:40]}")

    # ---- 版本漂移检查 ----
    print("\n[3] 版本耦合检查")
    print("-" * 64)
    hld_ver = (detect_hld_prd_version(hld_text) or "").lstrip("v")
    prd_ver = (detect_prd_version(prd_text) or args.prd_version).lstrip("v")
    print(f"  HLD 引用 PRD 版本 : {hld_ver}")
    print(f"  PRD 实际版本      : {prd_ver}  (参数/检测)")
    if hld_ver != prd_ver:
        print(f"  ❌ 版本漂移：HLD 头部的 PRD 版本 ({hld_ver}) ≠ PRD 实际 ({prd_ver})")
        blockers.append("VERSION")
    else:
        print("  ✅ 版本一致")

    # ---- 结论 ----
    print("\n" + "=" * 64)
    if blockers:
        print(f"❌ 校验未通过，阻塞项: {blockers}")
        print("   请补全 HLD 设计决策 + §1.2 矩阵行，或修正头部版本号后重跑。")
        print("=" * 64)
        sys.exit(1)
    else:
        print("✅ 校验通过：全部 MUST_TRACE 章节已追溯，版本一致。")
        print("=" * 64)
        sys.exit(0)


if __name__ == "__main__":
    main()
