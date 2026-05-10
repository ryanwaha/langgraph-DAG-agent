
> 基於 2026-03-24 架構審視討論，針對原始架構文件的六項結構性修正。

---

## 修訂一：SSOT 階梯化（非扁平）

### 原文問題

文件在不同段落做出三個互斥宣告：§2 稱「兩個 SSOT」、§7 稱「Event Log 是唯一真正的 SSOT」、§12 的不變量暗示 Event Log 可重建一切。三者不能同時為真。

### 修正

SSOT 結構為**階梯式**，而非扁平：

```
SSOT A + B（不可變原料）
    ↓  ETL Pipeline（含 LLM，非確定性）
Event Log（衍生但不可精確重建的中間產物）
    ↓  物化程序（確定性）
GraphDB（可拋棄的末端視圖）
```

- SSOT A（對話紀錄）與 SSOT B（Obsidian Vault）是系統的**不可變原始來源**。
- Event Log 是兩者的衍生物，但因 ETL 包含 LLM 推斷（非確定性函數），**一旦生成即不可從原料精確重建**。
- GraphDB 可從 Event Log 確定性重建，是完全可拋棄的。

### 系統不變量（修正版）

> - 從 Event Log 出發，可確定性重建任意歷史時間點的 GraphDB。
> - 從 SSOT A + B 出發，可重新生成 Event Log（**近似，非精確**）。
> - Event Log 因此具有不可替代性，需要備份策略。

### 影響段落

§2「兩個來源，一個投影」、§7「Event Log 的最終地位」、§12「系統的唯一不變量」。

---

## 修訂二：ETL 的確定性限制——Context Engineering 作為控制手段

### 原文問題

文件隱含 Event Log 可從 SSOT 確定性重建，但 ETL 中的 LLM 語意抽取引入不可消除的非確定性。

### 修正

承認 LLM 抽取的非確定性是系統的固有特性，不試圖消除，但透過**扎實的 context engineering** 將其控制在可接受範圍內。

新增設計原則：

> **原則九（新增）：ETL 的 LLM 推斷具有不可消除的非確定性，以 context engineering 實現可控性**
> 
> Pipeline 中 LLM 參與的所有階段（語意抽取、事件分類、關係推斷），其輸出不保證跨版本一致。系統通過嚴格的 prompt 設計、結構化輸出約束、與可復現的上下文組裝策略，將非確定性控制在不影響架構不變量的範圍內。

### 影響段落

§7 Event Sourcing 相關段落需補充此前提。

---

## 修訂三：敘事層獨立——不寫回 Obsidian

### 原文問題

先前討論中曾提及每日敘事「寫回 Obsidian Daily Notes」，這會產生循環依賴：`SSOT B → ETL → Event Log → 敘事層 → 寫回 SSOT B`，且自動生成的內容會汙染 SSOT B「人工意圖宣告」的性質。

### 修正

敘事層（LCM DAG）是**完全獨立的平行層**，擁有自己的存儲結構，不寫回 Obsidian Vault。

```
SSOT B（Obsidian）：純人工維護的意圖宣告，不含任何自動生成內容
敘事層（LCM DAG）：Pipeline 自動產出的時序敘事，獨立存儲
```

兩者不互相汙染。循環依賴消失。

LCM 壓縮的特殊性（近期原始 + 遠期壓縮的 DAG 結構、可展開的 event_id 指針）本身就決定了它不適合以 markdown 筆記形式存在於 Obsidian 中。

### 影響段落

§4 系統層次架構圖中敘事層的描述、§8 相關段落。

---

## 修訂四：GraphDB 時間解耦原則精確化

### 原文問題

§8 宣稱「時間不進 GraphDB」、在邊上加 `created_at` 是「類型錯誤」。但 Self 節點的邊設計（`UNDERSTOOD_AT {date}`、`CHANGED_VIEW_ON {from_session, to_session}`）直接攜帶時間戳，與此原則矛盾。

### 修正

原則六修改為：

> **原則六（修正版）：GraphDB 不以時間作為查詢維度**
> 
> GraphDB 的邊與節點**可攜帶** date 與 provenance 作為 metadata，但這些欄位嚴格遵守以下約束：
> 
> - **A. 不作為遍歷條件**：Cypher 查詢永遠不寫 `WHERE edge.date > ...`。時間篩選只發生在 DuckDB 側。
> - **B. 不作為排序依據**：GraphRAG 組裝 context 時，不按邊的 date 排序。排序由敘事層 LCM DAG 結構決定。
> - **C. LLM 可見**：組裝給 LLM 的 context 中，這些 metadata 作為**被動可見的輔助信號**存在，LLM 自行決定是否利用。
> 
> 時序推理的主通道是敘事層（LCM DAG）。當 GraphDB metadata 與敘事層產生衝突時，以敘事層為準。

