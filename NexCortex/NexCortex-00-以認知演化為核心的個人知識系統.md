## 宏觀架構總結報告

> 本報告紀錄一套以「認知外化」為本體論前提的個人知識管理系統之完整架構設計。 本文不涉及實作細節，專注於架構原則、層次分工與設計哲學。

---

## 一、系統的本體論前提

### 流行 PKM 模型的根本缺陷

現有主流個人知識管理系統（如 Building a Second Brain）的隱含本體論預設為：

> 知識是靜態物件，大腦是存取介面。

此預設在根本上是錯誤的。大腦不存儲知識，它**持續重建知識**。每次「回憶」都是重新激活一個分佈式的激活模式，而非讀取一個文件。認知的本質是動態的拓撲重組，不是靜態的資料存取。

### 本系統的本體論轉移

|維度|流行 PKM|本系統|
|---|---|---|
|知識的性質|靜態物件|激活模式（邊的集合）|
|核心動作|存儲|分析（Pipeline 產出 Session）|
|查詢行為|檢索|推理（語意湧現）|
|時間的角色|元數據|獨立語意層|
|你與系統的關係|使用者|系統的一部分（Self 節點）|
|系統形態|快照|過程|

**核心命題**：你不是在存放想法的地方，而是在構建一個與你一同演化的認知結構的外化。

---

## 二、SSOT 架構：兩個來源，一個投影

### 兩個性質根本不同的 SSOT

```
SSOT A：對話紀錄（plaintext）
  性質：被動生成、隱含知識、高覆蓋低精準、不可回頭修改

SSOT B：Obsidian Vault（筆記 + frontmatter + wikilinks）
  性質：主動撰寫、顯性宣告、低覆蓋高精準、隨時可修正
```

兩個 SSOT 管轄不同的認識論領域，強行合併是錯誤的。它們之間的張力本身就是信號，不是需要消除的噪音。

### GraphDB 是投影，永遠不是 SSOT

```
SSOT A ──┐
          ├──► GraphDB（兩個 SSOT 的可查詢投影）
SSOT B ──┘
```

GraphDB 是衍生物。直接編輯 GraphDB 等同於編輯編譯後的 binary——下次重建即消失，且喪失 provenance。

**系統不變量**：任何時刻，皆可從兩個 SSOT 完整重建 GraphDB。

---

## 三、Obsidian 作為意圖介面

### 信號強度的梯度

Obsidian 文件中，不同結構承載不同的認識論力量：

```
最強  │  frontmatter 顯式欄位     你的明確宣告
      │  wikilinks + 上下文句     你的有意識連結
      │  筆記標題                 你認為值得命名的概念
      │  筆記正文語意             你撰寫時的隱含判斷
最弱  │  自動抽取（對話紀錄）     LLM 的推斷
```

### Frontmatter 是影響信號，而非直接賦值

Frontmatter 不直接決定 GraphDB 節點屬性，而是以**高權重先驗**參與多信號合成：

```
節點屬性 = synthesize({
  frontmatter_explicit:   weight=0.90,
  wikilink_cooccurrence:  weight=0.60,
  llm_extraction:         weight=0.40,
  conversation_context:   weight=0.30,
})
```

每個節點屬性記錄完整的 provenance（主要信號來源、置信度、參與信號列表），使狀態可解釋、可追溯。

### Wikilinks 是合法的手動邊宣告介面

你永遠不需要打開 Cypher shell。想修正圖結構，在 Obsidian 裡撰寫內容，ETL 負責詮釋與解析衝突。

`overrides` frontmatter 欄位是唯一的手動修正介面，且它仍然在 SSOT B 裡，不在 GraphDB 裡。

---

## 四、系統層次的完整架構

