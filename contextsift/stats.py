"""Token 估算模块。

零依赖的启发式估算器：不加载任何 tokenizer，纯标准库实现。
设计取舍：
- ASCII / 拉丁文本：约每 4 个字符 1 个 token；
- CJK（中日韩）字符：约每 1 个字符 1~1.5 个 token；
- 数字与标点密集文本略作上调。
该估算不追求与特定模型完全一致，只求稳定、可复现、可比。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


# 常见 CJK 统一表意文字区间（含扩展 A）
_CJK_RE = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]"
)
_WS_RE = re.compile(r"\s+")


def is_cjk(ch: str) -> bool:
    """判断单个字符是否属于 CJK 文字。"""
    return bool(_CJK_RE.match(ch))


def char_token_weight(ch: str) -> float:
    """返回单字符的 token 权重估计。"""
    if is_cjk(ch):
        return 1.0
    if ch.isspace():
        return 0.0
    if unicodedata.category(ch).startswith("P"):
        return 0.35
    return 0.25  # 约 4 字符 = 1 token


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量，返回非负整数。

    示例：
        >>> estimate_tokens("hello world")
        3
        >>> estimate_tokens("你好世界") > 0
        True
    """
    if not text:
        return 0
    total = sum(char_token_weight(ch) for ch in text)
    # 换行与空白虽单独权重为 0，但 token 化时仍有边界开销，按词数补偿
    words = len(_WS_RE.split(text.strip()))
    return max(0, int(round(total + words * 0.25)))


@dataclass(frozen=True)
class TokenDelta:
    """压缩前后的 token 变化。"""

    before: int
    after: int

    @property
    def saved(self) -> int:
        return max(0, self.before - self.after)

    @property
    def saved_pct(self) -> float:
        if self.before == 0:
            return 0.0
        return round(self.saved / self.before * 100, 1)

    def as_dict(self) -> dict:
        return {
            "tokens_before": self.before,
            "tokens_after": self.after,
            "tokens_saved": self.saved,
            "saved_pct": self.saved_pct,
        }
