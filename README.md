<div align="center">

# ContextSift

**零依赖 · 离线优先的 CLI 输出智能压缩与上下文精简引擎**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](pyproject.toml)

[简体中文](README.md) · [繁體中文](README_zh-TW.md) · [English](README_EN.md)

</div>

---

## 🎉 介绍

把冗长、杂乱的命令行输出，变成大模型看得懂、看得快的精简文本。

在日常开发里，`git diff`、构建日志、测试输出动辄上千行，夹杂着颜色控制符、重复告警、密钥和无关噪声。把这些内容原样丢给 AI 编程助手，不仅烧 token，还会淹没真正重要的信息。**ContextSift** 就是为了解决这个问题而生：

> 它是一个**纯 Python 标准库**实现的压缩引擎，不联网、不装包、不上传数据，只做一件事——用可组合的「筛」策略，把文本压缩到刚好够用的程度，并告诉你能省下多少 token。

它既可以作为库嵌入你的工具链，也可以作为命令行工具直接管道使用。设计上参考了业界"压缩命令输出以节省 LLM token"的产品思路，但完全自研实现，并在策略可组合性、敏感信息脱敏、统计报告和可复现性上做了差异化。

---

## ✨ 特性

- 🧩 **可组合策略**：12 种压缩策略（去色、去重、折叠重复、截断、头尾保留、脱敏、行数限制、token 预算等），自由叠加、按顺序执行。
- 🎯 **开箱档位**：内置 `generic` / `git` / `test` / `build` / `aggressive` 五种预设，一行命令适配常见场景。
- 🔐 **隐私优先**：自动脱敏令牌、密钥、邮箱、IP 地址，输出可安全分享。
- 📊 **所见即所得的统计**：实时给出压缩前后的行数、字符数、token 数与节省比例。
- 🔒 **零依赖、离线、确定性**：仅用标准库，无网络请求；相同输入永远得到相同输出。
- 🪶 **轻量双用**：既是 Python 库，也是命令行工具，`python -m contextsift` 即可运行。
- 🧪 **测试完备**：36 个单元测试覆盖全部策略与核心路径。

---

## 🚀 快速开始

无需安装依赖，克隆即用（要求 Python 3.8+）。

```bash
git clone https://github.com/gitstq/ContextSift.git
cd ContextSift

# 从管道读取，使用通用档位压缩
cat your-log.txt | python3 -m contextsift --profile generic --report text

# 压缩 git 输出
git diff | python3 -m contextsift -p git

# 查看所有内置档位与策略
python3 -m contextsift --list-profiles
python3 -m contextsift --list-strategies
```

也可作为库直接用：

```python
from contextsift import SiftEngine

result = SiftEngine(profile="test").sift(raw_output)
print(result.text)           # 压缩后的文本
print(result.report("text")) # 压缩统计
```

---

## 📖 使用指南

### 命令行

```bash
# 基本用法：文件输入 / 标准输入
contextsift -p generic input.log
cat input.log | contextsift -p generic

# 追加自定义策略（可多次 -s，按给定顺序在档位之后执行）
contextsift -p generic -s number-lines -s truncate-lines:max_chars=120 input.log

# 设置 token 预算，超出则渐进裁剪
contextsift -p aggressive --token-budget 2000 big.log

# 写入文件并单独输出 JSON 报告到终端
contextsift -p git -o compact.txt --report json big.log
```

> 💡 **策略参数语法**：`-s name:key=val,key2=val2`，例如 `truncate-lines:max_chars=150`。

### 内置策略一览

| 策略名 | 作用 |
| --- | --- |
| `strip-ansi` | 移除 ANSI 颜色与控制转义序列 |
| `squeeze-blank` | 连续空行压成单个 |
| `collapse-repeats` | 折叠连续重复行并标注次数 |
| `dedupe` | 全局去重，保留首次出现顺序 |
| `strip-noise` | 移除 DEBUG / TRACE 等噪声行 |
| `truncate-lines` | 超长行截断并标注原始长度 |
| `head-tail` | 只保留开头和结尾，中间用摘要替代 |
| `max-lines` | 限制最大行数，超出等距采样 |
| `redact` | 脱敏令牌、密钥、邮箱、IP |
| `number-lines` | 为每行加行号，便于模型引用 |
| `token-budget` | 按 token 预算渐进裁剪 |
| `drop-empty` | 删除所有空行 |

### 作为库集成

```python
from contextsift import SiftEngine, get_strategy

# 方式一：使用预设档位
engine = SiftEngine(profile="build", token_budget=4000)
out = engine.sift(text)

# 方式二：从零组装自己的策略链
engine = SiftEngine(profile=None)
engine.add(get_strategy("strip-ansi"))
engine.add(get_strategy("collapse-repeats", min_run=2))
engine.add(get_strategy("redact"))
out = engine.sift(text)

# 结果对象
out.text             # 压缩后文本
out.lines            # 行列表
out.stats.as_dict()  # 统计字典
out.report("json")   # JSON 报告
```

### 设计迭代

ContextSift 从 0 到 1 的演进，记录了每一步的取舍：

1. **v0.1 · 最小可用**：只有 `strip-ansi` 与 `dedupe`，验证"压缩输出确实能省 token"的核心假设。
2. **v0.3 · 策略化重构**：把硬编码逻辑抽象成可组合的 `Strategy` 协议，引入引擎编排，支持策略自由叠加。
3. **v0.6 · 场景档位**：针对 git / test / build 等真实场景沉淀出预设档位，降低使用门槛。
4. **v0.8 · 隐私增强**：加入脱敏规则，修复"密钥被二次覆盖"的问题，让输出可安全分享。
5. **v1.0 · 可复现与打包**：统一确定性语义，补齐 36 个测试、一键打包脚本与三语文档，达到生产可用。

与同类工具相比，差异点在于：**纯标准库零依赖**、**策略可任意组合**、**内置隐私脱敏**、**透明可比的统计报告**，以及**完全离线、确定性输出**。

---

## 📦 打包部署

### 一键打包（生成归档 + 校验和）

```bash
python3 scripts/build.py
# 产出 releases/ 下：
#   contextsift-1.0.0.tar.gz
#   contextsift-1.0.0.zip
#   checksums.sha256
```

校验归档完整性：

```bash
cd releases && sha256sum -c checksums.sha256
```

### 安装为命令行工具

```bash
pip install .
contextsift --version
```

### 作为库部署

ContextSift 是纯 Python 库，无平台相关依赖，把 `contextsift/` 目录放进项目即可，或直接 `pip install .`。跨平台（Windows / macOS / Linux）行为一致。

> 本项目是库 + CLI 混合形态，不做二进制 Release；集成示例见上方「作为库集成」。源码归档附有校验和可供核验。

---

## 🤝 贡献

欢迎贡献！请遵守两条底线：**不引入运行时依赖**、**保持确定性**。提交遵循 Angular 规范（`feat` / `fix` / `docs` / `refactor` / `test` / `chore`），并确保 `python3 -m unittest discover -s tests` 全绿。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📄 协议

本项目采用 [MIT License](LICENSE)，可自由使用、修改与分发。

<div align="center">

Made with ❤️ by gitstq · 零依赖 · 离线优先 · 可复现

</div>
