"""ai/rule_engine.py — 三级降级链的最终兜底（LLD §2 / §5）

当主/备 LLM 均不可达时，按 HLD §6.11 B5 锚定的规则层产出可用结果：
- b01 → rule_engine：技能40 / 行业20 / 城市20 / 经验20（可被子请求 weights 覆盖）
- b02 → question_bank：基于 JD 关键词的固定题库模板
- b03 → advise：不评分式启发反馈（仍给综合分与逐维 rubric）
- b04 → template：模板化占位改写（明确标注未做语义优化）
- b05 → score_skip：启发式 ATS 分 + 结构建议（契约要求 atsScore 必填，故返回启发值）

全部返回与对应 response schema 同形状、可被机器 schema 校验通过的 dict（model/status 标识来源）。
确定性、无外部依赖、可单测 —— 是「降级优先、防生产事故」的核心保障。
"""
from __future__ import annotations

import math
import re
import uuid

# 行业关键词（用于规则层行业匹配维度）
_INDUSTRY_KW = [
    "互联网", "金融", "银行", "保险", "证券", "教育", "医疗", "健康", "制造", "工业",
    "电商", "零售", "物流", "供应链", "人工智能", "机器学习", "数据", "大数据", "云计算",
    "游戏", "文娱", "媒体", "广告", "营销", "咨询", "法律", "房地产", "能源", "汽车",
]
# 城市关键词（用于城市匹配维度）
_CITY_KW = [
    "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "西安", "苏州",
    "重庆", "天津", "长沙", "青岛", "厦门", "东莞", "宁波", "无锡", "佛山", "合肥",
]

_CJK = "一-鿿"  # \u4e00-\u9fff


def _tokenize(text: str) -> list[str]:
    """英文/数字词 + 中文整串 + 中文 2-gram，过滤长度<2。"""
    if not text:
        return []
    raw = re.findall(r"[a-zA-Z0-9]+|[" + _CJK + "]+", text.lower())
    out: list[str] = []
    for t in raw:
        out.append(t)
        if len(t) >= 2 and re.search("[" + _CJK + "]", t):
            for i in range(len(t) - 1):
                out.append(t[i:i + 2])
    return [t for t in out if len(t) >= 2]


def _extract_years(text: str) -> int:
    """从文本提取「最大工作年限」数字（如 '5年经验' -> 5）。"""
    if not text:
        return 0
    nums = [int(m) for m in re.findall(r"(\d{1,2})\s*年", text)]
    return max(nums) if nums else 0


def _keyword_hit(text: str, keywords: list[str]) -> set[str]:
    return {k for k in keywords if k in (text or "")}


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def rule_match(jd: str, resume: str, weights: dict | None = None) -> dict:
    """b01 规则兜底：返回 b01-match.response 形状（model='rule'）。"""
    jd_tok = set(_tokenize(jd))
    rs_tok = set(_tokenize(resume))

    # 技能维度：JD 要求中被简历覆盖的比例（recall）
    jd_meaningful = {t for t in jd_tok if len(t) >= 2}
    shared = jd_meaningful & rs_tok
    if jd_meaningful:
        skill_score = _clamp01(len(shared) / len(jd_meaningful))
    else:
        skill_score = 0.0
    matched_skills = sorted(shared, key=lambda t: (-len(t), t))[:12]

    ind_jd = _keyword_hit(jd, _INDUSTRY_KW)
    ind_rs = _keyword_hit(resume, _INDUSTRY_KW)
    if ind_jd & ind_rs:
        industry_score = 1.0
    elif ind_jd:
        industry_score = 0.6
    else:
        industry_score = 0.3

    city_jd = _keyword_hit(jd, _CITY_KW)
    city_rs = _keyword_hit(resume, _CITY_KW)
    if city_jd & city_rs:
        city_score = 1.0
    elif city_jd:
        city_score = 0.5
    else:
        city_score = 0.3

    rs_years = _extract_years(resume)
    jd_years = _extract_years(jd)
    if jd_years == 0:
        exp_score = 1.0 if rs_years >= 1 else 0.4
    else:
        exp_score = _clamp01(rs_years / jd_years)

    # 权重：子请求 weights(skill/jobtitle/exp) 覆盖；否则用 LLD 默认 40/20/20/20
    if weights and any(weights.get(k) is not None for k in ("skill", "jobtitle", "exp")):
        w_skill = weights.get("skill") or 0.0
        w_industry = weights.get("jobtitle") or 0.0  # jobtitle 维度映射到行业
        w_exp = weights.get("exp") or 0.0
        total = w_skill + w_industry + w_exp
        if total <= 0:
            w_skill, w_industry, w_exp = 0.4, 0.2, 0.2
            w_city = 0.2
        else:
            w_city = max(0.0, 1.0 - total)
            s = w_skill + w_industry + w_exp + w_city
            w_skill, w_industry, w_exp, w_city = (w_skill / s, w_industry / s, w_exp / s, w_city / s)
    else:
        w_skill, w_industry, w_city, w_exp = 0.4, 0.2, 0.2, 0.2

    score = _clamp01(skill_score * w_skill + industry_score * w_industry
                     + city_score * w_city + exp_score * w_exp)
    score = round(score, 4)

    explanation = (
        f"规则引擎匹配（降级）：技能覆盖 {skill_score:.2f}、行业 {industry_score:.2f}、"
        f"城市 {city_score:.2f}、经验 {exp_score:.2f}；权重 "
        f"技能{w_skill:.2f}/行业{w_industry:.2f}/城市{w_city:.2f}/经验{w_exp:.2f}。"
    )
    return {
        "score": score,
        "matchedSkills": matched_skills,
        "explanation": explanation,
        "model": "rule",
        "elapsedMs": 0,
    }