```
┌──────────────────────────────────────────────────────────────┐
│                     SSOT 層（唯一真實來源）                   │
│                                                              │
│   SSOT A：對話紀錄（plaintext）                              │
│   SSOT B：Obsidian Vault（筆記 + frontmatter + wikilinks）   │
└───────────────────────────┬──────────────────────────────────┘
                            │ ETL Pipeline（5 Phases）
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    事件層（Event Log）                        │
│                                                              │
│   DuckDB · Append-only · 時序認識論事件流                    │
│   ← 系統的最終 SSOT，可重建任意歷史狀態                      │
└───────────────────────────┬──────────────────────────────────┘
                            │ 每日 Pipeline 產出
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    敘事層（Narrative Layer）                  │
│                                                              │
│   LCM DAG 結構 · 日記體壓縮 · 寫回 Obsidian                  │
│   Level 0：今日事件（原始）                                   │
│   Level 1：週摘要（壓縮）                                     │
│   Level 2：月摘要（高度壓縮）                                 │
│   Level 3：年摘要（結構性轉移）                               │
│   ← 每個摘要節點保留 event_ids 指針，可按需展開              │
└───────────────────────────┬──────────────────────────────────┘
                            │ 物化程序（增量）
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    圖狀態層（GraphDB）                        │
│                                                              │
│   Kuzu · 當前知識拓撲 · 可完全拋棄重建                        │
│   節點：Concept / Session / Note / Self / Insight / Question  │
│   邊：帶 source · confidence · provenance metadata           │
│   ← 只表達當前拓撲，與時間完全解耦                           │
└───────────────────────────┬──────────────────────────────────┘
                            │ GraphRAG（Local + Global Search）
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    推理層                                     │
│                                                              │
│   本地 LLM · 注入個人側寫作為 global context                 │
│   ← 跨層語意在此湧現，不預先計算                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 五、各層的職責分工

|層次|存儲系統|管轄範疇|關鍵性質|
|---|---|---|---|
|SSOT A|Plaintext|行為紀錄|不可修改|
|SSOT B|Obsidian|意圖宣告|人工維護|
|Event Log|DuckDB|認識論事件|Append-only|
|敘事層|LCM DAG / Obsidian|時序語意|日記體，可展開|
|GraphDB|Kuzu|當前拓撲|可重建，無時間|
|推理層|本地 LLM|跨層合成|語意湧現|

**DuckDB 與 Kuzu 的精確分工**：DuckDB 管時序事件流與統計聚合（OLAP）；Kuzu 管當前圖狀態與多跳遍歷（Graph）。兩者協同驅動 GraphRAG，職責不重疊，不競爭。

---

## 六、Session 節點：神經元的類比

### Session 的本體論定位

Session 不是文件的替身，而是**對原始文件執行認識論分析之後的產出物**。

```
對話紀錄.txt ──Pipeline──► Session（分析的物化結果）
（SSOT A，原始文件）        （GraphDB 的公民）
```

原始文件繼續留在 SSOT A，Session 是完全不同類型的存在。兩者不在同一個層次，不需要 JOIN。

### 神經元的精確類比

|神經元|Session|
|---|---|
|細胞體（soma）|Session 節點本身（屬性）|
|樹突（接收信號）|入邊（來自其他 Session 的關係）|
|軸突（發送信號）|出邊（指向 Concept / Insight / Question）|
|突觸權重|邊的 confidence / salience|
|激活閾值|pkm_score|

**核心洞察**：神經元不是「有連結的點」，神經元就是那些連結本身的具現化。Session 同理——**Session 的身份由其邊的集合定義。**

### Session 作為跨層樞紐

Session 節點天然同時屬於多個層次，是各層指針的集合地：

```
Session 節點
├─ source_ref      → SSOT A（原始對話文件）
├─ narrative_ref   → 敘事層（對應的日記體摘要）
├─ event_ids[]     → Event Log（對應的認識論事件）
└─ 圖結構出邊      → Concept / Insight / Question 節點
```

Session 是**通往各層的鑰匙**，而非各層內容的存儲地。

---

## 七、Event Sourcing：漂變作為一等公民

### 認知漂變的性質

人類認知的漂變（drift）不是異常，而是系統必須承載的核心現象。

傳統快照模型無法區分：「這是一直以來的理解」與「這是經過 14 個月修正後的理解」。

### Event Log 的架構邏輯

```
傳統思維：UPDATE node SET domain = "ML"
Event Sourcing：APPEND ViewShifted {
  concept: "HDBSCAN",
  from: "statistics",
  to: "ML/Unsupervised",
  date: ..., evidence: session_id
}
```

GraphDB 節點永遠不被「修改」，只有新事件被追加。當前狀態是事件序列的摺疊（fold）：

```
current_state = event_log.fold(initial_state, apply_event)
```

### 認識論事件類型

|事件類型|語意|
|---|---|
|ConceptElaborated|同一概念，理解層次提升|
|ViewShifted|對同一問題，立場改變|
|ConceptFissioned|一個概念拆分為兩個（解析度提升）|
|ConceptMerged|兩個概念合併（發現同一性）|
|RelationInverted|關係方向釐清|
|ContradictionFlagged|新理解與舊理解衝突，尚未解決|
|ContradictionResolved|矛盾有了答案|

**ConceptFissioned** 是其中信息密度最高的事件——它直接標記了認知解析度的提升時刻。

### Event Log 的最終地位

Event Log 是整個系統中唯一真正的 SSOT。從 Event Log 出發，可以重建任意歷史時間點的 GraphDB 狀態。GraphDB 是完全可拋棄的計算結果。

---

## 八、GraphDB 與時間的解耦

### 時間不進 GraphDB 的根本理由

GraphDB 的邊表達的是**當前拓撲信念**：「你現在相信 A 與 B 有某種關係」。「你是如何、何時形成這個信念」屬於 Event Log 與敘事層的管轄範疇。

混淆兩者是類型錯誤（type error）。在邊上加 `created_at` 不是解法，而是把時序語意以錯誤的形式壓入了拓撲層。

### 時序語意的正確承載層

時序語意存在於**敘事層**，以 LCM 壓縮的日記體呈現：

```
敘事摘要（週 Level 1）：

