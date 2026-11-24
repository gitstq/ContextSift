"""核心引擎：编排策略、统计、结果封装。

设计原则：
- 确定性：相同输入 + 相同配置 => 完全相同输出；
- 离线：不发起任何网络请求；
- 零依赖：仅使用 Python 标准库。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .profiles import PROFILES, Profile, get_profile
from .stats import TokenDelta, estimate_tokens
from .strategies import SiftContext, Strategy, get_strategy


@dataclass(frozen=True)
class SiftStats:
    """压缩统计。"""

    lines_before: int
    lines_after: int
    chars_before: int
    chars_after: int
    tokens: TokenDelta
    strategies: tuple[str, ...] = field(default_factory=tuple)

    @property
    def line_saved_pct(self) -> float:
        if self.lines_before == 0:
            return 0.0
        return round((1 - self.lines_after / self.lines_before) * 100, 1)

    def as_dict(self) -> dict:
        return {
            "lines_before": self.lines_before,
            "lines_after": self.lines_after,
            "line_saved_pct": self.line_saved_pct,
            "chars_before": self.chars_before,
            "chars_after": self.chars_after,
            "strategies": list(self.strategies),
            **self.tokens.as_dict(),
        }


@dataclass(frozen=True)
class SiftResult:
    """一次压缩的结果。"""

    text: str
    stats: SiftStats

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines()

    def report(self, fmt: str = "text") -> str:
        """生成可读报告。fmt 支持 text / json。"""
        d = self.stats.as_dict()
        if fmt == "json":
            import json

            return json.dumps(d, ensure_ascii=False, indent=2)
        lines = [
            "ContextSift report",
            "  lines   : %(lines_before)d -> %(lines_after)d (%(line_saved_pct)s%% saved)" % d,
            "  chars   : %(chars_before)d -> %(chars_after)d" % d,
            "  tokens  : %(tokens_before)d -> %(tokens_after)d (%(saved_pct)s%% saved)" % d,
            "  applied : %s" % (", ".join(d["strategies"]) or "(none)"),
        ]
        return "\n".join(lines)


class SiftEngine:
    """压缩引擎。

    用法：
        engine = SiftEngine(profile="test")
        result = engine.sift(text)
        print(result.text)
    """

    def __init__(
        self,
        profile: str | None = "generic",
        strategies: list[Strategy] | None = None,
        token_budget: int | None = None,
        meta: dict | None = None,
    ):
        self._strategies: list[Strategy] = []
        if profile:
            p: Profile = get_profile(profile)
            for step_name, params in p.steps:
                self._strategies.append(get_strategy(step_name, **params))
        if strategies:
            self._strategies.extend(strategies)
        self._ctx = SiftContext(token_budget=token_budget, meta=meta or {})

    def add(self, strategy: Strategy) -> "SiftEngine":
        """追加一个策略，支持链式调用。"""
        self._strategies.append(strategy)
        return self

    @property
    def strategies(self) -> tuple[str, ...]:
        return tuple(s.name for s in self._strategies)

    def sift(self, text: str) -> SiftResult:
        """对文本执行压缩，返回 SiftResult。"""
        before_lines = text.splitlines()
        before_chars = len(text)
        before_tokens = estimate_tokens(text)

        lines = list(before_lines)
        applied: list[str] = []
        for strategy in self._strategies:
            lines = strategy.apply(lines, self._ctx)
            applied.append(strategy.name)

        out_text = "\n".join(lines)
        if text.endswith("\n") and lines:
            out_text += "\n"

        stats = SiftStats(
            lines_before=len(before_lines),
            lines_after=len(lines),
            chars_before=before_chars,
            chars_after=len(out_text),
            tokens=TokenDelta(before_tokens, estimate_tokens(out_text)),
            strategies=tuple(applied),
        )
        return SiftResult(out_text, stats)
