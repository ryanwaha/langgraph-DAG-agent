
# NexCortex 項目啟動說明

> 本文件是 NexCortex 專案的權威架構快照，收斂自五份架構設計文件（00-04）的最終狀態。
> 所有增量式修訂已被吸收為當前狀態的直接陳述。前置文件保留為推導紀錄，本文件是架構的唯一參考。

---

## 文件系譜

```
NexCortex-00  宏觀架構總結報告（原始架構）
NexCortex-01  宏觀架構修訂說明（六項結構性修正）
NexCortex-02  底層檢索引擎架構修訂說明（Agent 工具箱收斂）
NexCortex-03  ETL Pipeline 結構性決策修訂說明（結構與靈活性的辯證收斂）
NexCortex-99  專案核心哲學與元架構說明（元原則、哲學定位、設計原則體系）
    │
    └─► 本文件：項目啟動說明（權威快照）
```

---

## §1 專案本體論前提

### 流行 PKM 模型的根本缺陷

現有主流個人知識管理系統（如 Building a Second Brain）的隱含本體論預設為：知識是靜態物件，大腦是存取介面。此預設在根本上是錯誤的。大腦不存儲知識，它持續重建知識。每次「回憶」都是重新激活一個分佈式的激活模式，而非讀取一個文件。認知的本質是動態的拓撲重組，不是靜態的資料存取。

### 本體論轉移

| 維度 | 流行 PKM | 本系統 |
|------|----------|--------|
| 知識的性質 | 靜態物件 | 激活模式（邊的集合） |
| 核心動作 | 存儲 | 分析（Pipeline 產出 Session） |
| 查詢行為 | 檢索 | 推理（語意湧現） |
| 時間的角色 | 元數據 | 獨立語意層 |
| 你與系統的關係 | 使用者 | 系統的一部分（Self 節點） |
| 系統形態 | 快照 | 過程 |

**核心命題**：你不是在存放想法的地方，而是在構建一個與你一同演化的認知結構的外化。

### 系統的設計前提

系統的查詢主要由 Agent 自律執行，而非人類發起的互動式查詢。架構提供的是一組獨立的工具與框架，允許推理湧現。不存在 hardcoded 的查詢管線。這個前提影響所有底層設計決策。

---

## §2 元原則

### 陳述

> **凡是脈絡相關的語意判斷，在存儲層固化即為範疇錯誤。**
>
> 存儲層只合法存放脈絡無關的結構性事實與最低限度的信號標記。語意詮釋的唯一合法場所是查詢時的推理。

### 操作化邊界

| 合法（存儲層該做的） | 非法（存儲層不該做的） |
|---|---|
| 辨識概念錨點（讓 Kuzu 有節點可遍歷） | 完整表徵概念的語意與關係 |
| 三值的二元維度標註（信號標記） | 精確分類認知事件的類型（語意詮釋） |
| 存儲兩端上下文片段（素材保留） | 預先詮釋上下文片段的語意 |
| 字串正規化（表面形式統一） | 語意等價判斷（概念合併） |
| 保留疑似重複為獨立節點 | 積極合併灰色地帶的概念 |

精煉表述：**ETL 層可以標記信號的存在，但不可以詮釋信號的意義。**

---

## §3 設計原則完整體系

### 一覽表

| # | 原則 |
|---|------|
| 一 | GraphDB 是衍生物，永遠不直接編輯 |
| 二 | 兩個 SSOT 管轄不同認識論領域，不強行合併 |
| 三 | Frontmatter 是高優先級影響信號，而非直接賦值 |
| 四 | Wikilinks 是意圖的表達，其語意在推理時湧現 |
| 五 | 漂變是一等公民，以 Event Sourcing 模式承載 |
| 六 | GraphDB 不以時間作為查詢維度 |
| 七 | 跨層 JOIN 非法，語意由 LLM 在推理時湧現 |
| 八 | Session 是分析產出，其身份由邊的集合定義 |
| 九 | ETL 的非確定性以 context engineering 控制 |
| 十 | Agent 的工具彼此獨立，不存在固定的查詢管線 |
| 十一 | DuckDB 是結構化資料的通用查詢引擎，不綁定特定層 |
| 十二 | 向量索引是系統的粗粒度激活入口 |
| 十三 | 概念節點的職責是拓撲骨架，不是知識表徵 |
| 十四 | 認識論事件以正交的三值維度標註，不做離散分類 |
| 十五 | 模糊去重不在 ETL 層執行，由社群結構的湧現取代 |

### 各原則精確陳述

**原則一：GraphDB 是衍生物，永遠不直接編輯**
所有修正發生在 SSOT，GraphDB 永遠可從 Event Log 確定性重建。直接編輯 GraphDB 等同於編輯編譯後的 binary——下次重建即消失，且喪失 provenance。

**原則二：兩個 SSOT 管轄不同認識論領域，不強行合併**
SSOT A（對話紀錄）承載被動生成的隱含知識，SSOT B（Obsidian Vault）承載主動撰寫的顯性宣告。兩者管轄不同的認識論領域，它們之間的張力本身就是信號，不是需要消除的噪音。

