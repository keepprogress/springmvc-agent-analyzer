# SDK Agent Mode - 使用指南

> **版本**: 1.0.0
> **狀態**: Production Ready
> **最後更新**: 2025-10-06
> **適用於**: SpringMVC Agent Analyzer v1.0.0+

---

## 📋 目錄

1. [快速開始](#快速開始)
2. [安裝指南](#安裝指南)
3. [配置說明](#配置說明)
4. [使用方式](#使用方式)
5. [工具參考](#工具參考)
6. [Hook 系統](#hook-系統)
7. [最佳實踐](#最佳實踐)
8. [故障排除](#故障排除)
9. [進階主題](#進階主題)

---

## 快速開始

### 5 分鐘上手

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 設置 API Key
export ANTHROPIC_API_KEY=your-api-key-here

# 3. 啟動交互模式
python run_sdk_agent.py --interactive

# 4. 開始對話
You: 分析 src/main/java/controllers/UserController.java
Agent: 正在分析 Controller 文件...
```

### 示例對話

```
You: 分析整個項目的 Controller 層

Agent: 我將使用 analyze_directory 工具掃描項目...
[Using tool: analyze_directory]

發現 15 個 Controller 文件：
- UserController.java ✓
- OrderController.java ✓
- ProductController.java ✓
...

You: 構建這些 Controller 的依賴圖譜

Agent: 正在使用 build_graph 構建知識圖譜...
[Using tool: build_graph]

圖譜已構建：
- 節點數：45
- 邊數：78
- Controller→Service 依賴：25 條

You: 導出為 D3.js 格式

Agent: 正在導出圖譜...
[Using tool: export_graph]

已導出到：graphs/project_graph.json
可以在瀏覽器中查看互動圖譜！
```

---

## 安裝指南

### 環境要求

**必需項目**：
- Python 3.10 或更高版本
- pip 包管理器
- Claude API Key（通過環境變量 `ANTHROPIC_API_KEY` 設置）

**可選項目**：
- Git（用於版本控制）
- VS Code 或其他 IDE（推薦）

### 安裝步驟

#### 1. 克隆項目

```bash
git clone https://github.com/your-org/springmvc-agent-analyzer.git
cd springmvc-agent-analyzer
```

#### 2. 創建虛擬環境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

**核心依賴**：
```txt
claude-agent-sdk>=0.1.0     # Claude Agent SDK
aioconsole>=0.7.0           # 非阻塞異步輸入
anthropic>=0.18.0           # Claude API 客戶端
networkx>=3.0               # 圖譜構建
pyyaml>=6.0                 # 配置文件解析
```

#### 4. 設置 API Key

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY="your-api-key-here"

# Windows CMD
set ANTHROPIC_API_KEY=your-api-key-here

# Linux/Mac
export ANTHROPIC_API_KEY=your-api-key-here

# 或創建 .env 文件
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

#### 5. 驗證安裝

```bash
python -c "from sdk_agent import SpringMVCAnalyzerAgent; print('✓ SDK Agent Mode 安裝成功')"
```

---

## 配置說明

### 配置文件位置

- **默認配置**: `config/sdk_agent_config.yaml`
- **自定義配置**: 通過 `--config` 參數指定

### 配置文件結構

```yaml
# config/sdk_agent_config.yaml

server:
  mode: "sdk_agent"  # 操作模式

agent:
  # SDK 啟用狀態
  sdk_enabled: true

  # System Prompt
  system_prompt_type: "default"  # default | custom
  system_prompt_path: null       # 自定義 prompt 路徑

  # Hooks 系統
  hooks_enabled: true

  # 權限模式
  # acceptAll: 自動接受所有工具
  # acceptEdits: 自動接受只讀工具，確認編輯工具
  # rejectAll: 拒絕所有工具（需手動批准）
  # custom: 自定義回調
  permission_mode: "acceptEdits"

  # 對話設置
  max_turns: 20                    # 最大對話輪數
  include_partial_messages: true   # 包含部分消息

  # 允許的工具（支持通配符）
  allowed_tools:
    - "Read"
    - "Glob"
    - "Grep"
    - "mcp__analyzer__*"  # 所有分析工具

# 日誌配置
logging:
  level: "INFO"  # DEBUG | INFO | WARNING | ERROR
  file: "logs/sdk_agent.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 緩存配置
cache:
  cache_dir: ".cache"
  max_size_mb: 1000
  ttl_seconds: 86400  # 24 小時

# 模型配置
models:
  haiku: "claude-3-5-haiku-20241022"
  sonnet: "claude-3-5-sonnet-20241022"
  opus: "claude-opus-4-20250514"
  default: "sonnet"  # 默認使用 Sonnet

# Agent 配置
agents:
  min_confidence: 0.7  # 最小置信度閾值
```

### 關鍵配置項說明

#### permission_mode

- **acceptAll**: 適合批量分析，自動執行所有工具
- **acceptEdits**: 適合交互式分析，只讀工具自動執行，編輯工具需確認
- **rejectAll**: 適合審計模式，所有工具都需手動批准
- **custom**: 使用自定義 `can_use_tool` 回調

#### hooks_enabled

啟用後，將激活以下 Hooks：
- ✅ **ValidationHook** (PreToolUse): 路徑安全驗證
- ✅ **CacheHook** (PostToolUse): 分析結果緩存
- ✅ **CleanupHook** (Stop): 會話清理
- ✅ **ContextManagerHook** (PreCompact): 上下文壓縮
- ✅ **InputEnhancementHook** (UserPromptSubmit): 輸入增強

---

## 使用方式

### 方式 1: 交互式模式

**啟動命令**：
```bash
python run_sdk_agent.py --interactive
```

**功能**：
- 持續對話，支持多輪交互
- 自動工具選擇和執行
- 流式響應輸出
- 上下文保持

**適用場景**：
- 探索式分析
- 逐步構建知識圖譜
- 調試和驗證

**示例對話**：

```
🤖 SpringMVC Agent Analyzer - Interactive Mode
============================================================
SDK Client: Initialized
Tools Available: 11
Max Turns: 20
============================================================

Type your queries. Press Ctrl+C to exit.

You: 列出 src/main/java/controllers 目錄下的所有 Controller

Agent: 正在使用 analyze_directory 工具掃描...
[Using tool: mcp__analyzer__analyze_directory]

找到 8 個 Controller 文件：
1. UserController.java (125 lines)
2. OrderController.java (89 lines)
3. ProductController.java (156 lines)
...

You: 詳細分析第一個 Controller

Agent: 正在分析 UserController.java...
[Using tool: mcp__analyzer__analyze_controller]

Controller Analysis: UserController
============================================================
Package: com.example.controllers
Base URL: /api/users
Methods: 7
Dependencies: 2 (UserService, ValidationService)
Confidence: 95.3%
Model Used: claude-3-5-sonnet-20241022
Cost: $0.0042

Methods:
  - getUsers() → GET /api/users
  - getUserById() → GET /api/users/{id}
  - createUser() → POST /api/users
  - updateUser() → PUT /api/users/{id}
  - deleteUser() → DELETE /api/users/{id}
  - searchUsers() → GET /api/users/search
  - getUserProfile() → GET /api/users/{id}/profile

You: 這個 Controller 依賴的 Service 在哪裡？

Agent: 正在查詢依賴關係...
[Using tool: mcp__analyzer__find_dependencies]

UserController 依賴的 Service：
1. UserService
   - 位置: src/main/java/services/UserService.java
   - 類型: @Service
   - 方法數: 12

2. ValidationService
   - 位置: src/main/java/services/ValidationService.java
   - 類型: @Component
   - 方法數: 5

You: 構建完整的依賴圖譜

Agent: 正在構建知識圖譜...
[Using tool: mcp__analyzer__build_graph]

圖譜構建完成！
節點數: 35
邊數: 58
層級: 4

圖譜包含：
- 8 個 Controller
- 15 個 Service
- 8 個 Mapper
- 4 個 JSP

You: 退出

Agent: 正在清理資源...
[Stop Hook: Cleanup]

👋 再見！
```

### 方式 2: 批量分析模式

**使用 Python API**：

```python
import asyncio
from sdk_agent import SpringMVCAnalyzerAgent

async def analyze_project():
    # 創建 agent
    agent = SpringMVCAnalyzerAgent(
        config_path="config/sdk_agent_config.yaml",
        hooks_enabled=True
    )

    # 批量分析項目
    result = await agent.analyze_project(
        project_path="src/main/java",
        output_format="markdown"
    )

    # 處理結果
    print(result["analysis"])

    # 保存到文件
    with open("analysis_report.md", "w", encoding="utf-8") as f:
        f.write(result["analysis"])

# 運行
asyncio.run(analyze_project())
```

**命令行方式**：
```bash
python run_sdk_agent.py --analyze src/main/java --output report.md
```

### 方式 3: 集成到自定義腳本

```python
from sdk_agent import SpringMVCAnalyzerAgent

async def custom_analysis():
    agent = SpringMVCAnalyzerAgent()

    # 自定義分析流程
    await agent.client.__aenter__()
    try:
        # Step 1: 分析特定文件
        await agent.client.query(
            "分析 src/main/java/controllers/UserController.java"
        )
        async for msg in agent.client.receive_response():
            print(msg, end="")

        # Step 2: 查詢依賴
        await agent.client.query(
            "找出 UserController 的所有依賴"
        )
        async for msg in agent.client.receive_response():
            print(msg, end="")

        # Step 3: 導出圖譜
        await agent.client.query(
            "導出依賴圖譜為 D3.js 格式"
        )
        async for msg in agent.client.receive_response():
            print(msg, end="")
    finally:
        await agent.client.__aexit__(None, None, None)
```

---

## 工具參考

SDK Agent Mode 提供 11 個工具，分為 3 類：

### 分析工具 (6 個)

#### 1. analyze_controller

分析 Spring MVC Controller 文件。

**輸入**：
```json
{
  "file_path": "src/main/java/controllers/UserController.java",
  "include_details": true
}
```

**輸出**：
```
Controller Analysis: UserController
============================================================
Package: com.example.controllers
Base URL: /api/users
Methods: 7
Dependencies: 2
Confidence: 95.3%
...
```

#### 2. analyze_jsp

分析 JSP 視圖文件。

**輸入**：
```json
{
  "file_path": "src/main/webapp/WEB-INF/views/user-list.jsp"
}
```

#### 3. analyze_service

分析 Spring Service 層。

**輸入**：
```json
{
  "file_path": "src/main/java/services/UserService.java"
}
```

#### 4. analyze_mapper

分析 MyBatis Mapper XML。

**輸入**：
```json
{
  "file_path": "src/main/resources/mappers/UserMapper.xml"
}
```

#### 5. analyze_procedure

分析 Oracle 存儲過程。

**輸入**：
```json
{
  "file_path": "src/main/sql/procedures/user_management.prc"
}
```

#### 6. analyze_directory

批量分析目錄。

**輸入**：
```json
{
  "directory_path": "src/main/java/controllers",
  "pattern": "**/*.java",
  "recursive": true
}
```

**輸出**：
```
Directory Analysis Complete
============================================================
Total Files Found: 15
Successfully Analyzed: 14
Failed: 1
Total Cost: $0.0623
```

### 圖譜工具 (2 個)

#### 7. build_graph

從分析結果構建知識圖譜。

**自動觸發**: 分析工具執行後自動累積數據

**手動觸發**：
```json
{
  "force_rebuild": false
}
```

#### 8. export_graph

導出圖譜為各種格式。

**輸入**：
```json
{
  "output_path": "graphs/project_graph.json",
  "format": "d3",  // d3 | cytoscape | dot | graphml
  "include_metadata": true
}
```

**支持格式**：
- **d3**: D3.js 可視化（JSON）
- **cytoscape**: Cytoscape.js（JSON）
- **dot**: Graphviz DOT 格式
- **graphml**: GraphML XML 格式

### 查詢工具 (3 個)

#### 9. query_graph

查詢圖譜統計和信息。

**輸入**：
```json
{
  "query_type": "stats"  // stats | nodes | edges
}
```

**輸出**：
```
Graph Statistics:
- Nodes: 45
- Edges: 78
- Avg Degree: 3.47
- Density: 0.082
```

#### 10. find_dependencies

查找依賴關係。

**輸入**：
```json
{
  "node_id": "UserController",
  "depth": 2,  // 依賴深度
  "direction": "outgoing"  // outgoing | incoming | both
}
```

**輸出**：
```
UserController 的依賴 (深度 2):
1. UserService (直接依賴)
   - UserRepository (間接依賴)
   - CacheService (間接依賴)
2. ValidationService (直接依賴)
   - ValidatorFactory (間接依賴)
```

#### 11. analyze_impact

影響分析（找出誰依賴於目標）。

**輸入**：
```json
{
  "node_id": "UserService",
  "depth": 3
}
```

**輸出**：
```
修改 UserService 將影響:
1. UserController (1 hop)
2. OrderController (2 hops via OrderService)
3. ReportGenerator (3 hops)

總計受影響組件: 12
建議: 需要全面回歸測試
```

---

## Hook 系統

### 可用 Hooks

SDK Agent Mode 提供 5 個 Hook 事件點：

#### 1. ValidationHook (PreToolUse)

**觸發時機**: 工具執行前

**功能**：
- ✅ 路徑遍歷安全檢查
- ✅ 敏感目錄保護
- ✅ 文件存在性驗證

**示例**：

```python
# 嘗試訪問危險路徑
You: 分析 ../../../etc/passwd

Agent: ❌ 安全錯誤
[ValidationHook] 檢測到危險路徑模式: ../
路徑: ../../../etc/passwd
請使用工作區內的安全路徑。
```

#### 2. CacheHook (PostToolUse)

**觸發時機**: 工具執行後

**功能**：
- ✅ 分析結果緩存
- ✅ 語義相似度匹配
- ✅ 自動緩存失效

**緩存命中示例**：

```python
You: 分析 src/main/java/controllers/UserController.java

Agent: ✓ 使用緩存結果 (97% 相似度)
上次分析時間: 2025-10-06 14:32:15
緩存命中，節省成本: $0.0042
```

#### 3. CleanupHook (Stop)

**觸發時機**: 會話停止時

**功能**：
- ✅ 保存會話狀態
- ✅ 清理臨時文件
- ✅ 記錄統計信息

#### 4. ContextManagerHook (PreCompact)

**觸發時機**: 上下文壓縮前

**功能**：
- ✅ 智能保留重要消息
- ✅ 壓縮歷史對話
- ✅ 優化 token 使用

#### 5. InputEnhancementHook (UserPromptSubmit)

**觸發時機**: 用戶提交輸入時

**功能**：
- ✅ 自動添加項目上下文
- ✅ 補充相關信息
- ✅ 優化查詢表達

### 自定義 Hook

創建自定義 Hook：

```python
from typing import Dict, Any, Optional

class CustomHook:
    """自定義 Hook 示例"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)

    async def __call__(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Hook 執行邏輯"""

        if not self.enabled:
            return {"allowed": True}

        # 自定義邏輯
        if tool_name == "analyze_controller":
            # 例如：記錄分析次數
            self._log_usage(tool_name)

        return {"allowed": True}

    def _log_usage(self, tool_name: str):
        """記錄工具使用"""
        # 實現記錄邏輯
        pass

# 註冊 Hook
from sdk_agent import SpringMVCAnalyzerAgent

agent = SpringMVCAnalyzerAgent()
agent.hooks.append(CustomHook({"enabled": True}))
```

---

## 最佳實踐

### 1. 批量分析優化

**使用 analyze_directory 而非多次單文件分析**：

✅ **好**：
```python
You: 分析 src/main/java/controllers 目錄下所有 Controller
```

❌ **不好**：
```python
You: 分析 UserController.java
You: 分析 OrderController.java
You: 分析 ProductController.java
...
```

### 2. 逐步構建圖譜

**先分析，再構建圖譜，最後查詢**：

```python
# Step 1: 分析組件
You: 分析 controllers 目錄

# Step 2: 自動構建圖譜
# (build_graph 在分析後自動觸發)

# Step 3: 查詢和導出
You: 查詢圖譜統計
You: 導出為 D3.js 格式
```

### 3. 利用緩存

**重複查詢相同文件時，自動使用緩存**：

```python
# 第一次分析 - 調用 API
You: 分析 UserController.java
Agent: [調用 Claude API] 分析完成，耗時 2.3s

# 第二次分析 - 使用緩存
You: 分析 UserController.java
Agent: [緩存命中] 分析完成，耗時 0.1s
```

### 4. 權限模式選擇

**根據場景選擇合適的權限模式**：

| 場景 | 推薦模式 | 原因 |
|-----|---------|------|
| 批量分析 | acceptAll | 無需手動確認，提高效率 |
| 交互式探索 | acceptEdits | 只讀自動執行，編輯需確認 |
| 審計模式 | rejectAll | 所有操作需手動批准 |

### 5. 錯誤處理

**優雅處理文件不存在等錯誤**：

```python
You: 分析 nonexistent.java

Agent: ❌ 文件未找到: nonexistent.java
建議: 請檢查文件路徑是否正確

You: 使用 analyze_directory 查找所有 Controller

Agent: ✓ 找到 8 個 Controller 文件
```

### 6. 性能優化

**使用模式匹配過濾文件**：

```python
# 只分析 Controller
You: 分析 src/main/java 目錄，模式 **/*Controller.java

# 只分析 Service
You: 分析 src/main/java 目錄，模式 **/*Service.java
```

---

## 故障排除

### 常見問題

#### Q1: 提示 "SDK not installed"

**原因**: Claude Agent SDK 未安裝

**解決**：
```bash
pip install claude-agent-sdk>=0.1.0
```

#### Q2: 提示 "API Key not found"

**原因**: 環境變量未設置

**解決**：
```bash
# Windows
set ANTHROPIC_API_KEY=your-key-here

# Linux/Mac
export ANTHROPIC_API_KEY=your-key-here
```

#### Q3: 交互模式卡住不響應

**原因**: 異步 I/O 阻塞

**解決**: 確保安裝了 aioconsole
```bash
pip install aioconsole>=0.7.0
```

#### Q4: Hook 不執行

**原因**: hooks_enabled 未啟用

**解決**: 在配置文件中設置
```yaml
agent:
  hooks_enabled: true
```

#### Q5: 工具調用失敗

**原因**: 權限模式設為 rejectAll

**解決**: 修改權限模式
```yaml
agent:
  permission_mode: "acceptEdits"
```

### 調試技巧

#### 啟用 DEBUG 日誌

```yaml
# config/sdk_agent_config.yaml
logging:
  level: "DEBUG"
```

#### 查看詳細錯誤

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from sdk_agent import SpringMVCAnalyzerAgent
# 錯誤將打印到 stderr
```

#### 測試工具連接

```python
from sdk_agent import SpringMVCAnalyzerAgent

agent = SpringMVCAnalyzerAgent()
tools = agent.get_tools()
print(f"已註冊 {len(tools)} 個工具")
```

---

## 進階主題

### 動態切換模型

```python
from sdk_agent import SpringMVCAnalyzerAgent

agent = SpringMVCAnalyzerAgent()

# 運行時切換到 Haiku（更快更便宜）
await agent.set_model("haiku")

# 運行時切換到 Opus（更強大）
await agent.set_model("opus")
```

### 自定義 System Prompt

```yaml
# config/sdk_agent_config.yaml
agent:
  system_prompt_type: "custom"
  system_prompt_path: "prompts/custom_system_prompt.txt"
```

**prompts/custom_system_prompt.txt**:
```
You are a senior Spring MVC architect.

When analyzing code:
1. Focus on architectural patterns
2. Identify anti-patterns
3. Suggest best practices
4. Consider performance implications

Use available tools to analyze:
- Controllers (@Controller, @RestController)
- Services (@Service)
- Repositories (@Repository)
- Mappers (MyBatis XML)
```

### 集成 CI/CD

```yaml
# .github/workflows/analyze.yml
name: Spring MVC Analysis

on:
  push:
    branches: [main]
  pull_request:

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
        run: pip install -r requirements.txt

      - name: Run Analysis
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python run_sdk_agent.py --analyze src/main/java \
            --output analysis_report.md

      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: analysis-report
          path: analysis_report.md
```

---

## 相關資源

- 📘 [SDK Agent 技術規格](./SDK_AGENT_SPECIFICATION.md)
- 📋 [實施計劃](./SDK_AGENT_IMPLEMENTATION_PLAN.md)
- 🔄 [遷移指南](./MIGRATION_TO_SDK.md)
- 🏗️ [架構文檔](./ARCHITECTURE.md)
- 🚀 [快速開始](../QUICKSTART.md)

---

## 支持

如有問題或建議，請：

- 提交 Issue: https://github.com/your-org/springmvc-agent-analyzer/issues
- 查看文檔: https://docs.springmvc-analyzer.com
- 聯繫維護者: support@springmvc-analyzer.com

---

**祝您使用愉快！** 🎉
