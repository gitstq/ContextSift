<div align="center">

# ContextSift

**Zero-dependency, offline-first engine for smart CLI output compaction and context slimming**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](pyproject.toml)

[简体中文](README.md) · [繁體中文](README_zh-TW.md) · [English](README_EN.md)

</div>

---

## 🎉 Introduction

Turn long, messy command-line output into concise text that language models can read — fast.

In day-to-day development, `git diff`, build logs, and test output easily run into thousands of lines, riddled with color codes, repeated warnings, secrets, and irrelevant noise. Feeding all of that into an AI coding assistant burns tokens and buries the signal. **ContextSift** was built to fix exactly that:

> It is a compression engine written in **pure Python standard library** — no network, no installs, no uploads. It does one thing: apply composable "sift" strategies to shrink text to just enough, then tell you how many tokens you saved.

Use it as a library inside your toolchain or as a command-line utility in a pipeline. The design takes inspiration from the industry idea of "compacting command output to save LLM tokens," but the implementation is entirely original, with differentiators in strategy composability, sensitive-data redaction, statistical reporting, and reproducibility.

---

## ✨ Features

- 🧩 **Composable strategies**: 12 compaction strategies (ANSI stripping, deduplication, repeat collapsing, truncation, head-tail retention, redaction, line limits, token budgeting, and more) that stack freely and run in order.
- 🎯 **Ready-made profiles**: five presets — `generic`, `git`, `test`, `build`, and `aggressive` — one command fits common scenarios.
- 🔐 **Privacy first**: automatically redacts tokens, keys, emails, and IP addresses so output is safe to share.
- 📊 **Visible stats**: line, character, and token counts before and after, plus the exact savings percentage.
- 🔒 **Zero-dependency, offline, deterministic**: standard library only, no network calls; identical input always yields identical output.
- 🪶 **Dual use**: both a Python library and a CLI — just run `python -m contextsift`.
- 🧪 **Well tested**: 36 unit tests cover every strategy and the core paths.

---

## 🚀 Quick Start

No dependencies to install — clone and go (Python 3.8+).

```bash
git clone https://github.com/gitstq/ContextSift.git
cd ContextSift

# Read from a pipe and compact with the generic profile
cat your-log.txt | python3 -m contextsift --profile generic --report text

# Compact git output
git diff | python3 -m contextsift -p git

# List all built-in profiles and strategies
python3 -m contextsift --list-profiles
python3 -m contextsift --list-strategies
```

Or use it as a library:

```python
from contextsift import SiftEngine

result = SiftEngine(profile="test").sift(raw_output)
print(result.text)           # compacted text
print(result.report("text")) # compression stats
```

---

## 📖 Usage Guide

### Command line

```bash
# Basics: file input / stdin
contextsift -p generic input.log
cat input.log | contextsift -p generic

# Append custom strategies (repeat -s; they run in the given order after the profile)
contextsift -p generic -s number-lines -s truncate-lines:max_chars=120 input.log

# Set a token budget; excess content is trimmed progressively
contextsift -p aggressive --token-budget 2000 big.log

# Write output to a file and print a JSON report to the terminal
contextsift -p git -o compact.txt --report json big.log
```

> 💡 **Strategy argument syntax**: `-s name:key=val,key2=val2`, e.g. `truncate-lines:max_chars=150`.

### Built-in strategies

| Strategy | Purpose |
| --- | --- |
| `strip-ansi` | Remove ANSI color and control escape sequences |
| `squeeze-blank` | Collapse runs of blank lines into one |
| `collapse-repeats` | Fold consecutive duplicate lines, annotated with a count |
| `dedupe` | Global deduplication, preserving first-seen order |
| `strip-noise` | Drop DEBUG / TRACE and other noisy lines |
| `truncate-lines` | Truncate long lines and note the original length |
| `head-tail` | Keep only the head and tail; summarize the middle |
| `max-lines` | Cap line count, sampling evenly when exceeded |
| `redact` | Redact tokens, keys, emails, IPs |
| `number-lines` | Prefix each line with its number for easy referencing |
| `token-budget` | Trim progressively to fit a token budget |
| `drop-empty` | Remove all blank lines |

### Library integration

```python
from contextsift import SiftEngine, get_strategy

# Option 1: use a preset profile
engine = SiftEngine(profile="build", token_budget=4000)
out = engine.sift(text)

# Option 2: assemble your own strategy chain from scratch
engine = SiftEngine(profile=None)
engine.add(get_strategy("strip-ansi"))
engine.add(get_strategy("collapse-repeats", min_run=2))
engine.add(get_strategy("redact"))
out = engine.sift(text)

# The result object
out.text             # compacted text
out.lines            # list of lines
out.stats.as_dict()  # statistics dictionary
out.report("json")   # JSON report
```

### Design iterations

The journey of ContextSift from 0 to 1 records the trade-offs at every step:

1. **v0.1 · Minimal viable**: only `strip-ansi` and `dedupe`, to validate the core hypothesis that compacting output really saves tokens.
2. **v0.3 · Strategy refactor**: abstracted hard-coded logic into a composable `Strategy` protocol, introduced engine orchestration, and enabled free strategy stacking.
3. **v0.6 · Scenario profiles**: distilled presets for real-world scenarios like git / test / build to lower the barrier to entry.
4. **v0.8 · Privacy boost**: added redaction rules and fixed the "key overwritten twice" issue, making output safe to share.
5. **v1.0 · Reproducibility & packaging**: unified deterministic semantics, completed 36 tests, a one-click build script, and trilingual docs — production ready.

Compared with similar tools, the differentiators are: **pure standard-library, zero dependencies**, **arbitrarily composable strategies**, **built-in privacy redaction**, **transparent, comparable stats**, and **fully offline, deterministic output**.

---

## 📦 Packaging & Deployment

### One-click build (archive + checksums)

```bash
python3 scripts/build.py
# produces under releases/:
#   contextsift-1.0.0.tar.gz
#   contextsift-1.0.0.zip
#   checksums.sha256
```

Verify archive integrity:

```bash
cd releases && sha256sum -c checksums.sha256
```

### Install as a CLI tool

```bash
pip install .
contextsift --version
```

### Deploy as a library

ContextSift is pure Python with no platform-specific dependencies. Drop the `contextsift/` directory into your project, or simply `pip install .`. Behavior is identical across Windows, macOS, and Linux.

> This project is a hybrid library + CLI, so no binary Release is published; see "Library integration" above for examples. Source archives include checksums for verification.

---

## 🤝 Contributing

Contributions are welcome! Two ground rules: **no runtime dependencies** and **keep it deterministic**. Commits follow the Angular convention (`feat` / `fix` / `docs` / `refactor` / `test` / `chore`), and `python3 -m unittest discover -s tests` must stay green. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

Released under the [MIT License](LICENSE) — free to use, modify, and distribute.

<div align="center">

Made with ❤️ by gitstq · Zero-dependency · Offline-first · Reproducible

</div>