**原則三：Frontmatter 是高優先級影響信號，而非直接賦值**
Frontmatter 不直接決定 GraphDB 節點屬性，而是以高權重先驗參與多信號合成。每個節點屬性記錄完整的 provenance（主要信號來源、置信度、參與信號列表）。Provenance 存在於 GraphDB 節點/邊的屬性中（供 LLM 參考與 debug 用途），但不參與 Kuzu 的圖遍歷與排序邏輯。

**原則四：Wikilinks 是意圖的表達，其語意在推理時湧現**
Wikilinks 不被 ETL 機械式解析為結構化邊。它們保留在原始上下文中，透過向量索引被 LLM 看到，由 LLM 在推理時自行理解其意圖。ETL 只抽取結構化指標（懸空連結清單、連結密度），不詮釋連結的語意。

**原則五：漂變是一等公民，以 Event Sourcing 模式承載**
認知漂變（drift）不是異常，而是系統必須承載的核心現象。GraphDB 節點永遠不被「修改」，只有新的認識論事件被追加到 Event Log。當前狀態是事件序列的摺疊（fold）。

**原則六：GraphDB 不以時間作為查詢維度**
GraphDB 的邊與節點可攜帶 date 與 provenance 作為 metadata，但嚴格遵守以下約束：
- A. 不作為遍歷條件：Cypher 查詢永遠不寫 `WHERE edge.date > ...`。時間篩選只發生在 DuckDB 側。
- B. 不作為排序依據：GraphRAG 組裝 context 時，不按邊的 date 排序。排序由敘事層 LCM DAG 結構決定。
- C. LLM 可見：組裝給 LLM 的 context 中，這些 metadata 作為被動可見的輔助信號存在，LLM 自行決定是否利用。

時序推理的主通道是敘事層（LCM DAG）。當 GraphDB metadata 與敘事層產生衝突時，以敘事層為準。

**原則七：跨層 JOIN 非法，語意由 LLM 在推理時湧現**
預先計算跨層 JOIN 會把時序語意污染進拓撲層、讓 schema 變動需要重建 JOIN 邏輯、消滅 LLM 在推理時自行發現關聯的可能性。各層從未直接對話，LLM 是唯一的跨層介面。

**原則八：Session 是分析產出，其身份由邊的集合定義**
Session 不是原始文件的替身，而是對原始文件執行認識論分析之後的產出物。Session 的身份由其邊的集合定義（類比神經元：神經元就是那些連結本身的具現化）。pkm_score 是動態的激活閾值，非一次性計算。

**原則九：ETL 的非確定性以 context engineering 控制**
Pipeline 中 LLM 參與的所有階段（語意抽取、事件分類、關係推斷），其輸出不保證跨版本一致。系統通過嚴格的 prompt 設計、結構化輸出約束、與可復現的上下文組裝策略，將非確定性控制在不影響架構不變量的範圍內。

**原則十：Agent 的工具彼此獨立，不存在固定的查詢管線**
所有工具可按需獨立取用，交由 Agent 與語境決定組合方式。Agent 可能只用向量索引（輕量入口），也可能組合全部五個工具（完整 GraphRAG），完全取決於推理需要。

**原則十一：DuckDB 是結構化資料的通用查詢引擎，不綁定特定層**
DuckDB 以嵌入式 library 形式運行在 Agent 進程中，按需讀取任何 Parquet / CSV / 結構化檔案。Event Log 只是它查詢的資料集之一，不是它的身份。DuckDB 不「擁有」任何資料，它「觸及」所有結構化資料。

**原則十二：向量索引是系統的粗粒度激活入口**
向量索引執行擴散激活——相關度高的內容被點亮，相關度低的內容自然被蓋過。不做精確篩選，不做結構化查詢，只回答「什麼跟這段語意最相近」。覆蓋除 Event Log 外的所有語意來源。

**原則十三：概念節點的職責是拓撲骨架，不是知識表徵**
概念抽取的目標是辨識足以導航的錨點，不是完整表徵語意。概念節點只需要提供足夠的結構，讓圖能做只有圖才能做的事：多跳遍歷、社群偵測、Session 邊集合身份、Self 節點認知側寫。正確粒度無先驗答案，從 POC 迭代中校準。

**原則十四：認識論事件以正交的三值維度標註，不做離散分類**
ETL 層對認知事件做三個獨立的三值判斷（structural_change、tension、integration），不試圖將其歸入預定義的事件類型。事件的精細詮釋由查詢時 LLM 從 flags 組合與上下文片段中湧現。

**原則十五：模糊去重不在 ETL 層執行，由社群結構的湧現取代**
ETL 層只做確定性的字串正規化。語意等價的判斷不在存儲層固化——疑似重複的概念保留為獨立節點，透過社群偵測的共現模式自然呈現等價關係。寧可漏合（可逆），不可錯合（不可逆）。

---

## §4 系統不變量

> 1. 從 **DuckDB Event Log** 出發，可**確定性**重建任意歷史時間點的 **Kuzu GraphDB** 狀態。
> 2. 從 **SSOT A + B** 出發，可重新生成 Event Log（**近似，非精確**）。
> 3. Event Log 具有不可替代性，需獨立備份。
> 4. GraphDB 是完全可拋棄的計算結果。
> 5. 敘事層（LCM DAG）是獨立的平行層，不寫回任何 SSOT。

---

