# Stage 0 壓縮 Subgraph — 設計規格與實作參照

> 本文件為新專案開發的完整參照。
> 涵蓋：設計動機、架構決策、現有基礎設施、LangGraph subgraph 規格、Prompt 設計規格、整合介面。

---

## §1 設計動機

### 問題

`stage0_compress.py` 的現有 `_generate_sum()` 是**單層 LLM call**：
- 系統提示 + 一個 prompt template → 直接輸出 sum
- 跑在本地 Qwen 3.5 4B（小模型），要求一次 call 同時完成語意分類 + 壓縮決策 + 生成
- 實測語意覆蓋率僅約 20-25%（命題類語意容易丟失）

### 根本原因

**單層 call = prompt engineering**。小模型在單一 prompt 中需要同時：
1. 識別文本中的語意類型
2. 判斷各段的可壓縮性
3. 執行選擇性壓縮
4. 組裝成連貫的 sum

這是認知負載過高的任務分配，超出 4B 參數模型的可靠執行範圍。

### 解法：context engineering

將壓縮拆分為兩個明確子任務：

| 層 | 任務 | 輸入 | 輸出 |
|----|------|------|------|
| L1（分析） | 切分 + 分類 + 標記 | raw q+a | 帶 `[ACTION]` 標注的 segments JSON |
| L2（生成） | 根據標注執行壓縮 + 組裝 | annotated segments | sum |

L1 → L2 的 handoff 是 **context engineering** 的核心：L1 已完成所有語意判斷，L2 只需「照指令執行」，大幅降低 L2 的認知負載。

---

## §2 五種語意類型框架

任何 Q-A 對話節點中的文本可窮舉為五種語意類型：

| # | 語意類型 | 定義 | 可壓縮性 | L1 標記 |
|---|----------|------|----------|---------|
| 1 | 命題（Proposition） | 原子性的事實聲明或判斷 | 幾乎不可壓縮——刪除即丟失 | `KEEP` |
| 2 | 推理鏈（Reasoning Chain） | 從前提到結論的推導步驟 | 雙態：新穎推理 → `KEEP`；可推導者 → `COMPRESS` | `KEEP` / `COMPRESS` |
| 3 | 結論/決策（Conclusion） | 推理終點或明確的行動選擇 | 不可壓縮，但天然短小 | `KEEP` |
| 4 | 脈絡/動機（Context） | 為什麼討論這個話題、背景 | 高度可壓縮（一句話） | `COMPRESS` |
| 5 | 元對話（Meta-discourse） | 問候、確認、格式標記 | 100% 可壓縮（零語意載荷） | `DROP` |

**窮舉性**：任何文本片段要麼在做聲明（1）、在做推導（2）、在給結論（3）、在交代背景（4）、或在管理對話本身（5）。

**失敗模式預設**：L1 未能分類的段落預設為 `KEEP`（寧可多保留，不可漏刪命題）。

---

## §3 現有基礎設施

### 目錄結構

```
NexCortex/
├── content/          # SSOT A：*.jsonl 對話檔（15 個主題）
├── JSONL-DAG-engine/ # 外部依賴：dag_engine.load() → List[Session]
└── poc/
    ├── config.py     # OLLAMA_URL, OLLAMA_MODEL, CONTENT_DIR 等常數
    ├── llm.py        # call_llm() / call_llm_text() — Ollama HTTP client
    ├── prompts.py    # load(name) — 從 poc/prompts/*.txt 讀取 prompt
    ├── prompts/
    │   ├── stage0_sum_system.txt       # 現有 sum 系統提示
    │   ├── stage0_sum.txt              # 現有 sum prompt（含 {q}, {a} 佔位符）
    │   ├── stage0_session_system.txt   # session narrative 系統提示
    │   └── stage0_session.txt          # session narrative prompt（含 {sums}）
    └── stage0_compress.py  # 現有壓縮腳本（CLI entry point）
```

### `call_llm()` 介面

```python
from llm import call_llm

result: dict = call_llm(
    prompt: str,
    system: str | None = None,
    schema: dict | None = None,   # JSON Schema → Ollama format constraint
) -> dict
```

- 自動處理：JSON fence 清理、`<think>` tag 去除、最多 3 次重試
- `schema` 為 JSON Schema dict → Ollama 的 `format` 欄位（structured output）
- 模型：`qwen3.5:4b`（本地 Ollama，`http://127.0.0.1:11434`）

### JSONL 節點格式

```jsonl
{
  "type": "node",
  "id": "01KMPKDT3F...",
  "q": "使用者問題",
  "a": "回答內容（可能數千字）",
  "sum": null,              // Stage 0 填入
  "parents": ["parent_id"],
  "created_at": "2026-...",
  "compressed": false,
  "keyword": [],
  "scope": []
}
```

`sum` 欄位為 `null` 時需要 Stage 0 填入。軟刪除節點：`q` 以 `[deleted` 開頭，跳過處理。

