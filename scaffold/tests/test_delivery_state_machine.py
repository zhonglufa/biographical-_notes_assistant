"""test_delivery_state_machine.py — 10 态机单测（B2-2）"""
from base import check
from delivery_state_machine import DeliveryStateMachine, InvalidTransition


def main():
    # 全链路：pending_confirm -> ... -> closed
    sm = DeliveryStateMachine()
    tid = "T1"
    sm.create(tid)
    check("初始态 pending_confirm", sm.state(tid) == "pending_confirm")
    for nxt in ["autofilling", "submitted", "viewed", "contacting",
                "interview_invited", "interview_done", "offer", "closed"]:
        sm.transition(tid, nxt)
    check("终态 closed", sm.state(tid) == "closed")

    # 非法转移（回退边不允许）
    sm2 = DeliveryStateMachine()
    sm2.create("T2")
    bad = False
    try:
        sm2.transition("T2", "submitted")  # pending_confirm -> submitted 非法
    except InvalidTransition:
        bad = True
    check("非法转移抛错", bad)

    # 终态不可再转
    term = False
    try:
        sm.transition(tid, "rejected")  # closed 终态
    except InvalidTransition:
        term = True
    check("终态再转抛错", term)

    # 自环不允许
    sm3 = DeliveryStateMachine()
    sm3.create("T3")
    sm3.transition("T3", "autofilling")
    self_loop = False
    try:
        sm3.transition("T3", "autofilling")
    except InvalidTransition:
        self_loop = True
    check("自环抛错", self_loop)

    # 幂等四元组键
    k = DeliveryStateMachine.idempotency_key("u1", "boss", "j1", "2026-08-17")
    check("幂等键格式", k == "u1|boss|j1|2026-08-17")

    # 审计日志
    check("审计条数=8", len(sm.audit(tid)) == 8)
    print("test_delivery_state_machine OK")


if __name__ == "__main__":
    main()