## §5 SSOT 架構

### 階梯式結構

SSOT 結構為階梯式，而非扁平：

```
SSOT A + B（不可變原料）
    ↓  ETL Pipeline（含 LLM，非確定性）
Event Log（衍生但不可精確重建的中間產物）
    ↓  物化程序（確定性）
GraphDB（可拋棄的末端視圖）
```

### SSOT A：對話紀錄

- 格式：JSONL DAG（`q`、`a`、`sum_text`、`parents`、ULID-based IDs）
- 性質：被動生成、隱含知識、高覆蓋低精準、不可回頭修改
- 規模：~300MB 語料庫，100-500 個檔案，目前為線性結構（非分支）
- 工具：`dag_engine.load()`（github.com/ryanwaha/JSONL-DAG-engine）

### SSOT B：Obsidian Vault

- 格式：Markdown 筆記 + YAML frontmatter + wikilinks
- 性質：主動撰寫、顯性宣告、低覆蓋高精準、隨時可修正
- 角色：SSOT B 的編輯介面，不是 Agent 的查詢工具
- 不含任何自動生成內容（敘事層不寫回 Obsidian）

### Event Log

- 格式：Append-only DuckDB / Parquet
- 性質：SSOT A + B 的衍生物，但因 ETL 包含 LLM 推斷（非確定性函數），一旦生成即不可從原料精確重建
- 地位：具有不可替代性，需要獨立備份策略
- 當前狀態是事件序列的摺疊：`current_state = event_log.fold(initial_state, apply_event)`

### GraphDB

- 格式：Kuzu 圖資料庫
- 性質：Event Log 的確定性物化視圖，完全可拋棄
- 可從 Event Log 確定性重建任意歷史時間點的狀態

---

## §6 系統層次架構

### 完整架構圖

```
┌──────────────────────────────────────────────────────────────┐
│                     SSOT 層（唯一真實來源）                   │
│                                                              │
│   SSOT A：對話紀錄（JSONL DAG）                              │
│   SSOT B：Obsidian Vault（筆記 + frontmatter + wikilinks）   │
└───────────────────────────┬──────────────────────────────────┘
                            │ ETL Pipeline
                            │ （含 LLM 推斷，非確定性）
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    事件層（Event Log）                        │
│                                                              │
│   Append-only · Parquet 存儲 · DuckDB 查詢                   │
│   認識論事件流（三值維度模型）                                 │
│   ← 衍生但不可精確重建，需獨立備份                            │
└───────────────────────────┬──────────────────────────────────┘
                            │ 物化程序（確定性）
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    敘事層（Narrative Layer）                  │
│                                                              │
│   LCM DAG 結構 · 獨立平行層 · 不寫回任何 SSOT               │
│   Level 0：今日事件（原始）                                   │
│   Level 1：週摘要（壓縮）                                     │
│   Level 2：月摘要（高度壓縮）                                 │
│   Level 3：年摘要（結構性轉移）                               │
│   ← 每個摘要節點保留 event_ids 指針，可按需展開              │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    圖狀態層（GraphDB）                        │
│                                                              │
│   Kuzu · 當前知識拓撲 · 可完全拋棄重建                        │
│   節點：Concept / Session / Note / Self / Insight / Question  │
│   邊：帶 source · confidence · provenance metadata           │
│   ← 只表達當前拓撲，與時間解耦                               │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    檢索層                                     │
│                                                              │
│   向量索引（粗粒度激活入口）                                  │
│   索引：SSOT A/B 內容、LCM 敘事、Kuzu 節點描述               │
│   排除：Event Log（結構化事件不做語意相似度搜尋）             │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    推理層                                     │
│                                                              │
│   LLM · 注入個人側寫作為 global context                      │
│   五個獨立工具按需組合 · 跨層語意在此湧現                     │
└──────────────────────────────────────────────────────────────┘
```

### 各層職責分工

| 層次 | 存儲系統 | 管轄範疇 | 關鍵性質 |
|------|----------|----------|----------|
| SSOT A | JSONL DAG | 行為紀錄 | 不可修改 |
| SSOT B | Obsidian | 意圖宣告 | 人工維護，純寫入介面 |
| Event Log | DuckDB / Parquet | 認識論事件 | Append-only，不可精確重建 |
| 敘事層 | LCM DAG | 時序語意 | 獨立平行層，不寫回 SSOT |
| GraphDB | Kuzu | 當前拓撲 | 可拋棄重建，與時間解耦 |
| 檢索層 | 向量索引 | 語意相似度 | 粗粒度激活入口 |
| 推理層 | LLM | 跨層合成 | 語意湧現，唯一的跨層介面 |

---

## §7 核心實體定義

### Session 節點

**本體論定位**：Session 不是原始對話檔案的替身，而是對原始文件執行認識論分析之後的產出物。

```
對話紀錄.txt ──Pipeline──► Session（分析的物化結果）
（SSOT A，原始文件）        （GraphDB 的公民）
```

原始文件繼續留在 SSOT A，Session 是完全不同類型的存在。兩者不在同一個層次。

**神經元類比**：