「本週出現一個長期懸置問題的突破。
distributed consensus 相關的矛盾自 14 個月前標記為 unresolved，
本週在討論 Raft leader election 時突然解消。
解消的關鍵：safety 與 liveness 是兩個獨立約束，而非同一條件的兩面。
[event_ids: E0047, E1823, E2901]」
```

「14 個月」這個語意從未被存儲在任何一層，它在推理時由 LLM 計算兩個日期差而湧現。

---

## 九、GraphRAG：跨層 JOIN 的非法性與湧現的正確設計

### 為何跨層 JOIN 是非法的

預先計算跨層 JOIN 會：

- 把時序語意污染進 GraphDB 的拓撲層
- 讓每次 schema 變動需要重建 JOIN 邏輯
- 消滅「LLM 在推理時自行發現關聯」的可能性

### 湧現的正確機制

```
錯誤思維：存儲層負責關聯 → 查詢層取結果
正確思維：存儲層各自完整 → 查詢層組裝 context → LLM 發現關聯
```

各層從未直接對話。**LLM 是唯一的跨層介面。**

### GraphRAG 的查詢流程

```
Step 1：圖遍歷（Kuzu）
  在 GraphDB 中定位相關概念節點，展開相鄰 Session 節點
  取得 Session 攜帶的各層指針

Step 2：敘事檢索（LCM DAG）
  根據 narrative_ref，取出壓縮的日記體摘要
  近期 raw（Level 0），遠期壓縮（Level 1-3）

Step 3：按需展開（Event Log）
  LLM 在摘要中偵測到語意信號時，主動觸發展開
  取出原始認識論事件細節
  （不是所有 event_ids 都被展開，只有推理需要的）

Step 4：LLM 合成
  輸入：拓撲子圖 + 壓縮敘事 + 展開的關鍵事件 + 個人側寫
  輸出：湧現的跨層語意
