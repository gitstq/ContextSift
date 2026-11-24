"""命令行界面。

支持从 stdin 或文件读取，输出到 stdout 或文件，可打印压缩报告。
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .core import SiftEngine
from .profiles import list_profiles
from .strategies import get_strategy, list_strategies


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="contextsift",
        description="CLI 输出智能压缩与上下文精简引擎（零依赖、离线优先）",
    )
    p.add_argument("file", nargs="?", help="输入文件；省略则从 stdin 读取")
    p.add_argument("-p", "--profile", default="generic", help="预设档位（默认 generic）")
    p.add_argument(
        "-s", "--strategy", action="append", default=[],
        help="追加策略，格式 name 或 name:key=val（可多次指定）",
    )
    p.add_argument("--token-budget", type=int, help="token 预算上限")
    p.add_argument("-o", "--output", help="输出文件；省略则写 stdout")
    p.add_argument("--report", choices=("none", "text", "json"), default="none", help="压缩报告格式")
    p.add_argument("--list-profiles", action="store_true", help="列出所有预设档位")
    p.add_argument("--list-strategies", action="store_true", help="列出所有策略")
    p.add_argument("-v", "--version", action="version", version=f"contextsift {__version__}")
    return p


def _parse_strategy(spec: str):
    """解析 name:key=val,key2=val2 为策略实例。"""
    parts = spec.split(":", 1)
    name = parts[0]
    kwargs: dict = {}
    if len(parts) == 2:
        for kv in parts[1].split(","):
            if "=" not in kv:
                continue
            k, v = kv.split("=", 1)
            if v.lower() in ("true", "false"):
                kwargs[k] = v.lower() == "true"
            else:
                try:
                    kwargs[k] = int(v)
                except ValueError:
                    kwargs[k] = v
    return get_strategy(name, **kwargs)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_profiles:
        import json

        print(json.dumps(list_profiles(), ensure_ascii=False, indent=2))
        return 0
    if args.list_strategies:
        import json

        print(json.dumps(list_strategies(), ensure_ascii=False, indent=2))
        return 0

    if args.file:
        with open(args.file, encoding="utf-8", errors="replace") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    extra = [_parse_strategy(s) for s in args.strategy]
    engine = SiftEngine(profile=args.profile, strategies=extra, token_budget=args.token_budget)
    result = engine.sift(text)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.text)
    else:
        sys.stdout.write(result.text)

    if args.report != "none":
        stream = sys.stderr if args.output else sys.stdout
        stream.write("\n" + result.report(args.report) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