| 神經元 | Session |
|--------|---------|
| 細胞體（soma） | Session 節點本身（屬性） |
| 樹突（接收信號） | 入邊（來自其他 Session 的關係） |
| 軸突（發送信號） | 出邊（指向 Concept / Insight / Question） |
| 突觸權重 | 邊的 confidence / salience |
| 激活閾值 | pkm_score |

Session 的身份由其邊的集合定義——神經元不是「有連結的點」，神經元就是那些連結本身的具現化。

**跨層樞紐角色**：Session 節點天然同時屬於多個層次，是各層指針的集合地：

```
Session 節點
├─ source_ref      → SSOT A（原始對話文件）
├─ narrative_ref   → 敘事層（對應的日記體摘要）
├─ event_ids[]     → Event Log（對應的認識論事件）
└─ 圖結構出邊      → Concept / Insight / Question 節點
```

Session 是通往各層的鑰匙，而非各層內容的存儲地。

### 概念節點（Concept）

概念節點的存在理由是且僅是：提供 Kuzu 可遍歷的拓撲骨架。

- 概念節點不是知識的表徵，不需要「正確地」捕捉所有語意細節
- 它只需要提供足夠的結構，讓圖能做只有圖才能做的事：多跳遍歷、社群偵測、Session 邊集合身份、Self 節點認知側寫
- 抽取目標：辨識足以標記主題座標的錨點概念

### Self 節點

以認知主體為圖的中心節點。邊不只是語意關係，而是認識論事件：

```
[Self] -[UNDERSTANDS {date, confidence}]→ [Concept]
[Self] -[PUZZLED_BY {date}]→ [Concept]
[Self] -[CHANGED_VIEW_ON {from_session, to_session}]→ [Concept]
```

Self 節點的邊攜帶 date 與 provenance 作為 metadata，但遵守原則六的約束（不作為遍歷條件、不作為排序依據、LLM 可見）。

**湧現的個人側寫**：以 Self 為錨點，從圖的社群結構自然湧現：

```
認知偏好集群   ← 傾向什麼樣的思維模式與架構選擇
技術能力集群   ← 哪些領域有深度認識
認知盲區集群   ← 反覆問同類問題、某概念始終模糊
epistemic_status: "implicit" 節點  ← 頻繁使用但從未在 Obsidian 命名的概念
```

這些集群構成可機器讀取的「你」，作為 global context 按需注入 LLM。Self 節點不是系統的使用者，而是系統的錨點。

### 其他節點類型

| 節點類型 | 角色 |
|----------|------|
| Note | Obsidian 筆記的 GraphDB 對應物 |
| Insight | 從分析中湧現的洞察 |
| Question | 尚未解答的問題 |

---

## §8 Obsidian 整合

### 信號強度梯度

Obsidian 文件中，不同結構承載不同的認識論力量：

```
最強  │  frontmatter 顯式欄位     你的明確宣告
      │  wikilinks + 上下文句     你的有意識連結
      │  筆記標題                 你認為值得命名的概念
      │  筆記正文語意             你撰寫時的隱含判斷
最弱  │  自動抽取（對話紀錄）     LLM 的推斷
```

### Frontmatter 與多信號合成

Frontmatter 不直接決定 GraphDB 節點屬性，而是以高權重先驗參與多信號合成：

```
節點屬性 = synthesize({
  frontmatter_explicit:   weight=0.90,
  wikilink_cooccurrence:  weight=0.60,
  llm_extraction:         weight=0.40,
  conversation_context:   weight=0.30,
})
```

每個節點屬性記錄完整 provenance：`primary_source`（主要信號來源類型）、`confidence`（置信度）、`signal_list`（參與信號列表）、`source_session_id`（來源 Session）。

Provenance 存在於 GraphDB 但不參與 Kuzu 的圖遍歷與排序邏輯。LLM 在推理時可見，作為判斷信號可靠度的輔助依據。

### Wikilinks 的處理

Wikilinks 的語意不由 ETL 預先詮釋，而在推理時由 LLM 湧現。Wikilinks 及其周圍的上下文句透過向量索引被 LLM 看到，LLM 自行理解意圖。

```
反向連結上下文  → 向量索引覆蓋（上下文句的 embedding）
懸空連結        → ETL 生成清單存為 Parquet（gap detection 信號源）
                  DuckDB 可查，但語意不預先詮釋
別名連結        → 保留在原始筆記中，LLM 在推理時可見
連結密度        → ETL 計算為結構化指標存入 Parquet，DuckDB 可查
```

`overrides` frontmatter 欄位是唯一的手動修正介面，且它在 SSOT B 裡，不在 GraphDB 裡。

### Obsidian 在查詢時的角色

Obsidian 的所有可查詢內容已被其他引擎完整覆蓋：

| Obsidian 筆記的組成 | 查詢時由誰負責 |
|---------------------|----------------|
| Frontmatter (YAML) | DuckDB（結構化欄位查詢） |
| 筆記正文語意 | 向量索引（語意相似度） |
| Wikilinks 圖拓撲 | Kuzu（ETL 物化後的邊） |
| Wikilinks 語意意圖 | 向量索引（上下文句的 embedding）+ LLM 推理時湧現 |

Agent 在查詢時不直接存取 Obsidian Vault。

---

## §9 Event Sourcing 與認知漂變

### 認知漂變的性質

