# Compression Subgraph

背景任務，將每輪問答壓縮成一行 `sum` 寫入 DAG node，不阻塞主對話。

## 架構

```
答案長度 < SHORT_THRESHOLD(300)?
    YES → L2 (short path)   ── 直接摘要
    NO  → L1 → L2           ── 標注後再摘要
```

**L1 (l1_annotate)**：Python 端按 `\n\n` 預切段落並編號，model 只回傳索引+標籤（`KEEP / COMPRESS / DROP`），Python 端重建帶標籤文本。Model 不復現原文，output token 極少。

**L2 (l2_compress)**：接收標注段落（long path）或原始問答（short path），生成 1-2 句密集摘要。

## 檔案

| 檔案 | 職責 |
|------|------|
| `src/agent/compression/graph.py` | StateGraph 定義、nodes、`run_compression()` 公開入口 |
| `src/agent/compression/prompts.py` | 所有 prompt 常數、`SHORT_THRESHOLD` |
| `src/agent/llm.py` | 模型路由層：`get_compress_model()` |
| `src/agent/compression/__init__.py` | re-export `run_compression` |

## 模型設定（`.env`）

```
COMPRESS_MODEL=ollama/qwen3.5:4b              # 格式: provider/model-name
OLLAMA_URL=http://127.0.0.1:11434
COMPRESS_FALLBACK_MODEL=google_genai/gemini-2.0-flash-lite  # 留空則停用 fallback
```

切換模型只改 `COMPRESS_MODEL`，code 不動。支援 `ollama/`、`google_genai/`、其他 LangChain provider。

`COMPRESS_FALLBACK_MODEL` 設定後，Ollama 連線失敗（`ConnectError` / `ConnectTimeout`）時自動 fallback 至指定模型，由 LangChain `RunnableWithFallbacks` 處理，nodes 不感知切換。

### Ollama 特殊處理

`langchain-ollama` v1.0+ 使用 `reasoning=False`（constructor 欄位）停用思考模式，取代舊版的 `think=False` invoke-time kwarg。

`format` 不在 constructor 設定；`with_structured_output(method="json_schema")` 會將 Pydantic schema 序列化成 JSON Schema 傳給 Ollama 的 `format` 參數，在採樣層做 grammar-constrained decoding，比 `format="json"` + prompt 指令更可靠。

## 錯誤降級鏈

```
L1 失敗 → annotated = a[:2000]（L2 仍執行）
L2 失敗 → sum = ""
run_compression() 收到 "" → sum = q[:100] + "..."（保證非空字串）
```

## 整合點（`src/agent/graph.py`）

`summarize` node 建立 `asyncio.Task` 執行 `_compress_and_persist()`，立即返回 `{"summary": "", "last_node_id": node_id}`，主對話不等待。

壓縮完成後才呼叫 `append_node()`（`sum_text: str` 為必填），確保 JSONL 寫入時 sum 已就緒。

shutdown 順序：`cancel_session_flusher` → `drain_compression_tasks(timeout=30s)` → `flush_all_sessions`。

## 測試

```bash
# short path（< 300 chars）
PYTHONPATH=src python scripts/test_compression.py \
  --q "問題" --a "短答案"

# long path + 看 L1 segments
PYTHONPATH=src python scripts/test_compression.py --verbose \
  --q "問題" --a "第一段\n\n第二段\n\n第三段..."

# \n 會展開為真正換行
```

`--verbose` 模式印出實際 prompt、每段 L1 標籤、L1/L2 個別耗時。
