"""敏感信息脱敏模块。

仅使用标准库正则，提供常见键 / 令牌 / 个人信息的遮蔽规则。
用户可以自定义规则追加到 REDACT_RULES。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class RedactRule:
    """一条脱敏规则。"""

    name: str
    pattern: re.Pattern
    replacement: str | Callable[[re.Match], str]

    def apply(self, text: str) -> str:
        return self.pattern.sub(self.replacement, text)


def _mask_keep_edges(m: re.Match, keep: int = 4) -> str:
    """保留首尾若干字符，中间用星号遮蔽。"""
    s = m.group(0)
    if len(s) <= keep * 2:
        return "*" * len(s)
    return s[:keep] + "*" * (len(s) - keep * 2) + s[-keep:]


REDACT_RULES: tuple[RedactRule, ...] = (
    # GitHub / OpenAI / 通用 Bearer 令牌
    RedactRule(
        "ghp_token",
        re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
        "[REDACTED_GHP_TOKEN]",
    ),
    RedactRule(
        "bearer_token",
        re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{16,}", re.IGNORECASE),
        "Bearer [REDACTED]",
    ),
    RedactRule(
        "api_key_kv",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd)"
            r"\s*[:=]\s*[\"']?([^\s\"',;]{6,})"
        ),
        lambda m: m.group(0) if m.group(2).startswith("[REDACTED") else f"{m.group(1)}=[REDACTED]",
    ),
    # 邮箱
    RedactRule(
        "email",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    # IPv4（保守处理，避免误伤版本号）
    RedactRule(
        "ipv4",
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "[REDACTED_IP]",
    ),
)


def redact(text: str, rules: tuple[RedactRule, ...] = REDACT_RULES) -> tuple[str, int]:
    """按规则脱敏，返回 (脱敏后文本, 命中次数)。"""
    hits = 0
    for rule in rules:
        new_text = rule.apply(text)
        if new_text != text:
            hits += 1
            text = new_text
    return text, hits