人類認知的漂變（drift）不是異常，而是系統必須承載的核心現象。傳統快照模型無法區分：「這是一直以來的理解」與「這是經過 14 個月修正後的理解」。

GraphDB 節點永遠不被「修改」，只有新事件被追加。

### 認識論事件：三值維度模型

三個正交的二元維度，每個採三值邏輯：

| 維度 | 語意 | 偵測信號 |
|------|------|----------|
| structural_change | 結構有沒有變（量變 vs 質變） | 同一概念在不同 Session 中的框架定位是否改變 |
| tension | 有沒有產生未解決的矛盾（收斂 vs 發散） | 「但是我之前以為」「這跟之前矛盾」vs「原來如此」「說得通了」 |
| integration | 概念之間變得更統一還是更分化（合流 vs 分岔） | 「X 和 Y 其實是同一件事」vs「X 裡面其實有兩個不同機制」 |

**三值邏輯**：

| 值 | 意義 |
|----|------|
| True | 模型有足夠證據判斷為是 |
| False | 模型有足夠證據判斷為否 |
| Null | 證據不足以做判斷，或維度不適用 |

Null 吸收了「不適用」與「不確定」兩種情況。模型的信心程度被編碼進「敢不敢 commit 一個 true / false」這個決策本身。不引入 confidence 浮點數——在質性判斷上疊加量化指標是範疇錯誤。

### 有效組合與自然對應

全非 null 的有效組合為 8 種：

| structural | tension | integration | 自然對應（查詢時湧現，非 ETL 標註） |
|------------|---------|-------------|--------------------------------------|
| false | false | true | 日常學習：知道更多了，東西串起來了 |
| false | false | false | 區分深化：同框架內看到更多細節 |
| false | true | true | 疑惑浮現：東西看似該連但連不上 |
| false | true | false | 細節矛盾：具體事實之間打架 |
| true | false | true | 頓悟合併：框架重組，多歸一 |
| true | false | false | 框架分裂：一個概念拆開了，各自獨立 |
| true | true | true | 深層矛盾：根本框架之間的衝突 |
| true | true | false | 範式危機：舊框架碎了，新框架還沒成形 |

右欄的詮釋不是 ETL 的產出——它在查詢時由 LLM 根據 flags 組合與上下文片段自行湧現。

### Event Log Schema

```json
{
  "concept": "...",
  "sessions": ["session_A", "session_B"],
  "context_A": "...",
  "context_B": "...",
  "structural_change": true | false | null,
  "tension": true | false | null,
  "integration": true | false | null
}
```

三個維度，三值邏輯，無浮點數。上下文片段保留為 payload，供查詢時 LLM 做精細詮釋。

### pkm_score 與 confidence

兩個正交維度，共享梯度模型但各自獨立計算：

```
pkm_score（節點屬性）：這個概念/Session 在認知空間中有多「活躍」
  ← 被查詢命中、被其他 Session 引用、被 Event 提及 → 增強
  ← 長期未被激活 → 衰減

confidence（邊屬性）：這兩個概念之間的關係有多「可靠」
  ← 被更多 Session 佐證、被更多事件支持 → 增強
  ← 長期未被新證據支持 → 衰減
```

不等價：高 pkm_score 的節點可能有低 confidence 的邊（頻繁提及但關聯不確定），低 pkm_score 的節點之間可能有高 confidence 的邊（冷門但關係確鑿）。

pkm_score 是動態的，非一次性計算。更新機制與 confidence 同構（激活增強 + 時間衰減），但數值互不決定。對應神經元類比：pkm_score 是靜息電位（基礎活性），confidence 是突觸強度（連結可靠度）。

**物化階段的過濾邏輯**：

```
Event Log → 物化程序 → GraphDB

寫入條件（兩個閾值獨立）：
  節點：pkm_score ≥ node_threshold  → 寫入
  邊：  confidence ≥ edge_threshold → 寫入
```

pkm_score 與 confidence 的激活增強與時間衰減計算發生在 DuckDB 側（聚合查詢、窗口函數），計算結果存為 Parquet，物化程序讀取後判斷閾值。

---

## §10 GraphDB 設計

### Kuzu 的角色

Kuzu 管當前圖狀態與多跳遍歷（Graph）。它只表達當前拓撲信念：「你現在相信 A 與 B 有某種關係」。「你是如何、何時形成這個信念」屬於 Event Log 與敘事層。

### 時間解耦規則

GraphDB 的邊與節點可攜帶 date 與 provenance 作為 metadata，但：

- **A. 不作為遍歷條件**：Cypher 查詢永遠不寫 `WHERE edge.date > ...`。時間篩選只發生在 DuckDB 側。
- **B. 不作為排序依據**：GraphRAG 組裝 context 時，不按邊的 date 排序。排序由敘事層 LCM DAG 結構決定。
- **C. LLM 可見**：組裝給 LLM 的 context 中，這些 metadata 作為被動可見的輔助信號存在。

### 節點類型

| 節點類型 | 說明 |
|----------|------|
| Concept | 概念錨點（拓撲骨架） |
| Session | 認識論分析的物化結果 |
| Note | Obsidian 筆記對應物 |
| Self | 認知主體錨點 |
| Insight | 湧現的洞察 |
| Question | 未解答的問題 |

### 邊的 metadata

