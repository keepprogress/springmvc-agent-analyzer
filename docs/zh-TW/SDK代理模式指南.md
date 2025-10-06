# SDK 代理模式指南

深入了解 SpringMVC Agent Analyzer 的 SDK 代理模式，掌握雙向對話式分析。

## 📋 目錄

1. [什麼是 SDK 代理模式](#什麼是-sdk-代理模式)
2. [與批次模式的差異](#與批次模式的差異)
3. [何時使用代理模式](#何時使用代理模式)
4. [快速開始](#快速開始)
5. [對話模式](#對話模式)
6. [進階用法](#進階用法)
7. [最佳實踐](#最佳實踐)
8. [故障排除](#故障排除)

---

## 什麼是 SDK 代理模式

SDK 代理模式（SDK Agent Mode）是一種**雙向對話式**的分析模式，允許 AI 智能體：

- 🤔 **主動提問** - 當資訊不足時詢問使用者
- 💡 **澄清需求** - 確認分析範圍和目標
- 🔄 **迭代改進** - 根據回饋調整分析策略
- 🎯 **精準分析** - 理解使用者的真實需求

### 傳統批次模式 vs SDK 代理模式

```
批次模式:
使用者 → [提交所有檔案] → AI → [分析] → 結果
       單向，一次完成

代理模式:
使用者 ↔ [對話] ↔ AI ↔ [分析] ↔ 使用者 ↔ 結果
       雙向，迭代改進
```

### 架構圖

```
┌─────────────────────────────────────────────────────────┐
│                      使用者介面                          │
│           (CLI / Web UI / IDE Plugin)                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  SDK Agent Mode       │
         │  (Bidirectional)      │
         └───────┬───────────────┘
                 │
        ┌────────┴─────────┐
        │                  │
        ▼                  ▼
  ┌──────────┐      ┌──────────┐
  │ 使用者   │      │ AI 智能體 │
  │  輸入    │◄────►│  回應    │
  └──────────┘      └──────────┘
        │                  │
        │    [對話循環]    │
        │                  │
        └────────┬─────────┘
                 │
                 ▼
         ┌───────────────┐
         │  分析引擎      │
         │  (LLM-First)  │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │  分析結果      │
         └───────────────┘
```

---

## 與批次模式的差異

### 功能比較

| 特性 | 批次模式 | 代理模式 |
|------|----------|----------|
| **互動方式** | 單向 | 雙向對話 |
| **靈活性** | 固定流程 | 動態調整 |
| **需求澄清** | 不支援 | 支援 |
| **適用場景** | 明確任務 | 探索性分析 |
| **學習曲線** | 簡單 | 中等 |
| **自動化程度** | 高 | 中 |
| **成本** | 可預測 | 可能較高 |

### 使用場景對比

**批次模式適合：**
```python
# 已知要分析什麼，直接批次處理
agent = SpringMVCAnalyzerAgent(mode="batch")
results = await agent.analyze_batch([
    "UserController.java",
    "OrderController.java",
    "ProductController.java"
])
```

**代理模式適合：**
```python
# 需要探索和討論分析策略
agent = SpringMVCAnalyzerAgent(mode="agent")
response = await agent.chat(
    "這個專案很混亂，我想理解它的架構，你有什麼建議嗎？"
)
# AI 可能會問：「我發現有多個 Controller，你想先從哪個開始？」
```

---

## 何時使用代理模式

### ✅ 適合使用代理模式

1. **探索性分析**
   - 不確定專案結構
   - 需要逐步探索程式碼
   - 想了解特定模組的運作

2. **複雜問題診斷**
   - 追蹤 bug 的根源
   - 理解複雜的業務邏輯
   - 分析效能瓶頸

3. **重構規劃**
   - 評估重構影響範圍
   - 找出程式碼異味
   - 規劃遷移策略

4. **學習與理解**
   - 新人 onboarding
   - 理解舊有系統
   - 學習最佳實踐

### ❌ 不適合使用代理模式

1. **批次處理需求**
   - 分析整個專案（數百個檔案）
   - 定期自動化分析
   - CI/CD 整合

2. **明確且簡單的任務**
   - 只想提取路由列表
   - 統計程式碼行數
   - 產生簡單報告

3. **離線或自動化環境**
   - 無法即時互動
   - 需要完全自動化
   - 命令列批次腳本

---

## 快速開始

### 基本範例

```python
import asyncio
from sdk_agent.client import SpringMVCAnalyzerAgent

async def basic_agent_example():
    """基本的代理模式範例"""

    # 初始化代理模式
    agent = SpringMVCAnalyzerAgent(mode="agent")

    # 開始對話
    print("使用者: 請幫我分析 UserController.java")
    response = await agent.chat("請幫我分析 UserController.java")

    # 處理 AI 回應
    while not response['done']:
        print(f"\nAI: {response['message']}")

        # 如果 AI 需要更多資訊
        if response['needs_input']:
            user_input = input("\n使用者: ")
            response = await agent.chat(user_input)
        else:
            # AI 在思考或處理中
            response = await agent.continue_conversation()

    # 獲取最終結果
    print(f"\n分析完成！")
    print(f"結果: {response['result']}")

# 執行
asyncio.run(basic_agent_example())
```

### 對話範例

```
使用者: 請幫我分析 UserController.java

AI: 好的，我會分析 UserController.java。在開始之前，我想確認幾件事：
    1. 您主要想了解什麼？(路由、依賴關係、業務邏輯)
    2. 這個 Controller 有沒有特別需要注意的部分？

使用者: 我想了解所有的路由和依賴關係

AI: 明白了。我會專注於路由和依賴關係。正在分析中...

AI: 分析完成！發現以下資訊：
    - 5 個 REST API 端點
    - 3 個服務依賴 (UserService, EmailService, LogService)
    - 2 個異常處理器
    您想深入了解哪個部分？

使用者: UserService 在哪裡使用？

AI: UserService 在以下方法中使用：
    1. getUser() - 查詢使用者資料
    2. createUser() - 建立新使用者
    3. updateUser() - 更新使用者資料
    需要查看具體的呼叫細節嗎？
```

---

## 對話模式

### 1. 指令式對話

直接下達明確指令：

```python
async def command_pattern():
    agent = SpringMVCAnalyzerAgent(mode="agent")

    # 指令 1: 分析檔案
    response = await agent.chat("分析 UserController.java 的所有路由")

    # 指令 2: 查詢依賴
    response = await agent.chat("找出 UserService 的所有依賴")

    # 指令 3: 比較檔案
    response = await agent.chat("比較 UserController 和 AdminController 的差異")
```

### 2. 問答式對話

以提問方式探索：

```python
async def qa_pattern():
    agent = SpringMVCAnalyzerAgent(mode="agent")

    # 提問 1
    response = await agent.chat("這個專案有幾個 Controller？")

    # 提問 2
    response = await agent.chat("哪個 Controller 最複雜？")

    # 提問 3
    response = await agent.chat("UserController 調用了哪些服務？")
```

### 3. 探索式對話

逐步深入探索：

```python
async def exploration_pattern():
    agent = SpringMVCAnalyzerAgent(mode="agent")

    # 第一步：概覽
    response = await agent.chat("給我這個專案的整體架構概覽")

    # 第二步：聚焦
    response = await agent.chat("我想深入了解使用者管理模組")

    # 第三步：具體問題
    response = await agent.chat("UserController 的 createUser 方法做了什麼？")

    # 第四步：相關分析
    response = await agent.chat("這個方法有沒有安全性問題？")
```

### 4. 診斷式對話

問題診斷與追蹤：

```python
async def diagnostic_pattern():
    agent = SpringMVCAnalyzerAgent(mode="agent")

    # 描述問題
    response = await agent.chat("""
        我在 /users/{id} 端點遇到 500 錯誤，
        幫我追蹤問題可能出在哪裡
    """)

    # AI 可能會回應：
    # "我需要檢查以下幾個地方：
    #  1. UserController.getUserById()
    #  2. UserService.findById()
    #  3. UserRepository
    #  你想從哪個開始？"

    response = await agent.chat("從 UserService 開始")

    # 持續追蹤...
```

---

## 進階用法

### 1. 上下文管理

代理模式會維護對話上下文：

```python
async def context_example():
    agent = SpringMVCAnalyzerAgent(mode="agent")

    # 第一輪對話
    await agent.chat("分析 UserController.java")

    # 第二輪對話（有上下文）
    # AI 知道我們在談論 UserController
    await agent.chat("這個 Controller 有幾個路由？")

    # 第三輪（繼續相同上下文）
    await agent.chat("最複雜的方法是哪個？")

    # 清除上下文，開始新話題
    agent.clear_context()
    await agent.chat("現在分析 OrderController.java")
```

### 2. 多輪交互

處理複雜的多輪交互：

```python
async def multi_turn_example():
    agent = SpringMVCAnalyzerAgent(mode="agent")

    conversation_history = []

    # 持續對話直到使用者說「結束」
    while True:
        user_input = input("\n使用者: ")

        if user_input.lower() in ['結束', 'exit', 'quit']:
            break

        response = await agent.chat(user_input)
        conversation_history.append({
            "user": user_input,
            "agent": response['message']
        })

        print(f"AI: {response['message']}")

        # 如果 AI 需要額外資訊
        while response.get('needs_input'):
            follow_up = input("使用者: ")
            response = await agent.chat(follow_up)
            print(f"AI: {response['message']}")

    # 儲存對話歷史
    save_conversation(conversation_history)
```

### 3. 策略引導

引導 AI 使用特定分析策略：

```python
async def strategy_guided_example():
    agent = SpringMVCAnalyzerAgent(mode="agent")

    # 明確指定分析策略
    response = await agent.chat("""
        使用以下策略分析 UserController：
        1. 先識別所有 public 方法
        2. 對每個方法分析其 HTTP 端點
        3. 追蹤每個端點的依賴鏈
        4. 標記任何潛在的 N+1 查詢問題
        5. 產生完整的依賴關係圖
    """)

    # AI 會遵循這個策略逐步執行
```

### 4. 條件式分析

根據條件動態調整分析：

```python
async def conditional_analysis():
    agent = SpringMVCAnalyzerAgent(mode="agent")

    # 分析並根據結果決定下一步
    response = await agent.chat("分析 UserController 的複雜度")

    complexity = response['result'].get('complexity_score')

    if complexity > 50:
        # 高複雜度 - 深入分析
        response = await agent.chat("""
            複雜度過高，請進行深度分析：
            - 找出最複雜的 3 個方法
            - 建議重構方案
        """)
    else:
        # 低複雜度 - 簡單檢查
        response = await agent.chat("檢查是否符合最佳實踐")
```

### 5. 批次代理混合模式

結合批次處理和代理對話：

```python
async def hybrid_mode():
    # 步驟 1: 批次模式快速掃描
    batch_agent = SpringMVCAnalyzerAgent(mode="batch")
    quick_scan = await batch_agent.analyze_batch(all_files)

    # 步驟 2: 識別問題檔案
    problematic_files = [
        f for f in quick_scan
        if f['complexity_score'] > 50 or f['has_issues']
    ]

    # 步驟 3: 代理模式深入分析問題檔案
    agent_mode = SpringMVCAnalyzerAgent(mode="agent")

    for file in problematic_files:
        print(f"\n深入分析: {file['path']}")
        response = await agent_mode.chat(
            f"深入分析 {file['path']}，找出所有問題並建議解決方案"
        )

        # 與 AI 互動討論解決方案
        while True:
            user_input = input("您的問題（輸入 'next' 繼續下一個）: ")
            if user_input == 'next':
                break

            response = await agent_mode.chat(user_input)
            print(f"AI: {response['message']}")
```

---

## 最佳實踐

### 1. 清晰的提問

**❌ 不好的提問：**
```python
await agent.chat("分析這個")  # 太模糊
await agent.chat("有什麼問題嗎？")  # 範圍太廣
```

**✅ 好的提問：**
```python
await agent.chat("分析 UserController.java 的所有 REST API 端點和依賴關係")
await agent.chat("檢查 UserService.createUser() 方法是否有 SQL 注入風險")
```

### 2. 提供上下文

**❌ 缺乏上下文：**
```python
await agent.chat("這個方法做什麼？")  # AI 不知道是哪個方法
```

**✅ 提供充分上下文：**
```python
await agent.chat("""
    在 UserController.java 的 getUserById() 方法中，
    第 45 行調用了 userService.findById(id)，
    這個方法做了什麼？會拋出什麼異常？
""")
```

### 3. 逐步深入

**❌ 一次性提出所有問題：**
```python
await agent.chat("""
    分析所有 Controller、所有 Service、所有依賴、
    所有潛在問題、並給出完整的重構建議
""")  # 太複雜，結果可能不精確
```

**✅ 逐步探索：**
```python
# 第一步：概覽
await agent.chat("分析專案中所有的 Controller")

# 第二步：聚焦
await agent.chat("UserController 看起來最複雜，深入分析它")

# 第三步：具體問題
await agent.chat("getUserById 方法有什麼潛在問題？")
```

### 4. 儲存對話歷史

```python
class ConversationLogger:
    """對話歷史記錄器"""

    def __init__(self, log_file: str):
        self.log_file = log_file
        self.history = []

    def log_turn(self, user_msg: str, agent_msg: str):
        """記錄一輪對話"""
        turn = {
            "timestamp": datetime.now().isoformat(),
            "user": user_msg,
            "agent": agent_msg
        }
        self.history.append(turn)

        # 即時寫入檔案
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(turn, ensure_ascii=False) + "\n")

    def export_markdown(self, output_file: str):
        """匯出為 Markdown"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 對話歷史\n\n")
            for turn in self.history:
                f.write(f"## {turn['timestamp']}\n\n")
                f.write(f"**使用者:** {turn['user']}\n\n")
                f.write(f"**AI:** {turn['agent']}\n\n")
                f.write("---\n\n")

# 使用範例
logger = ConversationLogger("conversation.jsonl")

async def logged_conversation():
    agent = SpringMVCAnalyzerAgent(mode="agent")

    user_msg = "分析 UserController.java"
    response = await agent.chat(user_msg)

    logger.log_turn(user_msg, response['message'])

    # 對話結束後匯出
    logger.export_markdown("conversation_report.md")
```

### 5. 設定超時和重試

```python
from sdk_agent.config import AgentConfig

# 配置代理模式的超時和重試
config = AgentConfig(
    mode="agent",
    conversation_timeout=300,  # 5 分鐘超時
    max_turns=50,              # 最多 50 輪對話
    retry_on_error=True,       # 錯誤時自動重試
    max_retries=3              # 最多重試 3 次
)

agent = SpringMVCAnalyzerAgent(config=config)
```

### 6. 成本控制

```python
class CostAwareAgent:
    """成本感知的代理包裝器"""

    def __init__(self, budget: float):
        self.agent = SpringMVCAnalyzerAgent(mode="agent")
        self.budget = budget
        self.spent = 0.0

    async def chat(self, message: str) -> dict:
        """發送訊息並追蹤成本"""
        # 預估成本（基於訊息長度）
        estimated_cost = self.estimate_cost(message)

        if self.spent + estimated_cost > self.budget:
            raise Exception(
                f"預算不足！剩餘: ${self.budget - self.spent:.2f}, "
                f"需要: ${estimated_cost:.2f}"
            )

        response = await self.agent.chat(message)

        # 記錄實際成本
        actual_cost = response.get('cost', estimated_cost)
        self.spent += actual_cost

        print(f"[成本] 本次: ${actual_cost:.4f}, 累計: ${self.spent:.4f}, "
              f"剩餘: ${self.budget - self.spent:.2f}")

        return response

    def estimate_cost(self, message: str) -> float:
        """估算成本（簡化版）"""
        # 假設每 1000 字元約 $0.01
        return len(message) / 1000 * 0.01

# 使用範例
cost_agent = CostAwareAgent(budget=5.0)  # $5 預算

try:
    response = await cost_agent.chat("分析所有 Controller")
except Exception as e:
    print(f"錯誤: {e}")
```

---

## 故障排除

### 問題 1: AI 不停地問問題

**症狀：**
```
AI: 你想分析什麼？
使用者: UserController
AI: 你想了解 UserController 的什麼？
使用者: 路由
AI: 你想要詳細的路由資訊還是簡單列表？
...（無限循環）
```

**原因：** AI 需要更明確的指示

**解決方案：**
```python
# ❌ 模糊指令
await agent.chat("分析 UserController")

# ✅ 明確指令
await agent.chat("""
    分析 UserController.java：
    - 列出所有 REST API 端點（方法 + 路徑）
    - 顯示每個端點的參數
    - 不需要詢問，直接給我完整結果
""")
```

### 問題 2: 回應超時

**症狀：**
```
TimeoutError: Conversation exceeded 300 seconds
```

**原因：** 對話時間過長或任務太複雜

**解決方案：**

```python
# 方案 1: 增加超時時間
config = AgentConfig(conversation_timeout=600)  # 10 分鐘
agent = SpringMVCAnalyzerAgent(config=config)

# 方案 2: 分解任務
# ❌ 一次完成所有
await agent.chat("分析整個專案的所有檔案並產生報告")

# ✅ 分步驟
await agent.chat("先列出專案中所有的 Controller")
results = response['result']

# 然後逐個分析
for ctrl in results['controllers']:
    await agent.chat(f"分析 {ctrl}")
```

### 問題 3: 記憶體不足

**症狀：**
```
MemoryError: Conversation history too large
```

**原因：** 對話歷史佔用太多記憶體

**解決方案：**

```python
# 定期清理對話歷史
agent = SpringMVCAnalyzerAgent(mode="agent")

for i, file in enumerate(files):
    await agent.chat(f"分析 {file}")

    # 每 10 個檔案清理一次歷史
    if i % 10 == 0:
        agent.clear_context()
        print("已清理對話歷史")
```

### 問題 4: 回應不一致

**症狀：** 相同問題得到不同答案

**原因：** LLM 的非確定性

**解決方案：**

```python
# 設定溫度參數（較低 = 更一致）
config = AgentConfig(
    mode="agent",
    temperature=0.0  # 完全確定性（0.0-1.0）
)

agent = SpringMVCAnalyzerAgent(config=config)
```

### 問題 5: 無法理解程式碼

**症狀：**
```
AI: 抱歉，我無法理解這段程式碼的結構
```

**原因：** 程式碼格式問題或太複雜

**解決方案：**

```python
# 提供更多上下文
await agent.chat(f"""
    這是一個 SpringMVC Controller：
    {code}

    這是標準的 Spring MVC 語法，請分析：
    - @RequestMapping 註解
    - @Autowired 依賴注入
    - 方法參數和返回值
""")
```

---

## 實戰範例

### 範例 1: 重構規劃助手

```python
async def refactoring_assistant():
    """互動式重構規劃助手"""
    agent = SpringMVCAnalyzerAgent(mode="agent")

    print("=== 重構規劃助手 ===\n")

    # 第一步：了解現況
    response = await agent.chat("""
        我想重構 UserController，請幫我：
        1. 分析目前的程式碼結構
        2. 找出程式碼異味（code smells）
        3. 評估重構風險
    """)

    print(f"AI 分析: {response['message']}\n")

    # 第二步：討論方案
    response = await agent.chat("針對你發現的問題，有哪些重構方案？")
    print(f"AI 建議: {response['message']}\n")

    # 第三步：評估影響
    response = await agent.chat("""
        如果我採用方案 2（拆分成多個小 Controller），
        會影響哪些其他檔案？
    """)

    print(f"影響分析: {response['message']}\n")

    # 第四步：產生行動計畫
    response = await agent.chat("""
        請給我一個詳細的重構步驟清單，
        包括每個步驟的風險評估
    """)

    print(f"行動計畫:\n{response['message']}")

    return response['result']

# 執行
plan = asyncio.run(refactoring_assistant())
```

### 範例 2: Bug 追蹤助手

```python
async def bug_tracker():
    """互動式 Bug 追蹤助手"""
    agent = SpringMVCAnalyzerAgent(mode="agent")

    print("=== Bug 追蹤助手 ===\n")

    # 描述 Bug
    bug_description = """
    使用者回報：
    - 端點: POST /users
    - 錯誤: 500 Internal Server Error
    - 錯誤訊息: NullPointerException
    - 發生時機: 當 email 欄位為空時
    """

    response = await agent.chat(f"""
        幫我追蹤這個 Bug：
        {bug_description}

        請分析：
        1. 可能的根本原因
        2. 相關的程式碼位置
        3. 如何修復
    """)

    print(f"初步分析: {response['message']}\n")

    # 深入調查
    while True:
        question = input("\n您想深入了解什麼？(輸入 'done' 結束): ")

        if question.lower() == 'done':
            break

        response = await agent.chat(question)
        print(f"\nAI: {response['message']}")

    print("\n=== Bug 追蹤完成 ===")

# 執行
asyncio.run(bug_tracker())
```

### 範例 3: 新人 Onboarding 助手

```python
async def onboarding_assistant():
    """新人 onboarding 互動助手"""
    agent = SpringMVCAnalyzerAgent(mode="agent")

    print("=== 歡迎加入團隊！ ===\n")
    print("我是你的 AI 助手，可以幫你了解這個專案。\n")

    # 引導式介紹
    topics = [
        "專案整體架構",
        "主要的 Controller 和路由",
        "核心的 Service 和業務邏輯",
        "資料庫存取層（Repository/Mapper）",
        "常見的開發任務"
    ]

    for i, topic in enumerate(topics, 1):
        print(f"\n--- {i}. {topic} ---")

        response = await agent.chat(f"請介紹：{topic}")
        print(f"\n{response['message']}")

        # 允許提問
        while True:
            question = input("\n你有問題嗎？(直接按 Enter 繼續): ")

            if not question.strip():
                break

            response = await agent.chat(question)
            print(f"\n{response['message']}")

    print("\n=== Onboarding 完成！歡迎開始貢獻！ ===")

# 執行
asyncio.run(onboarding_assistant())
```

---

## 下一步

📚 **相關文檔：**
- [錯誤處理指南](./錯誤處理指南.md) - 處理各種錯誤情況
- [最佳實踐](./最佳實踐.md) - 進階技巧與建議
- [API 參考](./API參考.md) - 完整 API 文檔

🆘 **需要幫助：**
- [常見問題](./常見問題.md)
- [故障排除](./故障排除.md)
- [GitHub Discussions](https://github.com/yourusername/springmvc-agent-analyzer/discussions)

---

**上一篇：** [← 使用手冊](./使用手冊.md)
**下一篇：** [錯誤處理指南 →](./錯誤處理指南.md)