Self 節點的邊（如 `UNDERSTANDS {date, confidence}`）在此框架下合法——date 存在但不被 Kuzu 查詢觸碰。

### 影響段落

§8「GraphDB 與時間的解耦」、§10 Self 節點邊的設計、設計原則六。

---

## 修訂五：Provenance 的邊界——存在但不參與檢索

### 原文問題

§3 強調節點屬性記錄完整 provenance（信號來源、置信度、參與信號列表），但 provenance 天然包含時序資訊（哪個 Session、哪次 Pipeline）。如果 GraphDB 節點攜帶這些 metadata，「與時間完全解耦」的宣稱不成立。

### 修正

Provenance 遵循與 date 相同的 A+B 原則：

- 存在於 GraphDB 節點/邊的屬性中（供 LLM 參考與 debug 用途）
- **不參與** Kuzu 的圖遍歷與排序邏輯
- LLM 在推理時可見，作為判斷信號可靠度的輔助依據

Provenance 中允許攜帶的欄位：`primary_source`（主要信號來源類型）、`confidence`（置信度）、`signal_list`（參與信號列表）、`source_session_id`（來源 Session，隱含日期但不直接暴露為時間欄位）。

### 影響段落

§3 Frontmatter 與信號合成、設計原則三。

---

## 修訂六：pkm_score 與 confidence——耦合但獨立

### 原文問題

pkm_score（Session 的激活閾值）的定義模糊：未明確是靜態計算一次，還是動態更新。且與 confidence（邊的置信度）在概念上高度重疊。

### 修正

**pkm_score 與 confidence 是兩個正交維度，共享梯度模型但各自獨立計算：**

```
pkm_score（節點屬性）：這個概念/Session 在認知空間中有多「活躍」
  ← 被查詢命中、被其他 Session 引用、被 Event 提及 → 增強
  ← 長期未被激活 → 衰減

confidence（邊屬性）：這兩個概念之間的關係有多「可靠」
  ← 被更多 Session 佐證、被更多事件支持 → 增強
  ← 長期未被新證據支持 → 衰減
```

兩者不等價：高 pkm_score 的節點可能有低 confidence 的邊（頻繁提及但關聯不確定），低 pkm_score 的節點之間可能有高 confidence 的邊（冷門但關係確鑿）。

**pkm_score 是動態的**，非一次性計算。更新機制與 confidence 同構（激活增強 + 時間衰減），但數值互不決定。

**物化階段的過濾邏輯：**

```
Event Log → 物化程序 → GraphDB

寫入條件（兩個閾值獨立）：
  節點：pkm_score ≥ node_threshold  → 寫入
  邊：  confidence ≥ edge_threshold → 寫入
```

此設計對應神經元類比的完善：pkm_score 是神經元的靜息電位（基礎活性），confidence 是突觸強度（連結可靠度）。兩者由同一套 Hebbian-like 規則驅動（「越用越強」），但作用在不同的圖元素上。

### 影響段落

§6 Session 節點的神經元類比（pkm_score 部分需補充動態更新機制與衰減梯度）。

---

## 修訂後的設計原則總覽

|#|原則|狀態|
|---|---|---|
|一|GraphDB 是衍生物，永遠不直接編輯|不變|
|二|兩個 SSOT 管轄不同認識論領域，不強行合併|不變|
|三|Frontmatter 是高優先級影響信號，而非直接賦值|不變，provenance 邊界精確化（修訂五）|
|四|Wikilinks 是合法的手動邊宣告介面|不變|
|五|漂變是一等公民，以 Event Sourcing 模式承載|不變|
|六|~~GraphDB 與時間完全解耦~~ → **GraphDB 不以時間作為查詢維度**|**修正**（修訂四）|
|七|跨層 JOIN 非法，語意由 LLM 在推理時湧現|不變|
|八|Session 是分析產出，其身份由邊的集合定義|不變，pkm_score 定義補充（修訂六）|
|九|**（新增）ETL 的非確定性以 context engineering 控制**|**新增**（修訂二）|

---

## 修訂後的系統不變量

> 1. 從 **DuckDB Event Log** 出發，可**確定性**重建任意歷史時間點的 **Kuzu GraphDB** 狀態。
> 2. 從 **SSOT A + B** 出發，可重新生成 Event Log（**近似，非精確**）。
> 3. Event Log 具有不可替代性，需獨立備份。
> 4. GraphDB 是完全可拋棄的計算結果。
> 5. 敘事層（LCM DAG）是獨立的平行層，不寫回任何 SSOT。

---

_修訂日期：2026-03-24_ _依據：架構審視討論（六項結構性模糊的收斂）_