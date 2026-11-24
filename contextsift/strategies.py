"""压缩策略集合。

每个策略实现 Strategy 协议：接收行列表，返回处理后的行列表。
策略之间可自由组合、按顺序执行，由 SiftEngine 负责编排。
所有策略均为纯函数式：不修改输入列表，返回新列表。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable

from .redact import REDACT_RULES, RedactRule, redact

# ANSI 转义序列（颜色、光标控制等）
_ANSI_RE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|[@-Z\\-_])"
)
# URL 中常见的 query token
_QUERY_SECRET_RE = re.compile(r"(?i)([?&](?:token|key|sig|signature|access_token)=)[^&#\s]+")


@dataclass(frozen=True)
class SiftContext:
    """策略执行上下文，携带全局信息。"""

    token_budget: int | None = None
    meta: dict | None = None

    def get(self, key: str, default=None):
        return (self.meta or {}).get(key, default)


LineList = list[str]


class Strategy:
    """策略基类。子类实现 apply_lines 或 apply_text。"""

    name: str = "base"
    description: str = ""

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 具体策略
# ---------------------------------------------------------------------------


class StripAnsi(Strategy):
    name = "strip-ansi"
    description = "移除 ANSI 颜色与控制转义序列"

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        return [_ANSI_RE.sub("", line) for line in lines]


class SqueezeBlank(Strategy):
    name = "squeeze-blank"
    description = "将连续空行压缩为单个空行"

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        out: LineList = []
        prev_blank = False
        for line in lines:
            blank = not line.strip()
            if blank and prev_blank:
                continue
            out.append(line)
            prev_blank = blank
        return out


class CollapseRepeats(Strategy):
    name = "collapse-repeats"
    description = "折叠连续重复行，标注重复次数"

    def __init__(self, min_run: int = 3, marker: str = "... (repeated {n}x)"):
        self.min_run = min_run
        self.marker = marker

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        if not lines:
            return []
        out: LineList = []
        run_line = lines[0]
        run_len = 1
        for line in lines[1:]:
            if line == run_line:
                run_len += 1
                continue
            out.extend(self._flush(run_line, run_len))
            run_line, run_len = line, 1
        out.extend(self._flush(run_line, run_len))
        return out

    def _flush(self, line: str, n: int) -> LineList:
        if n >= self.min_run:
            keep = max(1, self.min_run // 2)
            return [line] * keep + [self.marker.format(n=n)]
        return [line] * n


class DedupeLines(Strategy):
    name = "dedupe"
    description = "全局去重，保留首次出现顺序"

    def __init__(self, keep_last: int = 0):
        self.keep_last = keep_last

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        seen: set[str] = set()
        out: LineList = []
        for line in lines:
            if line in seen:
                continue
            seen.add(line)
            out.append(line)
        if self.keep_last and len(out) > self.keep_last:
            out = ["... (dedupe: omitted %d unique lines)" % (len(out) - self.keep_last)] + out[-self.keep_last:]
        return out


class StripNoise(Strategy):
    name = "strip-noise"
    description = "移除调试噪声行（可配置前缀）"

    DEFAULT_PREFIXES = ("DEBUG", "TRACE", "VERBOSE")

    def __init__(self, prefixes: Iterable[str] | None = None):
        self.prefixes = tuple(prefixes or self.DEFAULT_PREFIXES)

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        out = []
        for line in lines:
            stripped = line.lstrip()
            if any(stripped.startswith(p) for p in self.prefixes):
                continue
            out.append(line)
        return out


class TruncateLines(Strategy):
    name = "truncate-lines"
    description = "截断超长行并标注原始长度"

    def __init__(self, max_chars: int = 300, marker: str = " …[+{n} chars]"):
        self.max_chars = max_chars
        self.marker = marker

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        out = []
        for line in lines:
            if len(line) > self.max_chars:
                cut = self.max_chars
                out.append(line[:cut] + self.marker.format(n=len(line) - cut))
            else:
                out.append(line)
        return out


class HeadTail(Strategy):
    name = "head-tail"
    description = "仅保留开头与结尾，中间用摘要替代"

    def __init__(self, head: int = 20, tail: int = 20):
        self.head = head
        self.tail = tail

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        total = len(lines)
        limit = self.head + self.tail
        if total <= limit:
            return list(lines)
        omitted = total - limit
        return (
            lines[: self.head]
            + ["... (%d lines omitted by head-tail) ..." % omitted]
            + lines[-self.tail :]
        )


class MaxLines(Strategy):
    name = "max-lines"
    description = "限制最大行数，超出部分等距采样保留"

    def __init__(self, max_lines: int = 200):
        self.max_lines = max_lines

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        total = len(lines)
        if total <= self.max_lines:
            return list(lines)
        if self.max_lines <= 1:
            return lines[:1]
        step = total / self.max_lines
        picked = [lines[int(i * step)] for i in range(self.max_lines)]
        return ["... (sampled %d/%d lines by max-lines) ..." % (self.max_lines, total)] + picked


class RedactSecrets(Strategy):
    name = "redact"
    description = "脱敏令牌、密钥、邮箱、IP 等敏感信息"

    def __init__(self, rules: tuple[RedactRule, ...] = REDACT_RULES):
        self.rules = rules

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        out = []
        for line in lines:
            cleaned, _ = redact(line, self.rules)
            cleaned = _QUERY_SECRET_RE.sub(r"\1[REDACTED]", cleaned)
            out.append(cleaned)
        return out


class NumberLines(Strategy):
    name = "number-lines"
    description = "为每行添加行号，便于模型引用"

    def __init__(self, width: int = 4):
        self.width = width

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        return ["%*d| %s" % (self.width, i + 1, line) for i, line in enumerate(lines)]


class TokenBudget(Strategy):
    name = "token-budget"
    description = "按 token 预算渐进裁剪：先砍尾部，再压缩中段"

    def __init__(self, budget: int | None = None):
        self.budget = budget

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        from .stats import estimate_tokens

        budget = self.budget if self.budget is not None else ctx.token_budget
        if budget is None or budget <= 0:
            return list(lines)

        text = "\n".join(lines)
        if estimate_tokens(text) <= budget:
            return list(lines)

        # 二分查找可容纳的最大行数（保留头尾各 25%）
        lo, hi = 1, len(lines)
        best: LineList = [lines[0]] if lines else []
        while lo <= hi:
            mid = (lo + hi) // 2
            head = mid * 2 // 3
            tail = mid - head
            candidate = lines[:head] + (["... (trimmed by token-budget) ..."] if mid < len(lines) else []) + (lines[-tail:] if tail else [])
            if estimate_tokens("\n".join(candidate)) <= budget:
                best = candidate
                lo = mid + 1
            else:
                hi = mid - 1
        return best


class DropEmpty(Strategy):
    name = "drop-empty"
    description = "删除所有空行"

    def apply(self, lines: LineList, ctx: SiftContext) -> LineList:
        return [line for line in lines if line.strip()]


# ---------------------------------------------------------------------------
# 注册表
# ---------------------------------------------------------------------------

STRATEGIES: dict[str, Callable[..., Strategy]] = {
    "strip-ansi": StripAnsi,
    "squeeze-blank": SqueezeBlank,
    "collapse-repeats": CollapseRepeats,
    "dedupe": DedupeLines,
    "strip-noise": StripNoise,
    "truncate-lines": TruncateLines,
    "head-tail": HeadTail,
    "max-lines": MaxLines,
    "redact": RedactSecrets,
    "number-lines": NumberLines,
    "token-budget": TokenBudget,
    "drop-empty": DropEmpty,
}


def get_strategy(name: str, **kwargs) -> Strategy:
    """按名称构造策略实例。未知名称抛出 KeyError。"""
    if name not in STRATEGIES:
        raise KeyError(f"unknown strategy: {name}")
    return STRATEGIES[name](**kwargs)


def list_strategies() -> list[dict]:
    """列出所有策略的元信息。"""
    return [
        {"name": s.name, "description": s.description}
        for s in (cls() for cls in STRATEGIES.values())
    ]
