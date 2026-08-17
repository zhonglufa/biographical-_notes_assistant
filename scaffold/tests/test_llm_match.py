"""test_llm_match.py — LLM 匹配 + 成本护栏单测（B2-3 · 护栏2核心）"""
from base import check
from llm_match import MockLLM, CostGuard, MatchService, CostGuardOpen, DEFAULT_DAILY_CAP_CENTS


class FailingLLM:
    def complete(self, prompt: str):
        raise RuntimeError("llm down")


def main():
    # 正常匹配
    g = CostGuard()
    svc = MatchService(MockLLM(), g)
    band, score, cost = svc.match("资深Java高级工程师", "招聘Java高级工程师")
    check("high 匹配", band == "high" and score > 0.9)
    check("成本已记账", g.remaining_cents() == DEFAULT_DAILY_CAP_CENTS - 10)
    check("失败计数已清零", g._failures == 0)

    # 失败熔断：连续失败达阈值 → 开闸 → 后续调用被拦
    g2 = CostGuard(failure_threshold=3)
    svc2 = MatchService(FailingLLM(), g2)
    for _ in range(3):
        try:
            svc2.match("r", "j")
        except Exception:
            pass
    check("熔断已开", g2.is_open)
    blocked = False
    try:
        svc2.match("r", "j")
    except CostGuardOpen:
        blocked = True
    check("熔断后调用抛 CostGuardOpen", blocked)

    # 超日硬上限
    g3 = CostGuard(daily_cap_cents=25)  # 每次 10 分，仅够 2 次
    svc3 = MatchService(MockLLM(), g3, cost_per_call_cents=10)
    svc3.match("r", "j")
    svc3.match("r", "j")
    check("接近上限未开闸", not g3.is_open)
    over = False
    try:
        svc3.match("r", "j")
    except CostGuardOpen:
        over = True
    check("超日硬上限抛 CostGuardOpen", over)

    print("test_llm_match OK")


if __name__ == "__main__":
    main()
