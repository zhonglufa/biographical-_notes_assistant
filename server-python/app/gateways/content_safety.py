"""ai/content_safety.py — 内容安全层接缝（HLD §6.11 B6 / §26.4）

所有 AI 输出经内容安全审核：政治敏感 / 违法 / 歧视 / 骚扰 / 鼓励造假。
本环境为「接缝」：默认放行（无真实审核模型），暴露 check() 接口供生产接入真实过滤器。
硬指标（golden set 歧视命中=0）在接入真实模型后由测试覆盖；此处不伪造审核结果。
"""
from __future__ import annotations


class ContentSafety:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def check(self, text: str) -> tuple[bool, str | None]:
        """返回 (是否通过, 不通过原因)。默认放行。

        enabled=False 时同样放行（仅用于测试隔离），真实接入时改为调用审核模型。
        """
        if not self.enabled:
            return True, None
        # TODO(seam): 接入真实内容安全模型/规则引擎；命中即返回 (False, reason)
        return True, None