```

### 四層職責的最終定位

```
GraphDB（Kuzu）     拓撲真相    「什麼與什麼有關係」
Event Log（DuckDB） 事實存檔    「什麼時候發生了什麼」
敘事層（LCM DAG）   時序語意    「這些事件放在一起意味著什麼」
Obsidian            意圖宣告    「你主動認為什麼」
```

---

## 十、Self 節點與個人側寫

### 以「我」為核心的 Ontology 轉移

傳統知識圖譜以概念為中心節點。本系統以**認知主體**為中心，邊不只是語意關係，而是認識論事件。

```
傳統：[HDBSCAN] -[related_to]→ [Clustering]
本系統：[Self] -[理解了 {date, confidence}]→ [HDBSCAN]
        [Self] -[曾困惑於 {date}]→ [KV Cache]
        [Self] -[CHANGED_VIEW_ON {from_session, to_session}]→ [Concept]
```

### 湧現的個人側寫

以 Self 為錨點構建圖後，從圖的社群結構自然湧現幾類集群：

```
認知偏好集群   ← 傾向什麼樣的思維模式與架構選擇
技術能力集群   ← 哪些領域有深度認識
認知盲區集群   ← 反覆問同類問題、某概念始終模糊
epistemic_status: "implicit" 節點  ← 你頻繁使用但從未在 Obsidian 命名的概念
```

這些集群加在一起，構成**可機器讀取的「你」**，作為 global context 按需注入 LLM。

Self 節點不是系統的使用者，而是系統的**錨點**。整個圖的語意由這個節點的存在而成立。

---

## 十一、設計原則總覽

**一、GraphDB 是衍生物，永遠不直接編輯** 所有修正發生在 SSOT，GraphDB 永遠可從 SSOT 完整重建。

**二、兩個 SSOT 管轄不同認識論領域，不強行合併** 行為紀錄（對話）與意圖宣告（Obsidian）的張力本身是信號。

**三、Frontmatter 是高優先級影響信號，而非直接賦值** 節點屬性由多信號合成，provenance 完整可追溯。

**四、Wikilinks 是合法的手動邊宣告介面** 透過 Obsidian 表達意圖，ETL 負責詮釋，你永遠不碰 GraphDB。

**五、漂變是一等公民，以 Event Sourcing 模式承載** Append-only Event Log 記錄所有認識論事件，GraphDB 是其物化視圖。

**六、GraphDB 與時間完全解耦** 時序語意屬於敘事層，不進 GraphDB。時間戳不是邊的屬性。

**七、跨層 JOIN 非法，語意由 LLM 在推理時湧現** 各層各自完整，LLM 是唯一的跨層介面。

**八、Session 是分析產出，其身份由邊的集合定義** Session 不是文件替身，是認識論分析的物化結果。pkm_score 是激活閾值。

---

## 十二、系統的唯一不變量

> 從 **DuckDB Event Log** 出發，可以重建任意歷史時間點的 **Kuzu GraphDB** 狀態。GraphDB 是完全可拋棄的計算結果。SSOT 的最終形式只有一個：事件流本身。

---

## 十三、這才是「第二大腦」的正確定義

流行定義把第二大腦等同於「組織良好的外部硬碟」，預設知識是靜態物件，大腦是存取介面。

本系統的回答是：

**第二大腦不是存放想法的地方，而是與你一同演化的認知結構的外化。**

它的智能不在存儲層，而在查詢層。存儲層只需要做好自己的職責，所有「有趣的」語意都是推理時的湧現，而非預先計算的結果。隨著 LLM 能力的提升，系統自動變得更聰明，不需要改動任何存儲 schema。

這個設計捕捉到了大腦的本質：**不是讀取，而是重建。不是存儲，而是演化。**

---

_報告涵蓋範圍：系統本體論、SSOT 架構、Obsidian 整合、四層存儲分工、Session 定義、Event Sourcing、時序語意解耦、GraphRAG 湧現機制、Self 節點與個人側寫。_

_尚未展開：ETL Pipeline 細節、Event Log schema、物化策略、GraphRAG 查詢介面實作、gap detection 機制。_