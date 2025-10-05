# SDK Agent 使用指南

**SpringMVC Agent Analyzer - SDK Agent Mode User Guide**

本指南介紹如何使用 SDK Agent 模式進行 Spring MVC 專案分析。

---

## 📋 目錄

- [快速開始](#快速開始)
- [三種模式比較](#三種模式比較)
- [安裝配置](#安裝配置)
- [使用方式](#使用方式)
  - [交互式模式](#交互式模式)
  - [批量分析模式](#批量分析模式)
  - [編程 API](#編程-api)
- [常見使用場景](#常見使用場景)
- [進階功能](#進階功能)
- [故障排除](#故障排除)
- [FAQ](#faq)

---

## 快速開始

### 前提條件

- Python 3.10+
- Claude Code CLI 已安裝
- **不需要** Anthropic API Key（使用 Claude Code 訂閱）

### 5 分鐘快速體驗

```bash
# 1. 安裝依賴
pip install -e ".[dev]"
pip install claude-agent-sdk>=0.1.0

# 2. 配置 SDK Agent 模式
echo "server:
  mode: sdk_agent

models:
  # 使用 Claude Code 模型
  default: claude-sonnet-4-5

sdk_agent:
  max_turns: 20
  permission_mode: acceptEdits
  hooks_enabled: true" > config/sdk_agent_config.yaml

# 3. 啟動交互式分析
python run_sdk_agent.py --interactive

# 4. 開始對話
# > 請分析 src/main/java/com/example/controller/UserController.java
# > 這個 controller 有哪些依賴？
# > 生成依賴關係圖
```

**恭喜！** 您已經成功使用 SDK Agent 模式 🎉

---

## 三種模式比較

SpringMVC Agent Analyzer 提供三種操作模式，根據您的訂閱選擇：

| 特性 | API 模式 | Passive 模式 | **SDK Agent 模式** ⭐ |
|------|---------|--------------|---------------------|
| **需要 API Key** | ✅ 是 | ❌ 否 | ❌ 否 |
| **需要訂閱** | Anthropic API | Claude Code | Claude Code |
| **交互方式** | MCP 工具調用 | Claude Code + MCP 工具 | **雙向對話** |
| **自主性** | 批量自動分析 | 用戶驅動分析 | **Agent 自主對話** |
| **成本** | ~$4.23/專案 | $0（使用訂閱） | **$0（使用訂閱）** |
| **Hooks 支持** | ❌ | ❌ | **✅ 完整支持** |
| **動態控制** | ❌ | 有限 | **✅ 運行時調整** |
| **許可權管理** | ❌ | ❌ | **✅ 細粒度控制** |
| **上下文管理** | ❌ | ❌ | **✅ 自動壓縮** |
| **最佳用途** | 批量處理 | 探索性分析 | **交互式深度分析** |

### 何時選擇 SDK Agent 模式？

✅ **選擇 SDK Agent 模式，如果您：**
- 只有 Claude Code 訂閱（沒有 API Key）
- 需要交互式對話分析代碼
- 想要 Agent 自主決策分析策略
- 需要驗證、上下文管理等 Hooks 功能
- 希望運行時動態調整模型和權限

❌ **不選擇 SDK Agent 模式，如果您：**
- 需要批量自動處理大量文件（用 API 模式）
- 只是偶爾查詢圖數據（用 Passive 模式）
- 不需要交互式對話

---

## 安裝配置

### 1. 安裝 SDK

```bash
# 安裝 Claude Agent SDK
pip install claude-agent-sdk>=0.1.0

# 或者在 requirements.txt 中添加
echo "claude-agent-sdk>=0.1.0" >> requirements.txt
pip install -r requirements.txt
```

### 2. 創建配置文件

創建 `config/sdk_agent_config.yaml`：

```yaml
# SDK Agent 模式配置
server:
  mode: "sdk_agent"

models:
  # 使用 Claude Code 的模型
  default: "claude-sonnet-4-5"
  haiku: "claude-3-5-haiku-20241022"
  sonnet: "claude-3-5-sonnet-20241022"

agents:
  # Agent 配置
  min_confidence: 0.7
  structure_validation_penalty: 0.6

sdk_agent:
  # SDK Agent 特定配置
  max_turns: 20                    # 最大對話輪數
  permission_mode: "acceptEdits"   # 權限模式：acceptAll, acceptEdits, rejectAll
  hooks_enabled: true              # 啟用 Hooks 系統

  hooks:
    # Hook 配置
    validation:
      enabled: true
      min_confidence: 0.7

    context_manager:
      enabled: true
      compact_threshold: 50        # 超過 50 輪壓縮上下文

    cache:
      enabled: true
      similarity_threshold: 0.85

  prompts:
    # 系統提示詞配置
    system_prompt_path: "prompts/sdk_agent/system_prompt.md"
    include_examples: true

graph:
  # 知識圖配置
  auto_build: true                 # 分析後自動構建圖
  export_format: "d3"              # 默認導出格式

cache:
  # 緩存配置
  cache_dir: ".cache"
  max_size_mb: 1000
  ttl_seconds: 86400
```

### 3. 驗證安裝

```bash
# 驗證 SDK 安裝
python -c "import claude_agent_sdk; print('SDK installed:', claude_agent_sdk.__version__)"

# 驗證配置
python run_sdk_agent.py --validate-config
```

---

## 使用方式

### 交互式模式

**最常用的方式**，啟動與 Agent 的雙向對話：

```bash
# 啟動交互式模式
python run_sdk_agent.py --interactive

# 或指定配置文件
python run_sdk_agent.py --interactive --config config/sdk_agent_config.yaml
```

#### 示例對話 1：分析 Controller

```
You: 請分析 src/main/java/com/example/controller/UserController.java

Agent: 我來分析這個 Controller 文件。
[調用工具: analyze_controller]

分析結果：
📄 UserController.java
- 類名：UserController
- 基礎路徑：/user
- 端點：
  • GET /user/list → listUsers()
  • POST /user/create → createUser()
  • GET /user/edit/{id} → editUser(Long id)
- 依賴服務：
  • UserService (注入)
  • RoleService (注入)
- 返回視圖：
  • user/list.jsp
  • user/form.jsp
  • user/edit.jsp

You: 這個 Controller 依賴的 UserService 有什麼方法？

Agent: 讓我分析 UserService。
[調用工具: analyze_service]

UserService 提供以下方法：
1. findAll() → List<User>
2. findById(Long id) → User
3. save(User user) → void
4. delete(Long id) → void
5. 事務管理：@Transactional 在 save/delete 方法

You: 如果我修改 UserService.save() 方法，會影響哪些組件？

Agent: 讓我進行影響分析。
[調用工具: analyze_impact]

影響分析結果：
🔍 修改 UserService.save() 會影響：

直接影響：
- UserController.createUser() - 調用 save()
- UserController.editUser() - 調用 save()

間接影響：
- user/form.jsp - 由 createUser() 渲染
- user/edit.jsp - 由 editUser() 渲染

建議：
- 更新相關單元測試
- 檢查事務邊界是否需要調整
- 驗證表單驗證邏輯
```

#### 示例對話 2：探索性分析

```
You: 這個專案有多少個 Controller？

Agent: [調用工具: list_files]
[調用工具: analyze_directory]

專案共有 8 個 Controller：
1. UserController - 用戶管理
2. RoleController - 角色管理
3. AuthController - 認證
4. ProductController - 產品管理
5. OrderController - 訂單管理
6. ReportController - 報表
7. ApiController - API 接口
8. AdminController - 後台管理

You: 哪個 Controller 最複雜？

Agent: 根據複雜度分析（端點數量、依賴數量、邏輯複雜度）：

最複雜的是 OrderController：
- 12 個端點
- 5 個服務依賴
- 3 個外部 API 調用
- 事務管理邏輯複雜

建議優先重構此 Controller。

You: 生成 OrderController 的依賴關係圖

Agent: [調用工具: build_graph]
[調用工具: export_graph]

依賴關係圖已生成：output/order_controller_dependencies.html

主要依賴鏈：
OrderController → OrderService → OrderRepository
              → PaymentService → PaymentGatewayAPI
              → ProductService → ProductRepository
              → UserService → UserRepository
```

### 批量分析模式

**適合一次性分析整個專案**：

```bash
# 分析專案並生成報告
python run_sdk_agent.py \
  --analyze-project src/main/java \
  --output-format markdown \
  --export-graph output/graph.html
```

#### 輸出示例

```markdown
# SpringMVC 專案分析報告

## 概覽
- 總文件數：156
- Controllers：8
- Services：15
- Repositories：12
- JSP 視圖：43
- MyBatis Mappers：12

## 架構分析
- 三層架構：Controller → Service → Repository
- 依賴注入：Spring @Autowired
- 事務管理：聲明式事務
- 視圖技術：JSP + JSTL

## 關鍵發現
1. OrderController 複雜度過高（建議重構）
2. 3 個 Service 缺少事務管理
3. 5 個 JSP 頁面包含業務邏輯（建議提取）
4. 2 個 SQL 查詢存在 N+1 問題

## 依賴關係圖
[圖形已導出到 output/graph.html]
```

### 編程 API

**在 Python 代碼中使用 SDK Agent**：

```python
import asyncio
from sdk_agent.client import SpringMVCAnalyzerAgent

async def analyze_project():
    # 初始化 Agent
    agent = SpringMVCAnalyzerAgent(
        config_path="config/sdk_agent_config.yaml",
        hooks_enabled=True,
        permission_mode="acceptEdits",
        max_turns=20
    )

    # 方式 1: 批量分析
    result = await agent.analyze_project(
        project_path="src/main/java",
        output_format="json"
    )

    print(f"分析了 {result['total_files']} 個文件")
    print(f"發現 {result['total_endpoints']} 個端點")

    # 方式 2: 單個文件分析
    from sdk_agent.tools.controller_tools import analyze_controller

    controller_result = await analyze_controller({
        "file_path": "src/main/java/com/example/UserController.java"
    })

    print(f"Controller: {controller_result['class_name']}")
    print(f"端點數量: {len(controller_result['endpoints'])}")

    # 方式 3: 圖查詢
    from sdk_agent.tools.graph_tools import query_graph

    stats = await query_graph({"query_type": "stats"})
    print(f"圖節點數: {stats['num_nodes']}")
    print(f"圖邊數: {stats['num_edges']}")

# 運行
asyncio.run(analyze_project())
```

---

## 常見使用場景

### 場景 1：代碼理解與文檔生成

**目標**：理解遺留代碼並生成文檔

```bash
python run_sdk_agent.py --interactive
```

```
You: 分析 src/main/java/com/legacy/order/ 目錄下的所有代碼，
     生成詳細的技術文檔，包括：
     1. 架構設計
     2. 數據流
     3. API 端點
     4. 依賴關係

Agent: [執行分析...]

已生成文檔：docs/legacy_order_module.md

主要發現：
- 訂單模塊使用經典三層架構
- 包含 5 個主要業務流程
- 依賴 PaymentService 和 InventoryService
- 數據流：Controller → OrderService → OrderRepository → Oracle DB

詳見文檔獲取完整架構圖和 API 說明。
```

### 場景 2：重構影響分析

**目標**：評估重構的影響範圍

```
You: 我計劃將 UserService 拆分為 UserQueryService 和 UserCommandService，
     請分析這個改動會影響哪些地方？

Agent: [調用 find_dependencies 和 analyze_impact]

影響分析：

直接影響（需要修改）：
1. UserController - 7 處注入點
2. AdminController - 3 處注入點
3. AuthService - 1 處依賴
4. AuditService - 2 處依賴

間接影響（可能需要調整）：
1. 單元測試：UserServiceTest
2. 配置：applicationContext.xml
3. 文檔：API_DESIGN.md

風險評估：
- 中等風險：需要大量代碼修改
- 建議：先創建適配器層，逐步遷移

遷移步驟建議：
1. 創建新的 Service 接口
2. 實現適配器層
3. 逐個 Controller 遷移
4. 更新測試
5. 刪除舊代碼
```

### 場景 3：性能瓶頸識別

**目標**：找出潛在的性能問題

```
You: 分析專案中的 MyBatis Mapper，找出可能的性能瓶頸

Agent: [調用 analyze_mapper 工具]

發現 5 個性能問題：

🔴 嚴重問題：
1. UserMapper.findAll() - N+1 查詢問題
   - 位置：UserMapper.xml:45
   - 問題：在循環中查詢角色信息
   - 建議：使用 JOIN 或批量查詢

2. OrderMapper.getOrderDetails() - 缺少索引
   - 位置：OrderMapper.xml:78
   - 問題：WHERE 條件字段無索引
   - 建議：在 order_date 字段添加索引

🟡 中等問題：
3. ProductMapper.search() - 全表掃描
   - 使用 LIKE '%keyword%' 導致索引失效
   - 建議：使用全文搜索或優化查詢

⚡ 優化建議：
- 啟用 MyBatis 二級緩存
- 使用批量操作代替循環
- 添加數據庫索引
```

### 場景 4：新功能開發指導

**目標**：了解如何添加新功能

```
You: 我要添加一個新的 "訂單導出" 功能，請告訴我需要：
     1. 創建哪些文件
     2. 修改哪些現有代碼
     3. 需要注意什麼

Agent: [分析現有架構]

新功能實現指南：

📁 需要創建的文件：
1. OrderExportController.java
   - 位置：src/main/java/com/example/controller/
   - 端點：GET /order/export

2. OrderExportService.java
   - 位置：src/main/java/com/example/service/
   - 方法：exportToExcel(), exportToPDF()

3. OrderExportMapper.xml
   - 位置：src/main/resources/mapper/
   - SQL：查詢導出數據

4. order_export.jsp
   - 位置：src/main/webapp/WEB-INF/views/order/
   - UI：導出選項界面

🔧 需要修改的文件：
1. OrderController.java
   - 添加導出按鈕鏈接

2. spring-mvc.xml
   - 註冊新的 Controller 和 Service

3. order/list.jsp
   - 添加 "導出" 按鈕

⚠️ 注意事項：
1. 大量數據導出建議使用異步處理
2. 添加分頁或限制導出數量
3. 考慮權限控制（參考現有 AuthController）
4. 導出格式：參考 ReportController 的實現
5. 錯誤處理：統一使用 GlobalExceptionHandler

📝 實現步驟：
1. 創建基本 Controller 和端點
2. 實現 Service 層業務邏輯
3. 編寫 Mapper SQL 查詢
4. 創建 JSP 視圖
5. 添加單元測試
6. 集成測試

是否需要我生成代碼模板？
```

### 場景 5：技術債務評估

**目標**：識別和量化技術債務

```
You: 評估整個專案的技術債務，按優先級排序

Agent: [全面分析代碼庫]

技術債務報告：

📊 總體評分：6.5/10（中等債務）

🔴 高優先級（建議立即處理）：
1. OrderController 複雜度過高
   - 圈複雜度：45（建議 <15）
   - 影響範圍：核心業務流程
   - 重構工作量：5 天

2. 缺少事務管理
   - 影響：3 個 Service 類
   - 風險：數據一致性問題
   - 修復工作量：2 天

🟡 中優先級（近期處理）：
3. JSP 中混雜業務邏輯
   - 影響：8 個 JSP 文件
   - 建議：提取到 Service 層
   - 重構工作量：3 天

4. SQL 注入風險
   - 影響：2 個動態 SQL
   - 風險：安全漏洞
   - 修復工作量：1 天

🟢 低優先級（有空時處理）：
5. 過時的依賴版本
6. 缺少 JavaDoc 註釋
7. 測試覆蓋率不足（45%）

💰 總估算工作量：15 人天

📈 建議處理順序：
Week 1: 修復事務管理和 SQL 注入（高風險）
Week 2: 重構 OrderController（高影響）
Week 3: 提取 JSP 業務邏輯（中等影響）
```

---

## 進階功能

### 1. Hooks 系統

SDK Agent 支持 5 種 Hooks，用於驗證、優化、監控：

#### PreToolUse Hook - 工具調用前驗證

```python
from sdk_agent.hooks.validation import ValidationHook

# 自動啟用（配置文件中設置）
# hooks:
#   validation:
#     enabled: true
#     min_confidence: 0.7

# 效果：分析結果信心度 < 0.7 時自動升級模型
```

```
Agent: [嘗試使用 analyze_controller]
Hook: 檢測到複雜代碼，信心度 0.65 < 0.7
Hook: 自動升級模型：Haiku → Sonnet
Agent: [使用 Sonnet 重新分析]
Result: 分析完成，信心度 0.92 ✓
```

#### PostToolUse Hook - 工具調用後處理

```python
# 自動清理臨時結果
# hooks:
#   cleanup:
#     enabled: true
#     keep_recent: 10

# 效果：自動刪除舊的分析結果，保持存儲清潔
```

#### UserPromptSubmit Hook - 用戶輸入預處理

```python
# 自動展開路徑和添加上下文
# hooks:
#   context_expansion:
#     enabled: true

# 效果：
# 用戶輸入："分析 UserController"
# 展開後："分析 src/main/java/com/example/controller/UserController.java，
#         請考慮其依賴的 UserService 和相關 JSP 視圖"
```

#### Stop Hook - 對話結束處理

```python
# 自動生成摘要和保存會話
# hooks:
#   session_save:
#     enabled: true
#     save_path: "sessions/"

# 效果：對話結束時自動保存完整會話記錄
```

#### PreCompact Hook - 上下文壓縮前處理

```python
# 智能選擇保留的消息
# hooks:
#   context_manager:
#     enabled: true
#     compact_threshold: 50

# 效果：超過 50 輪對話時，自動壓縮歷史消息，保留關鍵信息
```

### 2. 動態控制

運行時調整 Agent 行為：

```python
from sdk_agent.client import SpringMVCAnalyzerAgent

agent = SpringMVCAnalyzerAgent()

# 動態切換模型
await agent.set_model("claude-opus-4")  # 處理複雜任務時升級

# 動態調整權限
await agent.set_permission_mode("acceptAll")  # 批量處理時全部接受

# 中斷當前操作
await agent.interrupt()  # 停止長時間運行的分析
```

### 3. 權限管理

細粒度控制工具使用權限：

```python
# config/sdk_agent_config.yaml
sdk_agent:
  permission_mode: "custom"

  permissions:
    # 讀取工具：總是允許
    analyze_controller: "allow"
    analyze_service: "allow"
    query_graph: "allow"

    # 修改工具：需要確認
    build_graph: "confirm"
    export_graph: "confirm"

    # 危險操作：禁止
    delete_cache: "deny"
```

效果：

```
Agent: 我需要調用 export_graph 導出圖數據
System: [權限檢查：confirm]
System: 確認導出圖到 output/graph.html？(y/n)
You: y
Agent: [執行導出]
```

### 4. 緩存策略

語義緩存避免重複分析：

```python
# 配置語義緩存
# cache:
#   enabled: true
#   similarity_threshold: 0.85
#   vector_store: "faiss"

# 效果：
# 第一次分析 UserController.java → 調用 LLM，耗時 2s
# 修改註釋後再次分析 → 命中緩存（相似度 0.92），耗時 0.1s
```

---

## 故障排除

### 問題 1：SDK Agent 啟動失敗

**症狀**：
```
Error: Failed to initialize SpringMVCAnalyzerAgent
```

**解決方案**：

1. 檢查 Claude Code CLI 安裝：
```bash
claude --version
```

2. 檢查 SDK 安裝：
```bash
pip show claude-agent-sdk
```

3. 驗證配置文件：
```bash
python run_sdk_agent.py --validate-config
```

4. 查看詳細錯誤：
```bash
python run_sdk_agent.py --interactive --verbose
```

### 問題 2：工具調用失敗

**症狀**：
```
Error: Tool 'analyze_controller' execution failed
```

**解決方案**：

1. 檢查文件路徑是否正確：
```python
# 使用絕對路徑
file_path = "/absolute/path/to/UserController.java"

# 或者當前目錄相對路徑
file_path = "src/main/java/com/example/UserController.java"
```

2. 檢查文件是否可讀：
```bash
ls -la src/main/java/com/example/UserController.java
```

3. 查看工具日誌：
```bash
tail -f logs/sdk_agent.log
```

### 問題 3：分析結果不準確

**症狀**：分析結果缺少信息或包含錯誤

**解決方案**：

1. 檢查信心度：
```python
result = await analyze_controller({"file_path": "..."})
if result["confidence"] < 0.7:
    print("信心度過低，建議使用更強大的模型")
```

2. 啟用 Validation Hook：
```yaml
# config/sdk_agent_config.yaml
hooks:
  validation:
    enabled: true
    min_confidence: 0.8  # 提高閾值
```

3. 手動升級模型：
```python
await agent.set_model("claude-opus-4")  # 使用最強模型
```

### 問題 4：上下文過長導致錯誤

**症狀**：
```
Error: Context length exceeded
```

**解決方案**：

1. 啟用自動壓縮：
```yaml
hooks:
  context_manager:
    enabled: true
    compact_threshold: 30  # 降低閾值
```

2. 手動清理上下文：
```python
await agent.compact_context()
```

3. 拆分大型文件分析：
```python
# 不要一次分析整個目錄
# 分批處理
for subdir in ["controller", "service", "repository"]:
    await agent.analyze_project(f"src/main/java/com/example/{subdir}")
```

### 問題 5：Hooks 不生效

**症狀**：配置的 Hooks 沒有執行

**解決方案**：

1. 確認 Hooks 已啟用：
```yaml
sdk_agent:
  hooks_enabled: true  # 全局開關

  hooks:
    validation:
      enabled: true    # 具體 Hook 開關
```

2. 檢查 Hook 日誌：
```bash
grep "Hook" logs/sdk_agent.log
```

3. 驗證 Hook 註冊：
```python
# 在代碼中檢查
agent = SpringMVCAnalyzerAgent()
print(agent.hooks)  # 應該顯示已註冊的 Hooks
```

---

## FAQ

### Q1: SDK Agent 模式和 API 模式有什麼區別？

**A**: 主要區別：

| 方面 | SDK Agent 模式 | API 模式 |
|------|---------------|---------|
| 交互方式 | 雙向對話 | 單向工具調用 |
| 自主性 | Agent 自主決策 | 用戶驅動 |
| API Key | 不需要 | 需要 |
| 成本 | $0（使用訂閱） | ~$4.23/專案 |
| Hooks | 支持 | 不支持 |

**建議**：
- 探索性分析、交互式使用 → SDK Agent
- 批量自動處理 → API 模式

### Q2: 可以同時使用多種模式嗎？

**A**: 可以！三種模式共享底層組件：

```bash
# 使用 SDK Agent 進行探索性分析
python run_sdk_agent.py --interactive

# 使用 API 模式批量處理
python run_mcp_server.py --mode api --analyze-all

# 使用 Passive 模式在 Claude Code 中查詢
# (通過 MCP 工具)
```

### Q3: 如何自定義 System Prompt？

**A**: 兩種方式：

方式 1：修改配置文件
```yaml
# config/sdk_agent_config.yaml
sdk_agent:
  prompts:
    system_prompt_path: "prompts/custom_system_prompt.md"
```

方式 2：編程方式
```python
custom_prompt = """
你是 Spring MVC 專家，專注於：
1. 代碼質量分析
2. 性能優化建議
3. 安全漏洞檢測
"""

agent = SpringMVCAnalyzerAgent(system_prompt=custom_prompt)
```

### Q4: 如何添加自定義工具？

**A**: 使用 `@tool` 裝飾器：

```python
# sdk_agent/tools/custom_tools.py
from claude_agent_sdk import tool
from typing import Dict, Any

@tool(
    name="analyze_security",
    description="分析代碼安全漏洞",
    input_schema={
        "file_path": {
            "type": "string",
            "description": "要分析的文件路徑"
        }
    }
)
async def analyze_security(args: Dict[str, Any]) -> Dict[str, Any]:
    file_path = args["file_path"]

    # 自定義分析邏輯
    vulnerabilities = []

    with open(file_path) as f:
        content = f.read()

        # 檢查 SQL 注入
        if "Statement" in content and "+" in content:
            vulnerabilities.append({
                "type": "SQL Injection",
                "severity": "high",
                "description": "可能的 SQL 注入風險"
            })

    return {
        "file_path": file_path,
        "vulnerabilities": vulnerabilities,
        "total_issues": len(vulnerabilities)
    }

# 註冊到 Agent
from sdk_agent.client import SpringMVCAnalyzerAgent
agent = SpringMVCAnalyzerAgent()
# 工具會自動註冊
```

### Q5: 分析大型專案時如何優化性能？

**A**: 多種優化策略：

1. **啟用緩存**：
```yaml
cache:
  enabled: true
  similarity_threshold: 0.85
```

2. **並行處理**：
```python
import asyncio

files = ["Controller1.java", "Controller2.java", ...]

# 並行分析
results = await asyncio.gather(
    *[analyze_controller({"file_path": f}) for f in files]
)
```

3. **增量分析**：
```python
# 只分析修改的文件
changed_files = get_git_changed_files()
for file in changed_files:
    await analyze_file(file)
```

4. **分批處理**：
```python
# 每次處理 10 個文件
batch_size = 10
for i in range(0, len(files), batch_size):
    batch = files[i:i+batch_size]
    await process_batch(batch)
```

### Q6: 如何導出分析結果？

**A**: 多種導出格式：

```python
# 1. Markdown 報告
result = await agent.analyze_project(
    project_path="src/main/java",
    output_format="markdown"
)
# 保存到 output/report.md

# 2. JSON 數據
result = await agent.analyze_project(
    project_path="src/main/java",
    output_format="json"
)
# 保存到 output/analysis.json

# 3. 知識圖可視化
from sdk_agent.tools.graph_tools import export_graph

await export_graph({
    "output_path": "output/graph.html",
    "format": "d3"
})
# 在瀏覽器打開 output/graph.html

# 4. GraphML（用於 Neo4j、Gephi 等）
await export_graph({
    "output_path": "output/graph.graphml",
    "format": "graphml"
})
```

### Q7: 出現 "信心度過低" 警告怎麼辦？

**A**: 三種處理方式：

1. **自動升級模型**（推薦）：
```yaml
hooks:
  validation:
    enabled: true
    min_confidence: 0.7
# Hook 會自動升級模型
```

2. **手動切換模型**：
```python
# 使用更強大的模型
await agent.set_model("claude-opus-4")
result = await analyze_controller({"file_path": "..."})
```

3. **提供更多上下文**：
```python
# 分析時包含相關文件
result = await analyze_controller({
    "file_path": "UserController.java",
    "include_dependencies": True,  # 包含依賴的 Service
    "include_views": True          # 包含相關 JSP
})
```

### Q8: 如何集成到 CI/CD 流程？

**A**: 示例集成：

```yaml
# .github/workflows/code-analysis.yml
name: SpringMVC Analysis

on: [pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install claude-agent-sdk

      - name: Run analysis
        run: |
          python run_sdk_agent.py \
            --analyze-project src/main/java \
            --output-format markdown \
            --output-path report.md

      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

### Q9: 支持哪些 Spring 版本？

**A**:
- ✅ Spring MVC 3.x, 4.x, 5.x
- ✅ Spring Boot 1.x, 2.x, 3.x
- ✅ Spring Framework 6.x
- ✅ 傳統 XML 配置和註解配置都支持

LLM-First 方法的優勢：即使 Spring 版本更新，也無需修改代碼！

### Q10: 如何貢獻或報告問題？

**A**:
- 🐛 報告 Bug：[GitHub Issues](https://github.com/yourusername/springmvc-agent-analyzer/issues)
- 💡 功能建議：[GitHub Discussions](https://github.com/yourusername/springmvc-agent-analyzer/discussions)
- 🔧 貢獻代碼：Fork → 修改 → Pull Request
- 📧 聯繫：查看 README.md

---

## 下一步

- 📖 閱讀 [SDK Agent 技術規格](./SDK_AGENT_SPECIFICATION.md)
- 🛠️ 查看 [實現計劃](./SDK_AGENT_IMPLEMENTATION_PLAN.md)
- 🔄 了解 [從 MCP 遷移到 SDK](./MIGRATION_TO_SDK.md)
- 🏗️ 探索 [架構設計](./ARCHITECTURE.md)

---

**享受 SDK Agent 帶來的交互式代碼分析體驗！** 🚀