# ---- b02 question_bank ----
_BEHAVIOR_Q = [
    "请描述你在上一份工作中遇到的最具挑战性的项目，以及你是如何推进并化解风险的？",
    "讲一个你与跨职能团队协作出现分歧的例子，你是如何达成共识的？",
    "分享一次你主动承担职责之外工作的经历，结果如何？",
]
_TECH_Q = [
    "请结合你最熟悉的技术栈，说明你在其中解决过的一个性能或稳定性问题。",
    "针对你简历中的某个项目，请描述其整体架构与关键设计权衡。",
    "你如何保证代码质量与可维护性？请举具体实践。",
]
_CASE_Q = [
    "假设线上出现一类突发高并发请求导致服务抖动，请给出你的排查与处置思路。",
    "如果要在两周内交付一个你不完全熟悉领域的 MVP，你会如何规划？",
    "给出一个你用数据驱动决策、提升业务指标的实际案例。",
]


def question_bank(jd: str, resume: str, count: int, lang: str = "zh") -> dict:
    """b02 题库兜底：基于固定模板生成 count 道题（behavior/tech/case 轮换）。"""
    count = max(1, min(20, int(count)))
    pools = {"behavior": _BEHAVIOR_Q, "tech": _TECH_Q, "case": _CASE_Q}
    order = ["behavior", "tech", "case"]
    questions = []
    for i in range(count):
        qtype = order[i % len(order)]
        base = pools[qtype][(i // len(order)) % len(pools[qtype])]
        questions.append({
            "id": uuid.uuid4().hex[:12],
            "text": base,
            "type": qtype,
        })
    return {
        "questionSetId": uuid.uuid4().hex,
        "questions": questions,
    }


# ---- b03 advise ----
_DEFAULT_DIMS = ["完整性", "技术准确性", "结构化表达", "岗位匹配度", "逻辑性"]


def advise(question_id: str, answer: str, rubric_dims: list[str] | None = None) -> dict:
    """b03 兜底：不依赖 LLM 的启发式评估（仍给综合分 + 逐维 rubric + 反馈）。"""
    dims = rubric_dims or _DEFAULT_DIMS
    length = len(answer or "")
    # 结构化标记：数字/条目/分段
    has_number = bool(re.search(r"\d", answer or ""))
    has_bullet = bool(re.search(r"[\n;；]|\d+\.", answer or ""))
    coherence = _clamp01((length / 200.0))  # 长度近似完整性
    accuracy = _clamp01(0.5 + (0.3 if has_number else 0) + (0.2 if has_bullet else 0))
    structure = _clamp01(0.4 + (0.3 if has_bullet else 0) + (0.3 if length > 80 else 0))
    match = _clamp01(0.5 + (0.2 if has_number else 0) + (0.3 if length > 120 else 0))
    logic = _clamp01(0.5 + (0.25 if has_bullet else 0) + (0.25 if length > 100 else 0))
    per_dim = {
        "完整性": coherence, "技术准确性": accuracy, "结构化表达": structure,
        "岗位匹配度": match, "逻辑性": logic,
    }
    rubric = [{"dim": d, "score": round(_clamp01(per_dim.get(d, 0.5)), 4)} for d in dims]
    avg = round(sum(r["score"] for r in rubric) / max(1, len(rubric)), 4)
    feedback = (
        f"规则兜底评估（未调用 LLM）：回答约 {length} 字，"
        f"{'含量化/结构化要素' if (has_number or has_bullet) else '建议补充量化与结构化表述'}；"
        f"综合分 {avg}。"
    )
    return {"score": avg, "rubric": rubric, "feedback": feedback}


# ---- b04 template ----
def template_optimize(resume: str, target: str) -> dict:
    """b04 模板兜底：明确标注未做语义优化，返回单条变更（契约要求 changes 非空）。"""
    optimized = (resume or "") + f"\n\n[模板占位：LLM 不可用，未做语义优化；优化目标={target}]"
    changes = [{
        "field": "__notice__",
        "from": "",
        "to": f"LLM 不可用，退回模板占位；优化目标={target}，请在 LLM 恢复后重试",
    }]
    return {"optimized": optimized, "changes": changes}


# ---- b05 score_skip ----
_SECTION_KW = ["教育", "工作", "项目", "技能", "经历", "实习", "获奖", "证书"]


def score_skip_ats(resume: str) -> dict:
    """b05 兜底：启发式 ATS 分 + 结构建议（契约要求 atsScore 必填，故返回启发值）。"""
    text = resume or ""
    present = [s for s in _SECTION_KW if s in text]
    length_score = _clamp01(len(text) / 800.0)
    section_score = _clamp01(len(present) / len(_SECTION_KW))
    ats = round(_clamp01(0.6 * section_score + 0.4 * length_score) * 100, 2)
    suggestions = []
    if len(present) < 4:
        suggestions.append({"section": "结构完整性", "hint": "建议补充教育/工作/项目/技能等核心板块"})
    if length_score < 0.6:
        suggestions.append({"section": "内容充实度", "hint": "简历内容偏短，建议补充量化项目成果"})
    if not suggestions:
        suggestions.append({"section": "通用", "hint": "LLM 不可用，退回启发式评分；建议补充关键词匹配岗位 JD"})
    return {"atsScore": ats, "suggestions": suggestions}
