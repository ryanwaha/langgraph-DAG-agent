

> 基於 2026-03-24 架構審視討論（第二輪），針對原始架構文件中底層檢索系統的職責定義、工具邊界與 Agent 查詢架構的完整修正。 本文件獨立於第一輪修訂說明（六項結構性模糊的收斂），聚焦於「Agent 的工具箱裡到底有什麼」這個問題。

---

## 討論脈絡

### 起點：文件中 DuckDB 職責的模糊

原始架構文件將 DuckDB 與 Event Log 綁定（§4：「DuckDB · Append-only · 時序認識論事件流」），同時在 §5 提及「統計聚合（OLAP）」但從未展開。審視發現四個具體模糊點：

1. **「統計聚合」從未被定義**——pkm_score 計算、cluster 分佈分析、漂變偵測等職責在先前討論中確立，但文件中完全不存在。
2. **ETL 中間態存儲與 Event Log 的關係未釐清**——是否共用同一個 DuckDB 實例。
3. **GraphRAG 查詢中 DuckDB 的參與時機不明**——文件 §9 只在 Step 3（按需展開）提及 DuckDB，但先前討論中 DuckDB 也參與了查詢前的時間預篩選。
4. **pkm_score / confidence 的計算歸屬未定義**——動態計算由誰執行、何時觸發。

### 核心前提的確立

討論首先確立了一個影響所有後續決策的前提：

> **系統的查詢主要由 Agent 自律執行。架構提供的是一組獨立的工具與框架，允許推理湧現。不存在 hardcoded 的查詢管線。**

這意味著底層系統的設計目標不是「回答特定查詢」，而是「提供 Agent 可自主組合的工具箱」。

### 推導路徑

```
DuckDB 職責模糊
  → 追問 DuckDB 的本質（嵌入式列式分析引擎）
  → 發現其外部查詢能力（直接讀寫 Parquet，不需導入）被完全忽略
  → 重新定位：DuckDB 是引擎，不是容器
  → 連帶重新定義所有檢索系統的邊界
  → 向量索引定位為獨立的基礎引擎
  → LCM DAG 拆分為摘要檢索 + 展開 API
  → Obsidian 從查詢引擎中退出
  → Wikilinks 的語意不被預先詮釋
  → 收斂為五個獨立工具的 Agent 工具箱
```

---

## 修訂七：DuckDB 從「Event Log 容器」重新定位為「結構化資料通用查詢引擎」

### 原文問題

文件 §4 將 DuckDB 與 Event Log 綁定：「DuckDB · Append-only · 時序認識論事件流」。這是一個範疇錯誤——把引擎等同於它查詢的其中一個資料集。

DuckDB 的核心設計特性是**直接查詢外部檔案**（Parquet、CSV），不需要先導入。它不「擁有」任何資料，它「觸及」所有結構化資料。

### 修正

> **DuckDB 是整個系統的結構化資料查詢引擎，不綁定特定層。**
> 
> 它以嵌入式 library 形式運行在 Agent 進程中，按需讀取任何 Parquet / CSV / 結構化檔案。Event Log 只是它查詢的資料集之一，不是它的身份。

### DuckDB 的完整查詢範圍

```
資料來源                    查詢內容                         格式
────────────────────────────────────────────────────────────────
Event Log                  認識論事件的時序篩選與聚合         Parquet
Pipeline 中間產物           Session 統計、cluster 分佈、       Parquet
                           pkm_score 計算
SSOT A metadata            對話日期、長度、檔案索引           CSV / Parquet
SSOT B frontmatter         domain、tags、overrides            解析後的 Parquet
                           等 YAML 欄位
LCM DAG metadata           level、date_range、                Parquet
                           event_ids、concept_anchors
```

### DuckDB 不觸及的範疇

```
非結構化文本內容        → 向量索引
圖拓撲遍歷              → Kuzu
LCM DAG 層級展開        → LCM 展開 API
敘事內容的語意          → 向量索引
```

### 先前的「雙重角色」問題消失

「Event Log 存儲與 ETL 中間態是否共用同一個 DuckDB 實例」不再是問題——DuckDB 不是容器，沒有「存在裡面」的概念。所有 Parquet 檔案都在磁碟上，DuckDB 按需讀取。

### pkm_score / confidence 計算歸屬

pkm_score 與 confidence 的激活增強與時間衰減計算自然發生在 DuckDB 側（聚合查詢、窗口函數），計算結果存為 Parquet，物化程序讀取後判斷閾值決定是否寫入 GraphDB。

### 影響段落

§4 架構圖中 DuckDB 的描述、§5 分工表、§9 GraphRAG 查詢流程。

---

## 修訂八：向量索引作為獨立的基礎檢索引擎

### 原文問題

