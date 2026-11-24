"""预设压缩档位。

每个 profile 是一组有序策略配置，针对不同命令输出场景。
用户可在 profile 基础上追加自定义策略。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    steps: tuple[tuple[str, dict], ...]  # (策略名, 参数)


PROFILES: dict[str, Profile] = {
    "generic": Profile(
        "generic",
        "通用场景：清理控制符、压缩空白与重复行、脱敏、超长行截断",
        (
            ("strip-ansi", {}),
            ("squeeze-blank", {}),
            ("collapse-repeats", {"min_run": 3}),
            ("redact", {}),
            ("truncate-lines", {"max_chars": 300}),
        ),
    ),
    "git": Profile(
        "git",
        "Git 输出：保留 diff 结构，折叠重复、脱敏、限制行数",
        (
            ("strip-ansi", {}),
            ("squeeze-blank", {}),
            ("collapse-repeats", {"min_run": 4}),
            ("redact", {}),
            ("max-lines", {"max_lines": 300}),
        ),
    ),
    "test": Profile(
        "test",
        "测试日志：去噪声、折叠重复、保留首尾、脱敏",
        (
            ("strip-ansi", {}),
            ("strip-noise", {"prefixes": ("DEBUG", "TRACE")}),
            ("collapse-repeats", {"min_run": 3}),
            ("redact", {}),
            ("head-tail", {"head": 40, "tail": 40}),
        ),
    ),
    "build": Profile(
        "build",
        "构建日志：去 ANSI、折叠重复警告、截断长行、脱敏",
        (
            ("strip-ansi", {}),
            ("squeeze-blank", {}),
            ("collapse-repeats", {"min_run": 3}),
            ("redact", {}),
            ("truncate-lines", {"max_chars": 240}),
            ("head-tail", {"head": 30, "tail": 30}),
        ),
    ),
    "aggressive": Profile(
        "aggressive",
        "激进压缩：全局去重、删空行、限制行数、脱敏、token 预算",
        (
            ("strip-ansi", {}),
            ("drop-empty", {}),
            ("dedupe", {}),
            ("redact", {}),
            ("max-lines", {"max_lines": 120}),
            ("token-budget", {}),
        ),
    ),
}


def get_profile(name: str) -> Profile:
    """按名称获取 profile，未知名称抛出 KeyError。"""
    if name not in PROFILES:
        raise KeyError(f"unknown profile: {name}")
    return PROFILES[name]


def list_profiles() -> list[dict]:
    """列出所有 profile 元信息。"""
    return [
        {"name": p.name, "description": p.description, "steps": [s[0] for s in p.steps]}
        for p in PROFILES.values()
    ]
