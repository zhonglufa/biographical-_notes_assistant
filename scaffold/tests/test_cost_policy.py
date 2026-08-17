"""test_cost_policy.py — LLM 预算策略单测（C1 · 护栏2装配）"""
from base import check
from cost_policy import BudgetPolicy, DEMO_DAILY_CAP_CENTS
from llm_match import MockLLM, CostGuardOpen


def main():
    p = BudgetPolicy()
    svc = p.build_match_service(MockLLM())
    band, score, cost = svc.match("资深Java高级工程师", "招聘Java高级工程师")
    check("policy 装配后可匹配", band == "high")
    check("policy 未开闸", not p.is_open())
    check("剩余=默认上限-10", p.remaining_cents() == DEMO_DAILY_CAP_CENTS - 10)

    d = p.as_dict()
    check("摘要含日上限", d["daily_cap_cents"] == DEMO_DAILY_CAP_CENTS)
    check("摘要含熔断阈值", d["breaker_threshold"] == 5)
    check("摘要 circuit_open=False", d["circuit_open"] is False)

    # 超帽触发开闸（护栏 2 可度量落地）：cap=15、单call=10 → 第 2 次即超帽
    p2 = BudgetPolicy(daily_cap_cents=15, per_call_cents=10)
    svc2 = p2.build_match_service(MockLLM())
    svc2.match("r", "j")  # 成功，spent=10
    over = False
    try:
        svc2.match("r", "j")  # 10+10=20 > 15 -> 开闸
    except CostGuardOpen:
        over = True
    check("超帽开闸抛错", over)
    check("policy2 已开闸", p2.is_open())

    print("test_cost_policy OK")


if __name__ == "__main__":
    main()