原始架構文件完全未定義向量索引的存在、歸屬與角色。先前討論中提出三個選項（DuckDB VSS、Kuzu 原生、獨立 Faiss）但未收斂。

### 修正

向量索引是系統中與 DuckDB、Kuzu 同級的**基礎底層引擎**，維護為獨立的向量資料庫。

> **向量索引的角色：粗粒度的檢索來源與激活入口。**
> 
> 它執行擴散激活——相關度高的內容被點亮，相關度低的內容自然被蓋過。不做精確篩選，不做結構化查詢，只回答「什麼跟這段語意最相近」。

### 索引範圍

```
索引來源                嵌入粒度
────────────────────────────────────────
SSOT A（對話紀錄）     對話段落 / chunk
SSOT B（Obsidian 筆記） 筆記段落 / chunk（含 wikilinks 上下文）
LCM DAG 敘事內容       每個 Level 0-3 的摘要段落
Kuzu 節點描述           每個 Concept / Session / Insight 節點的語意描述
```

**排除 DuckDB（Event Log）**——結構化的認識論事件（`ConceptElaborated {subject, from, to, date}`）的查詢模式是精確的時序篩選與聯合，不是語意相似度。對事件做 embedding 搜尋會產生大量語意噪音。

### 輕量入口

向量索引可作為系統的輕量入口，允許 Agent 跳過完整的 GraphRAG 流程，直接取回語意最接近的幾個片段作為 context。Agent 自主決定是否需要升級為完整的多工具查詢。

### 與 DuckDB 的分工

```
向量索引：語意相似度，非結構化查詢（「什麼跟這段話最像」）
DuckDB：  精確條件篩選，結構化查詢（「過去三個月 ViewShifted 超過 3 次的概念」）

同一個資料實體可同時被兩者觸及，但觸及的「面」不同：
  Obsidian 筆記 → DuckDB 查 frontmatter / 向量索引查正文語意
  LCM 摘要     → DuckDB 查 metadata    / 向量索引查敘事內容
```

### 影響段落

§4 系統層次架構圖需補充向量索引層、§5 分工表需新增向量索引、§9 GraphRAG 查詢流程需補充向量搜尋作為可選起點。

---

## 修訂九：LCM DAG 拆分為兩個獨立的 Agent 工具

### 原文問題

原始架構文件將 LCM DAG 作為單一層描述，未區分「檢索摘要」與「展開摘要」兩個操作的獨立性。

### 修正

LCM DAG 在 Agent 工具箱中拆分為兩個獨立工具：

> **LCM 摘要檢索**：取出特定時期的敘事摘要（Level 0-3）。Agent 可能檢索一個 Level 2 月摘要就已足夠，不需要展開。
> 
> **LCM 展開 API**：將特定摘要節點按需展開到下一層的細節。Agent 自主判斷是否展開、展開到什麼深度。

拆分的理由：

- 「檢索」與「展開」是兩個獨立的 Agent 決策，不應耦合。
- 展開操作直接影響 context 的噪聲量——由 Agent 而非系統決定是否展開，保持了噪聲控制的自主權。
- LCM DAG 的深度固定（最多 4 層），展開方向單向（壓縮→原始），不是需要圖引擎處理的遞迴遍歷問題。

### DuckDB 與 LCM DAG 的關係

DuckDB 只查詢 LCM DAG 的**結構化 metadata**（level、date_range、event_ids、concept_anchors）。摘要的敘事內容檢索與層級展開由 LCM DAG 的獨立 API 處理。

### 影響段落

§4 敘事層描述、§9 GraphRAG Step 2-3 的描述。

---

## 修訂十：Obsidian 從查詢引擎退出——純寫入介面

### 原文問題

原始架構文件 §9 將 Obsidian 列為四層職責之一：「Obsidian — 意圖宣告 —『你主動認為什麼』」。這暗示 Obsidian 在查詢時是一個獨立的檢索介面。

### 修正

Obsidian 的所有可查詢內容已被其他引擎完整覆蓋：

```
Obsidian 筆記的組成      查詢時由誰負責
──────────────────────────────────────
Frontmatter (YAML)    →  DuckDB（結構化欄位查詢）
筆記正文語意           →  向量索引（語意相似度）
Wikilinks 圖拓撲       →  Kuzu（ETL 物化後的邊）
Wikilinks 語意意圖      →  向量索引（上下文句的 embedding）+ LLM 推理時湧現
```

> **Obsidian 是 SSOT B 的編輯介面，不是 Agent 的查詢工具。**
> 
> Agent 在查詢時不直接存取 Obsidian Vault。它透過 DuckDB 查 frontmatter，透過向量索引查正文語意，透過 Kuzu 查 ETL 物化後的連結結構。

### 影響段落