所有邊攜帶：
- `source`：信號來源類型
- `confidence`：置信度（動態，激活增強 + 時間衰減）
- `provenance`：`primary_source`、`signal_list`、`source_session_id`

### 物化條件

```
節點寫入：pkm_score ≥ node_threshold
邊寫入：  confidence ≥ edge_threshold
兩個閾值獨立判斷
```

---

## §11 敘事層（LCM DAG）

### 獨立性

敘事層是完全獨立的平行層，擁有自己的存儲結構，不寫回 Obsidian Vault。不與 SSOT B 互相汙染。

### 四層壓縮結構

| Level | 內容 | 時間粒度 |
|-------|------|----------|
| Level 0 | 今日事件（原始） | 日 |
| Level 1 | 週摘要（壓縮） | 週 |
| Level 2 | 月摘要（高度壓縮） | 月 |
| Level 3 | 年摘要（結構性轉移） | 年 |

### 按需展開機制

每個摘要節點保留 `event_ids` 指針。LLM 在摘要中偵測到語意信號時，主動觸發展開，取出原始認識論事件細節。不是所有 event_ids 都被展開，只有推理需要的。

展開方向單向（壓縮→原始），深度固定（最多 4 層），不需要圖引擎處理。

### 時序語意的承載

時序語意存在於敘事層，以 LCM 壓縮的日記體呈現。時間差（如「14 個月」）從未被存儲在任何一層，它在推理時由 LLM 計算兩個日期差而湧現。

---

## §12 Agent 工具箱

### 五個基礎工具

| 工具 | 回答的問題 | 查詢方式 |
|------|-----------|----------|
| 向量索引 | 「什麼跟這段語意最近」 | 語意相似度 |
| Kuzu (GraphDB) | 「什麼與什麼有關係」 | 圖遍歷 |
| DuckDB | 「符合什麼條件的結構化紀錄」 | SQL (Parquet) |
| LCM 摘要檢索 | 「這段時期的敘事是什麼」 | 階層式摘要檢索 |
| LCM 展開 API | 「這個摘要的原始細節是什麼」 | 按需展開至下層 |

### 向量索引

**索引範圍**：

| 索引來源 | 嵌入粒度 |
|----------|----------|
| SSOT A（對話紀錄） | 對話段落 / chunk |
| SSOT B（Obsidian 筆記） | 筆記段落 / chunk（含 wikilinks 上下文） |
| LCM DAG 敘事內容 | 每個 Level 0-3 的摘要段落 |
| Kuzu 節點描述 | 每個 Concept / Session / Insight 節點的語意描述 |

**排除**：Event Log——結構化的認識論事件的查詢模式是精確的時序篩選與聯合，不是語意相似度。

**輕量入口**：向量索引可作為系統的輕量入口，允許 Agent 跳過完整的 GraphRAG 流程，直接取回語意最接近的幾個片段。Agent 自主決定是否需要升級為完整的多工具查詢。

### DuckDB 的完整查詢範圍

| 資料來源 | 查詢內容 | 格式 |
|----------|----------|------|
| Event Log | 認識論事件的時序篩選與聚合 | Parquet |
| Pipeline 中間產物 | Session 統計、cluster 分佈、pkm_score 計算 | Parquet |
| SSOT A metadata | 對話日期、長度、檔案索引 | CSV / Parquet |
| SSOT B frontmatter | domain、tags、overrides 等 YAML 欄位 | 解析後的 Parquet |
| LCM DAG metadata | level、date_range、event_ids、concept_anchors | Parquet |

**DuckDB 不觸及的範疇**：非結構化文本內容（→ 向量索引）、圖拓撲遍歷（→ Kuzu）、LCM DAG 層級展開（→ LCM 展開 API）、敘事內容的語意（→ 向量索引）。

### LCM 摘要檢索與展開 API

兩個獨立工具，對應兩個獨立的 Agent 決策：

- **LCM 摘要檢索**：取出特定時期的敘事摘要（Level 0-3）。Agent 可能檢索一個 Level 2 月摘要就已足夠。
- **LCM 展開 API**：將特定摘要節點按需展開到下一層的細節。Agent 自主判斷是否展開、展開到什麼深度。

DuckDB 只查詢 LCM DAG 的結構化 metadata。摘要的敘事內容檢索與層級展開由 LCM DAG 的獨立 API 處理。

### 與 DuckDB 的分工

```
向量索引：語意相似度，非結構化查詢（「什麼跟這段話最像」）
DuckDB：  精確條件篩選，結構化查詢（「過去三個月 ViewShifted 超過 3 次的概念」）

同一個資料實體可同時被兩者觸及，但觸及的「面」不同：
  Obsidian 筆記 → DuckDB 查 frontmatter / 向量索引查正文語意
  LCM 摘要     → DuckDB 查 metadata    / 向量索引查敘事內容
```

---

## §13 ETL Pipeline

### 合法操作邊界

ETL 層只做「結構性的最小判斷」——剛好足以讓下游工具運作，但不多一步進入語意詮釋的領域。

