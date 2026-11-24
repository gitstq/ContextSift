"""ContextSift — 零依赖、离线优先的 CLI 输出智能压缩与上下文精简引擎。

本包只使用 Python 标准库，可在任何 Python 3.8+ 环境中离线运行。
设计目标：在不丢失关键信息的前提下，压缩命令 / 日志输出，降低
送入大语言模型（LLM）的 token 消耗。
"""

from .core import SiftEngine, SiftResult, SiftStats, SiftContext
from .strategies import STRATEGIES, get_strategy, list_strategies
from .profiles import PROFILES, get_profile, list_profiles
from .stats import estimate_tokens

__version__ = "1.0.0"
__all__ = [
    "SiftEngine",
    "SiftResult",
    "SiftStats",
    "SiftContext",
    "STRATEGIES",
    "get_strategy",
    "list_strategies",
    "PROFILES",
    "get_profile",
    "list_profiles",
    "estimate_tokens",
    "__version__",
]
