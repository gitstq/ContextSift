<div align="center">

# ContextSift

**零依賴 · 離線優先的 CLI 輸出智慧壓縮與脈絡精簡引擎**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](pyproject.toml)

[简体中文](README.md) · [繁體中文](README_zh-TW.md) · [English](README_EN.md)

</div>

---

## 🎉 介紹

把冗長雜亂的命令列輸出，轉成大型語言模型看得懂、看得快的精簡文字。

在日常開發裡，`git diff`、建置日誌、測試輸出動輒上千行，還夾雜著顏色控制碼、重複警示、金鑰與無關雜訊。把這些內容原封不動丟給 AI 程式助手，不只燒 token，還會把真正重要的資訊給淹沒了。**ContextSift** 就是為了解決這個問題而生：

> 它是一個**純 Python 標準庫**實作的壓縮引擎，不連網、不裝套件、不上傳資料，只做一件事——用可組合的「篩」策略，把文字壓縮到剛好夠用的程度，並告訴你省下了多少 token。

它既能作為函式庫嵌進你的工具鏈，也能作為命令列工具直接管線使用。設計上參考了業界「壓縮命令輸出以節省 LLM token」的產品思路，但完全自研實作，並在策略可組合性、敏感資訊遮罩、統計報表與可重現性上做出差異化。

---

## ✨ 特性

- 🧩 **可組合策略**：12 種壓縮策略（去色、去重、折疊重複、截斷、頭尾保留、遮罩、行數限制、token 預算等），自由疊加、依序執行。
- 🎯 **開箱檔位**：內建 `generic` / `git` / `test` / `build` / `aggressive` 五種預設，一行指令適用常見場景。
- 🔐 **隱私優先**：自動遮罩權杖、金鑰、電子郵件、IP 位址，輸出可安心分享。
- 📊 **所見即所得的統計**：即時給出壓縮前后的行數、字元數、token 數與節省比例。
- 🔒 **零依賴、離線、決定性**：只用標準庫，無網路請求；相同輸入永遠得到相同輸出。
- 🪶 **輕量雙用**：既是 Python 函式庫，也是命令列工具，`python -m contextsift` 即可執行。
- 🧪 **測試完備**：36 個單元測試涵蓋全部策略與核心路徑。

---

## 🚀 快速開始

無須安裝依賴，複製即用（需 Python 3.8+）。

```bash
git clone https://github.com/gitstq/ContextSift.git
cd ContextSift

# 從管線讀取，使用通用檔位壓縮
cat your-log.txt | python3 -m contextsift --profile generic --report text

# 壓縮 git 輸出
git diff | python3 -m contextsift -p git

# 查看所有內建檔位與策略
python3 -m contextsift --list-profiles
python3 -m contextsift --list-strategies
```

也可作為函式庫直接使用：

```python
from contextsift import SiftEngine

result = SiftEngine(profile="test").sift(raw_output)
print(result.text)           # 壓縮後的文字
print(result.report("text")) # 壓縮統計
```

---

## 📖 使用指南

### 命令列

```bash
# 基本用法：檔案輸入 / 標準輸入
contextsift -p generic input.log
cat input.log | contextsift -p generic

# 追加自訂策略（可多次 -s，依給定順序在檔位之後執行）
contextsift -p generic -s number-lines -s truncate-lines:max_chars=120 input.log

# 設定 token 預算，超出則漸進裁減
contextsift -p aggressive --token-budget 2000 big.log

# 寫入檔案並單獨輸出 JSON 報表到終端機
contextsift -p git -o compact.txt --report json big.log
```

> 💡 **策略參數語法**：`-s name:key=val,key2=val2`，例如 `truncate-lines:max_chars=150`。

### 內建策略一覽

| 策略名 | 作用 |
| --- | --- |
| `strip-ansi` | 移除 ANSI 顏色與控制轉義序列 |
| `squeeze-blank` | 連續空行壓成單一空行 |
| `collapse-repeats` | 折疊連續重複行並標註次數 |
| `dedupe` | 全局去重，保留首次出現順序 |
| `strip-noise` | 移除 DEBUG / TRACE 等雜訊行 |
| `truncate-lines` | 超長行截斷並標註原始長度 |
| `head-tail` | 只保留開頭與結尾，中間用摘要替代 |
| `max-lines` | 限制最大行數，超出則等距取樣 |
| `redact` | 遮罩權杖、金鑰、電子郵件、IP |
| `number-lines` | 為每行加行號，便於模型引用 |
| `token-budget` | 依 token 預算漸進裁減 |
| `drop-empty` | 刪除所有空行 |

### 作為函式庫整合

```python
from contextsift import SiftEngine, get_strategy

# 方式一：使用預設檔位
engine = SiftEngine(profile="build", token_budget=4000)
out = engine.sift(text)

# 方式二：從零組裝自己的策略鏈
engine = SiftEngine(profile=None)
engine.add(get_strategy("strip-ansi"))
engine.add(get_strategy("collapse-repeats", min_run=2))
engine.add(get_strategy("redact"))
out = engine.sift(text)

# 結果物件
out.text             # 壓縮後文字
out.lines            # 行列表
out.stats.as_dict()  # 統計字典
out.report("json")   # JSON 報表
```

### 設計迭代

ContextSift 從 0 到 1 的演進，記錄了每一步的取捨：

1. **v0.1 · 最小可用**：只有 `strip-ansi` 與 `dedupe`，驗證「壓縮輸出確實能省 token」的核心假設。
2. **v0.3 · 策略化重構**：把硬編碼邏輯抽象成可組合的 `Strategy` 協定，引入引擎編排，支援策略自由疊加。
3. **v0.6 · 場景檔位**：針對 git / test / build 等真實場景沉澱出預設檔位，降低使用門檻。
4. **v0.8 · 隱私增強**：加入遮罩規則，修正「金鑰被二次覆蓋」的問題，讓輸出可安心分享。
5. **v1.0 · 可重現與打包**：統一決定性語義，補齊 36 個測試、一鍵打包腳本與三語文件，達到生產可用。

與同類工具相比，差異點在於：**純標準庫零依賴**、**策略可任意組合**、**內建隱私遮罩**、**透明可比的統計報表**，以及**完全離線、決定性輸出**。

---

## 📦 打包部署

### 一鍵打包（產生封存檔 + 校驗和）

```bash
python3 scripts/build.py
# 產出 releases/ 下：
#   contextsift-1.0.0.tar.gz
#   contextsift-1.0.0.zip
#   checksums.sha256
```

校驗封存檔完整性：

```bash
cd releases && sha256sum -c checksums.sha256
```

### 安裝為命令列工具

```bash
pip install .
contextsift --version
```

### 作為函式庫部署

ContextSift 是純 Python 函式庫，無平台相關依賴，把 `contextsift/` 目錄放進專案即可，或直接 `pip install .`。跨平台（Windows / macOS / Linux）行為一致。

> 本專案是函式庫 + CLI 混合形態，不做二進位 Release；整合範例見上方「作為函式庫整合」。原始碼封存檔附有校驗和可供核驗。

---

## 🤝 貢獻

歡迎貢獻！請遵守兩條底線：**不引入執行期依賴**、**保持決定性**。提交遵循 Angular 規範（`feat` / `fix` / `docs` / `refactor` / `test` / `chore`），並確保 `python3 -m unittest discover -s tests` 全綠。詳見 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📄 授權

本專案採用 [MIT License](LICENSE)，可自由使用、修改與散佈。

<div align="center">

Made with ❤️ by gitstq · 零依賴 · 離線優先 · 可重現

</div>