---

## §4 LangGraph Subgraph 規格

### 整體流程

```
compress_node_sum(q, a, node_id="") -> str
  │
  ▼
[START]
  │
  ▼
router ──── a < SHORT_THRESHOLD ────→ l2_compress ──→ [END]
  │                                         ↑
  └──── a ≥ SHORT_THRESHOLD ──→ l1_annotate ─┘
```

### State Schema

```python
from typing_extensions import TypedDict

class CompressionState(TypedDict):
    node_id: str      # 用於日誌，不影響邏輯
    q: str            # 原始問題
    a: str            # 原始回答
    route: str        # "short" | "long"，由 router 設定
    annotated: str    # L1 輸出的格式化標注文本，short path 為空字串
    sum: str          # 最終輸出
```

> **注意**：`route` 和 `annotated` 不需要 reducer（單一 worker，no fan-out）。

### Nodes

#### `router`

```python
SHORT_THRESHOLD = 800  # chars in `a`；初始值，需實際語料校準

def router(state: CompressionState) -> dict:
    route = "short" if len(state["a"]) < SHORT_THRESHOLD else "long"
    return {"route": route}
```

#### `l1_annotate`

- 輸入：`state["q"]`, `state["a"]`（截斷至 4000 chars）
- 呼叫 L1 prompt（見 §5）
- 輸出 JSON segments，轉換為格式化文本存入 `state["annotated"]`

轉換格式：
```
segments = [
  {"text": "命題內容...", "action": "KEEP"},
  {"text": "背景說明...", "action": "COMPRESS"},
  {"text": "好的，讓我解釋...", "action": "DROP"},
]

→ annotated = "[KEEP] 命題內容...\n[COMPRESS] 背景說明...\n[DROP] 好的，讓我解釋..."
```

失敗保底：若 segments 為空，使用 `state["a"][:2000]` 作為 `annotated`（使 L2 仍能執行）。

#### `l2_compress`

```python
def l2_compress(state: CompressionState) -> dict:
    if state["route"] == "long" and state.get("annotated"):
        # Long path: annotation-guided compression
        prompt = L2_ANNOTATED_PROMPT.format(q=state["q"], annotated=state["annotated"])
        result = call_llm(prompt, system=L2_ANNOTATED_SYSTEM, schema=SUM_SCHEMA)
    else:
        # Short path: reuse existing stage0_sum prompt
        prompt = L2_SHORT_PROMPT.format(q=state["q"], a=state["a"][:3000])
        result = call_llm(prompt, system=L2_SHORT_SYSTEM, schema=SUM_SCHEMA)
    return {"sum": str(result.get("sum", "")).strip()}
```

### 路由函數

```python
from typing import Literal

def _route_after_router(state: CompressionState) -> Literal["l1_annotate", "l2_compress"]:
    return "l1_annotate" if state["route"] == "long" else "l2_compress"
```

### Graph 組裝

```python
from langgraph.graph import StateGraph, START, END

def build_compression_graph():
    builder = StateGraph(CompressionState)

    builder.add_node("router", router)
    builder.add_node("l1_annotate", l1_annotate)
    builder.add_node("l2_compress", l2_compress)

    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router", _route_after_router, ["l1_annotate", "l2_compress"]
    )
    builder.add_edge("l1_annotate", "l2_compress")
    builder.add_edge("l2_compress", END)

    return builder.compile()
```

### 公開介面

```python
# Singleton compiled graph（模組級別 lazy init）
_graph = None

def compress_node_sum(q: str, a: str, node_id: str = "") -> str:
    """Main entry point. Returns compressed sum string."""
    global _graph
    if _graph is None:
        _graph = build_compression_graph()

    result = _graph.invoke({
        "node_id": node_id,
        "q": q,
        "a": a,
        "route": "",
        "annotated": "",
        "sum": "",
    })
    return result["sum"]
```

---

## §5 Prompt 設計規格

### 新增 Prompts（需建立）

#### `stage0_l1_system.txt`

```
你是文本語意分析助手。分析給定的問答文本，將答案切分為語意完整的段落，並為每段標記處理方式。
保留原始語言（中文保留中文，英文保留英文）。
```

#### `stage0_l1.txt`

```
分析以下問答，將答案切分為語意段落，並為每段標記處理方式。

Q: {q}

A: {a}

語意類型與處理規則：
- KEEP：命題（不可刪除的事實聲明）、推理鏈中的新穎推導步驟、結論/決策
- COMPRESS：脈絡說明、背景動機（可濃縮至一句）、可從前提推導的推理步驟
- DROP：元對話（問候、確認、「好的」、格式引導語）、重複已說過的內容

切分原則：
- 每段 1-4 句話，保持語意完整性
- 寧可少切（保留邏輯連貫段落），不要過度切分
- 無法判斷類型時，預設標記為 KEEP

只回傳 JSON 物件：
{"segments": [{"text": "段落文本", "action": "KEEP"}, ...]}
```