| 合法（ETL 該做的） | 非法（ETL 不該做的） |
|---|---|
| 辨識概念錨點（讓 Kuzu 有節點可遍歷） | 完整表徵概念的語意與關係 |
| 三值的二元維度標註（讓物化程序有最低限度的信號） | 精確分類認知事件的類型 |
| 存儲兩端上下文片段（讓 LLM 在查詢時有素材） | 預先詮釋上下文片段的語意 |
| 字串正規化（讓同一表面形式不重複） | 語意等價判斷（embedding 比對、LLM 合併） |
| 保留疑似重複為獨立節點 | 積極合併灰色地帶的概念 |

### 概念抽取

- 目標：辨識足以標記主題座標的錨點概念（拓撲骨架，非知識表徵）
- 粒度：無先驗答案，從 POC 迭代中校準
- 輸出格式：概念標籤的字串列表（不要求結構化三元組）

### 字串正規化

```
合法操作：
  - 大小寫統一（全部 lowercase）
  - 空格/標點正規化（multiple spaces → single，去除尾部標點）
  - 完全相同的正規化結果 → 合併

到此為止。不做 embedding 相似度比對，不做 LLM 判斷，不維護別名表。
```

### 模糊去重的消除

去重不再是獨立步驟，而是社群偵測的副產品：

```
概念抽取 → 字串正規化（僅此）→ 建圖（帶重複）→ 社群偵測
                                                    ↓
                                            社群結構即軟去重結果
```

如果兩個名稱真的指向同一個概念，它們會反覆出現在相同的 Session 群裡。共現信號是純粹的結構性事實，不需要語意判斷。

### Wikilinks 的 ETL 處理

```
反向連結上下文  → 向量索引覆蓋
懸空連結        → 生成清單存為 Parquet（gap detection 信號源）
別名連結        → 保留在原始筆記中
連結密度        → 計算為結構化指標存入 Parquet
```

語意不預先詮釋。

### ETL 非確定性的控制

Pipeline 中 LLM 參與的所有階段，其輸出不保證跨版本一致。系統通過嚴格的 prompt 設計、結構化輸出約束、與可復現的上下文組裝策略，將非確定性控制在不影響架構不變量的範圍內。Event Log 因此具有不可替代性——一旦生成即不可從原料精確重建。

---

## §14 GraphRAG 查詢架構

### 跨層 JOIN 的非法性

```
錯誤思維：存儲層負責關聯 → 查詢層取結果
正確思維：存儲層各自完整 → 查詢層組裝 context → LLM 發現關聯
```

各層從未直接對話。LLM 是唯一的跨層介面。

### 查詢流程

以五個獨立工具為基礎，Agent 自主組合。典型的完整 GraphRAG 流程：

```
Step 1：入口選擇（Agent 決策）
  選項 A：向量索引（語意相似度入口）
  選項 B：Kuzu（圖遍歷入口）
  選項 C：DuckDB（結構化條件入口）
  Agent 可能只用一個入口，也可能組合多個

Step 2：圖遍歷（Kuzu）
  在 GraphDB 中定位相關概念節點，展開相鄰 Session 節點
  取得 Session 攜帶的各層指針

Step 3：敘事檢索（LCM 摘要檢索）
  根據 narrative_ref，取出壓縮的日記體摘要
  近期 raw（Level 0），遠期壓縮（Level 1-3）

Step 4：按需展開（LCM 展開 API + DuckDB）
  LLM 在摘要中偵測到語意信號時，主動觸發展開
  取出原始認識論事件細節
  DuckDB 提供結構化的時序篩選

Step 5：LLM 合成
  輸入：拓撲子圖 + 壓縮敘事 + 展開的關鍵事件 + 個人側寫
  輸出：湧現的跨層語意
```

不存在固定的查詢管線。Agent 可能只用向量索引取回幾個片段就足夠，也可能走完整流程。

---

## §15 POC 開發路徑

### 核心假設

POC 驗證的是整個系統架構可行性的前提假設：

> 從對話紀錄中，可以透過 LLM 抽取出足以構成有意義拓撲骨架的概念錨點。

### Pipeline 概覽

```
Stage 1 ─► Stage 2 ─► Stage 3 ─► Stage 4 ─► Stage 5 ─► Stage 6
 JSONL      概念        字串       共現圖      社群        視覺化
 解析       抽取        正規化     建構        偵測        + 評估
                ▲                                           │
                └──── prompt 迭代迴圈（核心瓶頸）─────────────┘
```

核心瓶頸在 Stage 2（概念抽取 prompt 的迭代校準）。Stage 3 因修訂十五壓縮為純字串正規化。認識論事件偵測從 POC 關鍵路徑中移除，延遲到概念抽取穩定後獨立迭代。

### POC 範圍外的組件

Kuzu 整合、Event Log 建立、敘事層、向量索引、Agent 工具箱——均在 POC 成功後依序建設。

詳細的 Stage 規格、決策閘門、評估標準與迭代策略見獨立的 POC 操作文件。

---

## §16 技術棧與約束條件

### 存儲與查詢

| 組件 | 技術 | 角色 |
|------|------|------|
| 結構化查詢引擎 | DuckDB | 通用 SQL 查詢，直接讀寫 Parquet |
| 結構化存儲 | Parquet | Event Log、Pipeline 中間態、metadata |
| 圖資料庫 | Kuzu | 當前知識拓撲，多跳遍歷 |
| 向量索引 | 待定（POC 後選型） | 粗粒度語意相似度 |