§9 四層職責定位中 Obsidian 的描述需修正為「SSOT B 的寫入介面」。

---

## 修訂十一：Wikilinks 的語意不被預先詮釋

### 原文問題

設計原則四稱「Wikilinks 是合法的手動邊宣告介面」，隱含 ETL 會將 wikilinks 機械式解析為結構化的關係邊。但 wikilinks 的本質是**主觀意圖**——同一個 `[[概念A]]` 在不同語境中可能承載完全不同的意圖。

### 修正

> **Wikilinks 的語意不由 ETL 預先詮釋，而在推理時由 LLM 湧現。**
> 
> Wikilinks 及其周圍的上下文句透過向量索引被 LLM 看到，LLM 自行理解「為什麼你在這個脈絡下寫了這個連結」。這與原則七（語意由 LLM 在推理時湧現）完全一致。

機械式解析 wikilinks 為 `(source, target, relation_type)` 等於在 ETL 層強制詮釋一個本質上模糊的主觀信號。使用者需要做的是在寫 wikilinks 時提供足夠的上下文讓模型能理解意圖——這是對 SSOT B 信號品質的投資，是可接受的權衡。

Wikilinks 的幾個特殊屬性在此框架下的處理方式：

```
反向連結上下文  → 向量索引覆蓋（上下文句的 embedding）
懸空連結        → ETL 生成清單存為 Parquet（gap detection 信號源）
                  DuckDB 可查，但語意不預先詮釋
別名連結        → 保留在原始筆記中，LLM 在推理時可見
連結密度        → ETL 計算為結構化指標存入 Parquet，DuckDB 可查
```

### 設計原則四的修正

原則四從「Wikilinks 是合法的手動邊宣告介面」修正為：

> **原則四（修正版）：Wikilinks 是意圖的表達，其語意在推理時湧現**
> 
> Wikilinks 不被 ETL 機械式解析為結構化邊。它們保留在原始上下文中，透過向量索引被 LLM 看到，由 LLM 在推理時自行理解其意圖。ETL 只抽取結構化指標（懸空連結清單、連結密度），不詮釋連結的語意。

### 影響段落

§3 Wikilinks 相關描述、設計原則四。

---

## 修訂後的 Agent 工具箱

### 五個基礎工具

```
工具                回答的問題                        查詢方式
─────────────────────────────────────────────────────────────
向量索引             「什麼跟這段語意最近」             語意相似度
                     索引：SSOT A/B 內容、LCM 敘事、
                     Kuzu 節點描述

Kuzu (GraphDB)      「什麼與什麼有關係」               圖遍歷
                     當前拓撲、多跳路徑、社群結構

DuckDB              「符合什麼條件的結構化紀錄」        SQL (Parquet)
                     Event Log、Pipeline 中間態、
                     SSOT A metadata、SSOT B frontmatter、
                     LCM DAG metadata

LCM 摘要檢索        「這段時期的敘事是什麼」            階層式摘要檢索

LCM 展開 API        「這個摘要的原始細節是什麼」        按需展開至下層
```

### 工具使用原則

> **所有工具可按需獨立取用，交由 Agent 與語境決定組合方式。**
> 
> 不存在 hardcoded 的查詢管線。Agent 可能只用向量索引（輕量入口），也可能組合全部五個工具（完整 GraphRAG），完全取決於推理需要。

### 與原始架構文件的對照

```
原始文件的「四層職責」         修訂後的工具歸屬
──────────────────────────────────────────────────
GraphDB (Kuzu)  拓撲真相    → Kuzu（不變）
Event Log       事實存檔    → DuckDB 查詢的資料集之一（非綁定）
敘事層          時序語意    → LCM 摘要檢索 + LCM 展開 API（拆分）
Obsidian        意圖宣告    → 退出查詢引擎，內容由 DuckDB + 向量索引覆蓋
（未定義）                  → 向量索引（新增為基礎引擎）
```

---

## 修訂後的設計原則變動

|#|原則|狀態|
|---|---|---|
|四|~~Wikilinks 是合法的手動邊宣告介面~~ → **Wikilinks 是意圖的表達，其語意在推理時湧現**|**修正**（修訂十一）|
|十|**（新增）Agent 的工具彼此獨立，不存在固定的查詢管線**|**新增**|
|十一|**（新增）DuckDB 是結構化資料的通用查詢引擎，不綁定特定層**|**新增**|
|十二|**（新增）向量索引是系統的粗粒度激活入口，覆蓋除 Event Log 外的所有語意來源**|**新增**|

---

_修訂日期：2026-03-24_ _依據：架構審視討論第二輪（底層檢索引擎的職責定義與 Agent 工具箱收斂）_ _前置文件：「第二大腦」宏觀架構修訂說明（第一輪，六項結構性修正）_