#### `stage0_l2_annotated_system.txt`

```
你是知識萃取助手，根據語意標注生成密集摘要。
保留原始語言（中文保留中文，英文保留英文）。
```

#### `stage0_l2_annotated.txt`

```
根據以下標注段落，生成問答節點的密集摘要（sum）。

原始問題：{q}

標注段落：
{annotated}

標注說明：
- [KEEP]：必須保留的核心內容（命題、新穎推理、結論）
- [COMPRESS]：需要濃縮的背景資訊（一句話帶到關鍵點即可）
- [DROP]：忽略，不納入摘要

摘要規則：
- 長度：1-2 句話，不超過 120 字
- 必須涵蓋所有 [KEEP] 段落的核心資訊
- [COMPRESS] 段落擇要保留最關鍵的背景（若 [KEEP] 已足夠，可省略）
- 忽略所有 [DROP] 段落
- 禁止：泛泛描述（「討論了...」「介紹了...」「探討了...」），直接陳述結論或洞見
- 禁止：「此」「這個」作為開頭
- 語氣：陳述句，不用「本文」「作者」等學術腔

只回傳 JSON 物件：
{"sum": "<摘要內容>"}
```

### 現有可重用 Prompts（Short Path）

Short path 的 L2 直接重用：
- System: `stage0_sum_system.txt`
- Prompt: `stage0_sum.txt`（佔位符：`{q}`, `{a}`）

---

## §6 JSON Schemas

```python
# L1 output schema
L1_SCHEMA = {
    "type": "object",
    "properties": {
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "action": {"type": "string", "enum": ["KEEP", "COMPRESS", "DROP"]}
                },
                "required": ["text", "action"]
            }
        }
    },
    "required": ["segments"]
}

# L2 output schema（shared）
SUM_SCHEMA = {
    "type": "object",
    "properties": {"sum": {"type": "string"}},
    "required": ["sum"]
}
```

---

## §7 整合點

### 與 `stage0_compress.py` 整合

現有腳本的 `_generate_sum(q, a)` 可替換為：

```python
from stage0_graph import compress_node_sum

# 原本：
record["sum"] = _generate_sum(record["q"], record["a"])

# 替換為：
record["sum"] = compress_node_sum(record["q"], record["a"], node_id=record["id"])
```

建議以 `--use-graph` flag 控制，保留原有 single-call path 作為 baseline 對比。

### 作為主 Agent Workflow 的 Subgraph

```python
from stage0_graph import build_compression_graph

# 在主 graph 中作為節點
compression_subgraph = build_compression_graph()

main_builder.add_node("compress_node", compression_subgraph)
```

或在主 graph 的節點中直接呼叫 `compress_node_sum()`（function call，非 subgraph 掛載）。

---

## §8 開放設計決策

| 決策點 | 當前設定 | 校準方式 |
|--------|----------|----------|
| `SHORT_THRESHOLD` | 800 chars（`a` 欄位） | 實測語料分佈，找自然斷點 |
| L1 / L2 是否同一模型 | 預設同一（`qwen3.5:4b`） | L1 可換更小模型加速 |
| L1 few-shot 範例 | 先 zero-shot，穩定後加 | 從實測失敗案例提取 |
| L1 失敗保底策略 | 空 segments → 使用 raw a | 或可 fallback 至 short path |
| `a` 截斷長度 | L1: 4000 chars，L2 short: 3000 chars | 依 OLLAMA_NUM_CTX 調整 |

---

## §9 評估標準

Stage 0 品質驗證（對應三通道完備性前提 P0）：

| 評估維度 | 通過標準 |
|----------|----------|
| 命題覆蓋率 | sum 保留原始節點中所有不可壓縮命題 |
| 資訊密度 | sum 字數 ≤ 原文 20%，語意損失 < 5% |
| 一致性 | 相同輸入，不同 run 的 sum 語意等價（允許表面差異） |
| 無幻覺 | sum 不包含原文中不存在的事實 |

---

## §10 依賴清單

```
# 現有（poc/requirements.txt）
requests        # Ollama HTTP client
duckdb
networkx
python-louvain
pyvis
python-ulid

# 新增
langgraph       # pip install langgraph
```

本地模型：`qwen3.5:4b`（Ollama，`http://127.0.0.1:11434`）

---

*文件日期：2026-03-28*
*性質：Stage 0 LangGraph subgraph 開發參照文件*
*對應架構文件：NexCortex-04-三通道完備性推導與語意類型映射.md*




taskkill //IM "ollama app.exe" //F 2>&1; taskkill //IM ollama.exe //F 2>&1
OLLAMA_FLASH_ATTENTION=1 
OLLAMA_KV_CACHE_TYPE=q8_0 
LLAMA_GPU_OVERHEAD=268435456 
ollama serve > /tmp/ollama.log 2>&1 
ollama  list 2>&1