### 圖與社群偵測（POC 階段）

| 組件 | 技術 |
|------|------|
| 圖建構與分析 | networkx |
| 社群偵測 | Louvain（python-louvain） |
| 視覺化 | pyvis |

### LLM

| 角色 | 技術 | 備註 |
|------|------|------|
| 本地推理（ETL 抽取） | Qwen 3.5 4B/9B | KV cache Q8 量化 |
| 主 LLM（推理層） | 雲端 API | 唯一的非本地依賴 |

### 硬體約束

- GPU：RTX 3070 Ti（8GB VRAM）
- 本地模型受限於 VRAM，影響可用模型大小與推理速度

### 自定工具

| 工具 | 來源 |
|------|------|
| JSONL DAG Engine | github.com/ryanwaha/JSONL-DAG-engine |

### 筆記系統

| 工具 | 角色 |
|------|------|
| Obsidian | SSOT B 的寫入介面 |

### 部署模式

全本地部署，除主 LLM API。雲端 API 的供應商依賴是非技術性的供應鏈風險，需持續追蹤。

### 語料規模

- SSOT A：~300MB，100-500 個 JSONL 檔案
- 目前為線性結構（非分支 DAG）

---

## 附錄 A：設計原則速查表

```
元原則  脈絡相關的語意判斷 → 存儲層固化 = 範疇錯誤

  一  GraphDB 是衍生物，永遠不直接編輯
  二  兩個 SSOT 管轄不同認識論領域，不強行合併
  三  Frontmatter 是高優先級影響信號，而非直接賦值
  四  Wikilinks 是意圖的表達，其語意在推理時湧現
  五  漂變是一等公民，以 Event Sourcing 模式承載
  六  GraphDB 不以時間作為查詢維度
  七  跨層 JOIN 非法，語意由 LLM 在推理時湧現
  八  Session 是分析產出，其身份由邊的集合定義
  九  ETL 的非確定性以 context engineering 控制
  十  Agent 的工具彼此獨立，不存在固定的查詢管線
 十一  DuckDB 是結構化資料的通用查詢引擎，不綁定特定層
 十二  向量索引是系統的粗粒度激活入口
 十三  概念節點的職責是拓撲骨架，不是知識表徵
 十四  認識論事件以正交的三值維度標註，不做離散分類
 十五  模糊去重不在 ETL 層執行，由社群結構的湧現取代
```

---

## 附錄 B：術語表

| 術語 | 定義 |
|------|------|
| SSOT | Single Source of Truth。系統中不可變的原始來源 |
| SSOT A | 對話紀錄（JSONL DAG 格式），被動生成，不可修改 |
| SSOT B | Obsidian Vault（筆記 + frontmatter + wikilinks），主動撰寫，人工維護 |
| Session | 對原始對話執行認識論分析後的產出物，GraphDB 中的核心節點類型。其身份由邊的集合定義 |
| Concept | 概念錨點節點，提供 Kuzu 可遍歷的拓撲骨架。不是知識表徵 |
| Self | 認知主體節點，系統的錨點。整個圖的語意由這個節點的存在而成立 |
| Event Log | Append-only 的認識論事件流，存儲為 Parquet，由 DuckDB 查詢。SSOT A + B 的衍生物，但不可精確重建 |
| pkm_score | 節點的動態激活閾值，反映概念在認知空間中的活躍程度。激活增強 + 時間衰減 |
| confidence | 邊的動態置信度，反映兩個概念之間關係的可靠程度。與 pkm_score 正交 |
| LCM DAG | Lossy Compression Model 的 DAG 結構，敘事層的存儲形式。四層壓縮（Level 0-3），可按需展開 |
| GraphRAG | Graph-based Retrieval Augmented Generation。利用圖結構增強 LLM 推理的查詢架構 |
| Kuzu | 嵌入式圖資料庫，管轄當前知識拓撲 |
| DuckDB | 嵌入式列式分析引擎，系統的結構化資料通用查詢引擎 |
| Parquet | 列式存儲格式，系統中所有結構化資料的持久化格式 |
| Provenance | 節點/邊屬性的來源追蹤，記錄主要信號來源、置信度、參與信號列表。存在於 GraphDB 但不參與遍歷 |
| Frontmatter | Obsidian 筆記的 YAML 元數據區塊，作為高權重先驗參與多信號合成 |
| Wikilinks | Obsidian 的內部連結語法 `[[概念]]`，承載主觀意圖，語意在推理時湧現 |
| 三值維度模型 | 認識論事件的標註框架：structural_change、tension、integration，每個維度為 true / false / null |
| 物化 | 從 Event Log 確定性生成 GraphDB 的過程 |
| 社群偵測 | 透過 Louvain 等演算法從圖的共現模式中識別出概念群組，同時作為軟去重的機制 |
| Context Engineering | 透過嚴格的 prompt 設計與結構化輸出約束，控制 LLM 推斷的非確定性 |
| JSONL DAG | NexCortex 的對話紀錄格式，每個節點包含 q、a、sum_text、parents 欄位，以 ULID 作為 ID |

---

*文件日期：2026-03-26*
*性質：項目啟動說明，收斂自 NexCortex 系列架構文件 00-04 的最終狀態*
