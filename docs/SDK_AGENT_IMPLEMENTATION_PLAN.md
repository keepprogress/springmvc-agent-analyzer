# SDK Agent Mode - 實施計劃

> **版本**: 1.0.0
> **狀態**: In Progress
> **開始日期**: 2025-10-05
> **預計完成**: 2025-10-11 (6 週)

---

## 📋 目錄

1. [概述](#概述)
2. [Phase 1: 基礎設施](#phase-1-基礎設施)
3. [Phase 2: 工具適配](#phase-2-工具適配)
4. [Phase 3: Hooks 系統](#phase-3-hooks-系統)
5. [Phase 4: SDK Client](#phase-4-sdk-client)
6. [Phase 5: 測試](#phase-5-測試)
7. [Phase 6: 文檔和發布](#phase-6-文檔和發布)
8. [驗收標準](#驗收標準)
9. [風險和緩解](#風險和緩解)

---

## 概述

### 目標

在 SpringMVC Agent Analyzer 中添加 **SDK Agent Mode**，作為第三種操作模式，利用 Claude Agent SDK 的高級功能。

### 實施原則

- ✅ **保持向後兼容** - 不破壞現有 API/Passive 模式
- ✅ **代碼復用優先** - 最大化利用現有組件
- ✅ **增量開發** - 每個 Phase 都可獨立測試
- ✅ **詳細文檔** - 每步都記錄，避免遺忘

### 時間表

| Phase | 任務 | 時間 | 狀態 |
|-------|------|------|------|
| Phase 1 | 基礎設施 | Week 1 | 🔄 In Progress |
| Phase 2 | 工具適配 | Week 2-3 | ⏳ Pending |
| Phase 3 | Hooks 系統 | Week 4 | ⏳ Pending |
| Phase 4 | SDK Client | Week 5 | ⏳ Pending |
| Phase 5 | 測試 | Week 5-6 | ⏳ Pending |
| Phase 6 | 文檔和發布 | Week 6 | ⏳ Pending |

---

## Phase 1: 基礎設施

**目標**: 搭建 SDK Agent Mode 的基礎架構，包含配置、目錄結構、依賴安裝。

**預計時間**: 1 週
**狀態**: 🔄 In Progress

### Checklist

#### 1.1 依賴安裝

- [ ] **安裝 Claude Agent SDK**
  ```bash
  pip install claude-agent-sdk>=0.1.0
  ```

- [ ] **更新 requirements.txt**
  ```txt
  # 添加到 requirements.txt
  claude-agent-sdk>=0.1.0
  ```

- [ ] **驗證 Claude Code CLI 安裝**
  ```bash
  claude --version
  # 或
  npx @anthropic-ai/claude-code --version
  ```

#### 1.2 目錄結構創建

- [ ] **創建 sdk_agent 目錄**
  ```bash
  mkdir -p sdk_agent/{tools,hooks}
  touch sdk_agent/__init__.py
  touch sdk_agent/client.py
  touch sdk_agent/config.py
  touch sdk_agent/permissions.py
  touch sdk_agent/tools/__init__.py
  touch sdk_agent/tools/analysis_tools.py
  touch sdk_agent/tools/graph_tools.py
  touch sdk_agent/tools/query_tools.py
  touch sdk_agent/hooks/__init__.py
  touch sdk_agent/hooks/validation_hooks.py
  touch sdk_agent/hooks/context_hooks.py
  touch sdk_agent/hooks/cache_hooks.py
  ```

**預期結構**:
```
sdk_agent/
├── __init__.py              # 導出主類
├── client.py                # SpringMVCAnalyzerAgent 主類
├── config.py                # 配置管理
├── permissions.py           # 權限控制
├── tools/                   # SDK 工具
│   ├── __init__.py         # 導出所有工具
│   ├── analysis_tools.py   # 分析工具
│   ├── graph_tools.py      # 圖譜工具
│   └── query_tools.py      # 查詢工具
└── hooks/                   # Hook 實現
    ├── __init__.py         # 導出所有 hooks
    ├── validation_hooks.py # 驗證 hooks
    ├── context_hooks.py    # 上下文 hooks
    └── cache_hooks.py      # 緩存 hooks
```

#### 1.3 配置文件

- [ ] **創建 config/sdk_agent_config.yaml**
  ```yaml
  # SDK Agent 配置文件
  server:
    mode: "agent"

  agent:
    sdk_enabled: true
    system_prompt_type: "default"
    hooks_enabled: true
    enabled_hooks:
      - "PreToolUse"
      - "PostToolUse"
      - "UserPromptSubmit"
      - "Stop"
    permission_mode: "acceptEdits"
    permission_callback_enabled: true
    max_turns: 20
    include_partial_messages: true
    allowed_tools:
      - "Read"
      - "Glob"
      - "Grep"
      - "mcp__analyzer__*"
  ```

- [ ] **更新主配置 config/config.yaml**
  ```yaml
  server:
    mode: "api"  # api | passive | agent
  ```

#### 1.4 入口點

- [ ] **創建 run_sdk_agent.py**
  ```python
  #!/usr/bin/env python3
  """
  SDK Agent Mode 入口點。

  Usage:
      python run_sdk_agent.py --interactive
      python run_sdk_agent.py --analyze /path/to/project
  """
  import asyncio
  import argparse
  from pathlib import Path
  from sdk_agent.client import SpringMVCAnalyzerAgent

  def main():
      parser = argparse.ArgumentParser(description="SpringMVC Analyzer - SDK Agent Mode")
      parser.add_argument(
          "--config",
          default="config/sdk_agent_config.yaml",
          help="Configuration file path"
      )
      parser.add_argument(
          "--interactive",
          action="store_true",
          help="Start interactive mode"
      )
      parser.add_argument(
          "--analyze",
          metavar="PATH",
          help="Analyze project at PATH"
      )

      args = parser.parse_args()

      # 創建 agent
      agent = SpringMVCAnalyzerAgent(config_path=args.config)

      if args.interactive:
          # 交互式模式
          asyncio.run(agent.start_interactive())
      elif args.analyze:
          # 一次性分析
          asyncio.run(agent.analyze_project(args.analyze))
      else:
          parser.print_help()

  if __name__ == "__main__":
      main()
  ```

#### 1.5 基礎類實現

- [ ] **實現 sdk_agent/__init__.py**
  ```python
  """
  SDK Agent Mode for SpringMVC Analyzer.

  This module provides SDK-based agent functionality using Claude Agent SDK.
  """

  from .client import SpringMVCAnalyzerAgent
  from .exceptions import (
      SDKAgentError,
      SDKNotInstalledError,
      CLINotFoundError,
  )

  __all__ = [
      "SpringMVCAnalyzerAgent",
      "SDKAgentError",
      "SDKNotInstalledError",
      "CLINotFoundError",
  ]

  __version__ = "1.0.0"
  ```

- [ ] **實現 sdk_agent/exceptions.py**
  ```python
  """SDK Agent 異常定義"""

  class SDKAgentError(Exception):
      """SDK Agent 基礎錯誤"""
      pass

  class SDKNotInstalledError(SDKAgentError):
      """Claude Agent SDK 未安裝"""
      pass

  class CLINotFoundError(SDKAgentError):
      """Claude Code CLI 未找到"""
      pass

  class HookExecutionError(SDKAgentError):
      """Hook 執行錯誤"""
      pass

  class PermissionDeniedError(SDKAgentError):
      """權限被拒絕"""
      pass

  class ToolExecutionError(SDKAgentError):
      """工具執行錯誤"""
      pass
  ```

- [ ] **實現 sdk_agent/config.py**
  ```python
  """配置管理"""
  from pathlib import Path
  from typing import Dict, Any
  import yaml

  class SDKAgentConfig:
      """SDK Agent 配置管理器"""

      def __init__(self, config_path: str = "config/sdk_agent_config.yaml"):
          self.config_path = Path(config_path)
          self.config = self._load_config()

      def _load_config(self) -> Dict[str, Any]:
          """載入配置文件"""
          if not self.config_path.exists():
              return self._get_default_config()

          with open(self.config_path, 'r', encoding='utf-8') as f:
              config = yaml.safe_load(f)

          # 合併默認配置
          default = self._get_default_config()
          return self._merge_config(default, config)

      def _get_default_config(self) -> Dict[str, Any]:
          """獲取默認配置"""
          return {
              "server": {"mode": "agent"},
              "agent": {
                  "sdk_enabled": True,
                  "system_prompt_type": "default",
                  "hooks_enabled": True,
                  "permission_mode": "acceptEdits",
                  "max_turns": 20,
              }
          }

      def _merge_config(self, default: Dict, custom: Dict) -> Dict:
          """合併配置"""
          result = default.copy()
          for key, value in custom.items():
              if isinstance(value, dict) and key in result:
                  result[key] = self._merge_config(result[key], value)
              else:
                  result[key] = value
          return result

      def get(self, key: str, default=None):
          """獲取配置值"""
          keys = key.split(".")
          value = self.config
          for k in keys:
              if isinstance(value, dict):
                  value = value.get(k, default)
              else:
                  return default
          return value
  ```

### 驗證標準

- [ ] 目錄結構正確創建
- [ ] 配置文件可以正確加載
- [ ] 依賴安裝成功
- [ ] 入口點可執行（即使功能未實現）
- [ ] 無導入錯誤

---

## Phase 2: 工具適配

**目標**: 用 @tool 裝飾器包裝現有的 agent 功能，實現所有分析工具。

**預計時間**: 2 週
**狀態**: ⏳ Pending

### Checklist

#### 2.1 分析工具實現

- [ ] **實現 sdk_agent/tools/__init__.py**
  ```python
  """SDK Agent 工具集"""

  from .analysis_tools import (
      analyze_controller,
      analyze_jsp,
      analyze_service,
      analyze_mapper,
      analyze_procedure,
      analyze_directory,
  )

  from .graph_tools import (
      build_graph,
      export_graph,
  )

  from .query_tools import (
      query_graph,
      find_dependencies,
      analyze_impact,
  )

  # 所有工具列表
  ALL_TOOLS = [
      # 分析工具
      analyze_controller,
      analyze_jsp,
      analyze_service,
      analyze_mapper,
      analyze_procedure,
      analyze_directory,
      # 圖譜工具
      build_graph,
      export_graph,
      # 查詢工具
      query_graph,
      find_dependencies,
      analyze_impact,
  ]

  __all__ = [
      "analyze_controller",
      "analyze_jsp",
      "analyze_service",
      "analyze_mapper",
      "analyze_procedure",
      "analyze_directory",
      "build_graph",
      "export_graph",
      "query_graph",
      "find_dependencies",
      "analyze_impact",
      "ALL_TOOLS",
  ]
  ```

- [ ] **實現 analyze_controller 工具**
  - 文件: `sdk_agent/tools/analysis_tools.py`
  - 復用: `agents.controller_agent.ControllerAgent`
  - 輸入: `{file_path: str, include_details: bool}`
  - 輸出: 格式化文本 + analysis_data

- [ ] **實現 analyze_jsp 工具**
  - 文件: `sdk_agent/tools/analysis_tools.py`
  - 復用: `agents.jsp_agent.JSPAgent`
  - 輸入: `{file_path: str}`
  - 輸出: 格式化文本 + analysis_data

- [ ] **實現 analyze_service 工具**
  - 文件: `sdk_agent/tools/analysis_tools.py`
  - 復用: `agents.service_agent.ServiceAgent`
  - 輸入: `{file_path: str}`
  - 輸出: 格式化文本 + analysis_data

- [ ] **實現 analyze_mapper 工具**
  - 文件: `sdk_agent/tools/analysis_tools.py`
  - 復用: `agents.mapper_agent.MapperAgent`
  - 輸入: `{file_path: str}`
  - 輸出: 格式化文本 + analysis_data

- [ ] **實現 analyze_procedure 工具**
  - 文件: `sdk_agent/tools/analysis_tools.py`
  - 復用: `agents.procedure_agent.ProcedureAgent`
  - 輸入: `{file_path: str}`
  - 輸出: 格式化文本 + analysis_data

- [ ] **實現 analyze_directory 工具**
  - 文件: `sdk_agent/tools/analysis_tools.py`
  - 復用: 所有 agents
  - 輸入: `{directory_path: str, pattern: str, recursive: bool}`
  - 輸出: 批量分析結果

**代碼範例**:
```python
# sdk_agent/tools/analysis_tools.py
from claude_agent_sdk import tool
from typing import Any, Dict, Optional
from pathlib import Path
import logging

# 導入現有 agents
from agents.controller_agent import ControllerAgent
from agents.jsp_agent import JSPAgent
from agents.service_agent import ServiceAgent
from agents.mapper_agent import MapperAgent
from agents.procedure_agent import ProcedureAgent

# 全局 agent 實例（單例模式）
_agents: Dict[str, Any] = {}
_logger = logging.getLogger("sdk_agent.tools")

def _get_or_create_agent(agent_type: str):
    """獲取或創建 agent 實例（單例）"""
    if agent_type not in _agents:
        # TODO: 從配置創建 agent
        # 暫時使用默認配置
        if agent_type == "controller":
            _agents[agent_type] = ControllerAgent(...)
        elif agent_type == "jsp":
            _agents[agent_type] = JSPAgent(...)
        # ... 其他 agents
    return _agents[agent_type]

@tool(
    name="analyze_controller",
    description=(
        "Analyze Spring MVC Controller file to extract:\n"
        "- Request mappings (@RequestMapping, @GetMapping, etc.)\n"
        "- Service dependencies (@Autowired)\n"
        "- Method signatures and parameters\n"
        "- Return types and views"
    ),
    input_schema={
        "file_path": str,
        "include_details": bool
    }
)
async def analyze_controller(args: Dict[str, Any]) -> Dict[str, Any]:
    """分析 Controller 文件"""
    file_path = args["file_path"]
    include_details = args.get("include_details", True)

    _logger.info(f"Analyzing controller: {file_path}")

    # 驗證文件存在
    if not Path(file_path).exists():
        return {
            "content": [{
                "type": "text",
                "text": f"Error: File not found: {file_path}"
            }],
            "is_error": True
        }

    # 使用現有 ControllerAgent
    agent = _get_or_create_agent("controller")
    result = await agent.analyze(file_path)

    # 格式化輸出
    analysis = result.get("analysis", {})
    summary = f"""
Controller Analysis: {analysis.get('class_name', 'Unknown')}
{'=' * 60}
Package: {analysis.get('package', 'N/A')}
Base URL: {analysis.get('base_url', 'N/A')}
Methods: {len(analysis.get('methods', []))}
Dependencies: {len(analysis.get('dependencies', []))}
Confidence: {result.get('confidence', 0.0):.2%}
Model Used: {result.get('model_used', 'N/A')}
Cost: ${result.get('cost', 0.0):.4f}
    """.strip()

    if include_details and analysis.get('methods'):
        summary += "\n\nMethods:\n"
        for method in analysis['methods']:
            summary += f"  - {method.get('name')}() → {method.get('url', 'N/A')}\n"

    return {
        "content": [{
            "type": "text",
            "text": summary
        }],
        "analysis_data": result  # 完整數據供後續使用
    }

@tool(
    name="analyze_directory",
    description=(
        "Analyze all files in a directory matching a pattern.\n"
        "Automatically detects file types and uses appropriate agents."
    ),
    input_schema={
        "directory_path": str,
        "pattern": str,
        "recursive": bool
    }
)
async def analyze_directory(args: Dict[str, Any]) -> Dict[str, Any]:
    """批量分析目錄"""
    directory = Path(args["directory_path"])
    pattern = args.get("pattern", "**/*.java")
    recursive = args.get("recursive", True)

    if not directory.exists():
        return {
            "content": [{
                "type": "text",
                "text": f"Error: Directory not found: {directory}"
            }],
            "is_error": True
        }

    # 查找文件
    if recursive:
        files = list(directory.glob(pattern))
    else:
        files = list(directory.glob(pattern.replace("**/", "")))

    _logger.info(f"Found {len(files)} files matching pattern '{pattern}'")

    # 批量分析
    results = []
    for idx, file_path in enumerate(files, 1):
        agent_type = _detect_agent_type(str(file_path))
        if agent_type:
            _logger.info(f"[{idx}/{len(files)}] Analyzing {file_path.name} as {agent_type}")
            agent = _get_or_create_agent(agent_type)
            result = await agent.analyze(str(file_path))
            results.append({
                "file": str(file_path),
                "type": agent_type,
                "result": result
            })

    # 統計
    success_count = sum(1 for r in results if not r['result'].get('is_error'))
    total_cost = sum(r['result'].get('cost', 0.0) for r in results)

    summary = f"""
Directory Analysis Complete
{'=' * 60}
Total Files Found: {len(files)}
Successfully Analyzed: {success_count}
Failed: {len(results) - success_count}
Total Cost: ${total_cost:.4f}
    """.strip()

    return {
        "content": [{
            "type": "text",
            "text": summary
        }],
        "results": results
    }

def _detect_agent_type(file_path: str) -> Optional[str]:
    """自動檢測 agent 類型"""
    file_path_lower = file_path.lower()

    if file_path_lower.endswith(".jsp"):
        return "jsp"
    elif "controller" in file_path_lower and file_path_lower.endswith(".java"):
        return "controller"
    elif "service" in file_path_lower and file_path_lower.endswith(".java"):
        return "service"
    elif file_path_lower.endswith(".xml") and "mapper" in file_path_lower:
        return "mapper"
    elif file_path_lower.endswith((".sql", ".prc")):
        return "procedure"

    return None
```

#### 2.2 圖譜工具實現

- [ ] **實現 build_graph 工具**
  - 文件: `sdk_agent/tools/graph_tools.py`
  - 復用: `graph.graph_builder.GraphBuilder`
  - 功能: 從分析結果構建圖譜

- [ ] **實現 export_graph 工具**
  - 文件: `sdk_agent/tools/graph_tools.py`
  - 復用: `graph.graph_builder.GraphBuilder.save_graph()`
  - 功能: 導出圖譜為各種格式

#### 2.3 查詢工具實現

- [ ] **實現 query_graph 工具**
  - 文件: `sdk_agent/tools/query_tools.py`
  - 復用: `graph.graph_builder.GraphBuilder`
  - 功能: 查詢圖譜統計、節點、邊

- [ ] **實現 find_dependencies 工具**
  - 文件: `sdk_agent/tools/query_tools.py`
  - 復用: `graph.graph_builder.GraphBuilder.find_all_dependencies()`
  - 功能: 查找依賴關係

- [ ] **實現 analyze_impact 工具**
  - 文件: `sdk_agent/tools/query_tools.py`
  - 復用: `graph.graph_builder.GraphBuilder.find_all_dependents()`
  - 功能: 影響分析

### 驗證標準

- [ ] 所有工具可以獨立調用
- [ ] 工具正確復用現有 agents
- [ ] 輸出格式正確（content + 額外數據）
- [ ] 錯誤處理正確
- [ ] 日誌記錄完整

---

## Phase 3: Hooks 系統

**目標**: 實現 PreToolUse, PostToolUse, UserPromptSubmit 等 hooks。

**預計時間**: 1 週
**狀態**: ⏳ Pending

### Checklist

#### 3.1 驗證 Hooks

- [ ] **實現 validate_file_path hook**
  - 文件: `sdk_agent/hooks/validation_hooks.py`
  - 事件: `PreToolUse`
  - 功能: 檢查路徑遍歷、敏感目錄、文件存在性

- [ ] **實現 on_session_stop hook**
  - 文件: `sdk_agent/hooks/validation_hooks.py`
  - 事件: `Stop`
  - 功能: 清理資源、保存狀態

**代碼範例**:
```python
# sdk_agent/hooks/validation_hooks.py
from typing import Any, Dict, Optional
from claude_agent_sdk.types import HookContext, HookJSONOutput
import logging

_logger = logging.getLogger("sdk_agent.hooks.validation")

async def validate_file_path(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: HookContext
) -> HookJSONOutput:
    """
    PreToolUse Hook: 驗證文件路徑安全性。
    """
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # 只檢查文件分析工具
    if not tool_name.startswith("analyze_"):
        return {}

    file_path = tool_input.get("file_path", "")
    _logger.debug(f"Validating file path: {file_path}")

    # 檢查路徑遍歷攻擊
    dangerous_patterns = ["../", "..\\", "/etc/", "C:\\Windows", "/root", "/sys"]
    for pattern in dangerous_patterns:
        if pattern in file_path:
            _logger.warning(f"Dangerous path pattern detected: {pattern} in {file_path}")
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Security: Dangerous path pattern detected: {pattern}\n"
                        f"Path: {file_path}\n"
                        f"Please use a safe file path within your workspace."
                    )
                }
            }

    # 檢查文件存在性
    from pathlib import Path
    if not Path(file_path).exists():
        _logger.warning(f"File not found: {file_path}")
        # 不阻止，讓工具自己處理
        # 只記錄警告

    return {}

async def on_session_stop(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: HookContext
) -> HookJSONOutput:
    """
    Stop Hook: 會話停止時執行清理。
    """
    _logger.info("Session stopping - performing cleanup...")

    # TODO: 保存當前圖譜
    # TODO: 記錄會話統計
    # TODO: 清理臨時文件

    return {}
```

#### 3.2 上下文 Hooks

- [ ] **實現 add_project_context hook**
  - 文件: `sdk_agent/hooks/context_hooks.py`
  - 事件: `UserPromptSubmit`
  - 功能: 自動添加專案上下文

- [ ] **實現 on_pre_compact hook**
  - 文件: `sdk_agent/hooks/context_hooks.py`
  - 事件: `PreCompact`
  - 功能: Context 壓縮前記錄

#### 3.3 緩存 Hooks

- [ ] **實現 cache_analysis_result hook**
  - 文件: `sdk_agent/hooks/cache_hooks.py`
  - 事件: `PostToolUse`
  - 功能: 緩存分析結果

#### 3.4 Hook 註冊

- [ ] **實現 sdk_agent/hooks/__init__.py**
  ```python
  """SDK Agent Hooks"""

  from .validation_hooks import validate_file_path, on_session_stop
  from .context_hooks import add_project_context, on_pre_compact
  from .cache_hooks import cache_analysis_result

  # 默認 Hook 配置
  DEFAULT_HOOKS = {
      "PreToolUse": [validate_file_path],
      "PostToolUse": [cache_analysis_result],
      "UserPromptSubmit": [add_project_context],
      "Stop": [on_session_stop],
      "PreCompact": [on_pre_compact],
  }

  __all__ = [
      "validate_file_path",
      "on_session_stop",
      "add_project_context",
      "on_pre_compact",
      "cache_analysis_result",
      "DEFAULT_HOOKS",
  ]
  ```

### 驗證標準

- [ ] 所有 hooks 正確觸發
- [ ] 錯誤 hook 可以阻止工具執行
- [ ] 上下文 hook 正確添加信息
- [ ] 緩存 hook 正確保存結果
- [ ] 日誌記錄完整

---

## Phase 4: SDK Client

**目標**: 實現 SpringMVCAnalyzerAgent 主類，集成所有組件。

**預計時間**: 1 週
**狀態**: ⏳ Pending

### Checklist

#### 4.1 Client 實現

- [ ] **實現 SpringMVCAnalyzerAgent.__init__()**
  - 載入配置
  - 初始化 logger
  - 準備 SDK server

- [ ] **實現 _create_sdk_server()**
  - 使用 create_sdk_mcp_server
  - 註冊所有工具

- [ ] **實現 _create_options()**
  - 創建 ClaudeAgentOptions
  - 配置 system prompt
  - 配置 hooks
  - 配置 permissions

- [ ] **實現 start_interactive()**
  - 啟動交互式對話循環
  - 處理用戶輸入
  - 顯示響應

- [ ] **實現 analyze_project()**
  - 一次性分析專案
  - 返回結果

- [ ] **實現動態控制方法**
  - set_model()
  - set_permission_mode()
  - interrupt()
  - get_server_info()

**代碼範例** (完整文件太長，見附錄)

#### 4.2 Permission 實現

- [ ] **實現 can_use_tool 回調**
  - 文件: `sdk_agent/permissions.py`
  - 功能: 程序化控制工具權限

#### 4.3 System Prompt

- [ ] **創建默認 system prompt**
  - 文件: `sdk_agent/prompts/system_prompt.txt`
  - 內容: Agent 能力說明、使用指南

### 驗證標準

- [ ] Client 可以正常初始化
- [ ] 交互模式可以啟動
- [ ] 工具可以正常調用
- [ ] Hooks 正確執行
- [ ] 權限正確檢查
- [ ] 動態控制正常工作

---

## Phase 5: 測試

**目標**: 編寫集成測試，驗證所有功能。

**預計時間**: 1-2 週
**狀態**: ⏳ Pending

### Checklist

#### 5.1 單元測試

- [ ] **測試工具函數**
  - `test_analyze_controller()`
  - `test_analyze_directory()`
  - `test_build_graph()`
  - `test_query_graph()`

- [ ] **測試 Hooks**
  - `test_validate_file_path_hook()`
  - `test_add_context_hook()`
  - `test_cache_hook()`

#### 5.2 集成測試

- [ ] **創建 tests/integration/test_sdk_agent.py**

- [ ] **測試完整工作流**
  ```python
  @pytest.mark.integration
  @pytest.mark.asyncio
  async def test_sdk_agent_full_workflow():
      """測試完整分析工作流"""
      agent = SpringMVCAnalyzerAgent()

      # 分析文件
      result = await agent.analyze_file("/path/to/Controller.java")
      assert result is not None

      # 構建圖譜
      graph = agent.get_graph()
      assert graph.number_of_nodes() > 0

      # 查詢依賴
      deps = await agent.query("Find dependencies of UserController")
      assert deps is not None
  ```

- [ ] **測試錯誤處理**
- [ ] **測試 Hook 觸發**
- [ ] **測試權限控制**

### 驗證標準

- [ ] 所有測試通過
- [ ] 代碼覆蓋率 > 80%
- [ ] 無明顯 bug

---

## Phase 6: 文檔和發布

**目標**: 完善文檔，準備發布。

**預計時間**: 1 週
**狀態**: ⏳ Pending

### Checklist

#### 6.1 用戶文檔

- [x] **SDK_AGENT_SPECIFICATION.md** - 技術規格
- [ ] **SDK_AGENT_GUIDE.md** - 使用指南
- [ ] **MIGRATION_TO_SDK.md** - 遷移指南

#### 6.2 開發文檔

- [x] **SDK_AGENT_IMPLEMENTATION_PLAN.md** - 實施計劃（本文檔）
- [ ] **SDK_INTEGRATION_PROGRESS.md** - 進度追蹤

#### 6.3 更新現有文檔

- [ ] **README.md**
  - 添加 SDK Agent Mode 說明
  - 更新快速開始

- [ ] **docs/ARCHITECTURE.md**
  - 更新架構圖
  - 添加 SDK Agent 流程

- [ ] **docs/MCP_INTEGRATION.md**
  - 添加三種模式對比

#### 6.4 示例代碼

- [ ] **創建 examples/sdk_agent_demo.py**
  - 完整使用示例
  - 交互式示例
  - 批量分析示例

### 驗證標準

- [ ] 所有文檔完整
- [ ] 示例代碼可運行
- [ ] README 清晰明了

---

## 驗收標準

### 功能完整性

- [ ] 所有 11 個工具實現並測試
- [ ] 所有 5 個 Hook 事件實現
- [ ] Client 所有方法實現
- [ ] 權限系統工作正常

### 質量標準

- [ ] 代碼覆蓋率 > 80%
- [ ] 無 critical bugs
- [ ] 性能可接受（與 MCP mode 相當）

### 文檔完整性

- [ ] 技術規格完整
- [ ] 使用指南清晰
- [ ] API 文檔完整
- [ ] 示例代碼可運行

### 兼容性

- [ ] 不破壞現有 API Mode
- [ ] 不破壞現有 Passive Mode
- [ ] 配置向後兼容

---

## 風險和緩解

### 風險 1: Claude Code CLI 依賴

**風險**: SDK 依賴 Claude Code CLI，用戶可能未安裝

**緩解**:
- 提供清晰的安裝文檔
- 在啟動時檢查 CLI 是否存在
- 提供友好的錯誤信息

### 風險 2: SDK 版本兼容性

**風險**: Claude Agent SDK 可能更新破壞兼容性

**緩解**:
- 固定 SDK 版本 (>=0.1.0, <0.2.0)
- 定期測試新版本
- 文檔中明確支持的版本

### 風險 3: 性能開銷

**風險**: SDK 層可能增加性能開銷

**緩解**:
- 性能測試和優化
- 使用單例模式減少重複初始化
- 緩存分析結果

### 風險 4: 複雜度增加

**風險**: 三種模式增加維護複雜度

**緩解**:
- 最大化代碼復用
- 清晰的模式切換邏輯
- 詳細的文檔

---

## 附錄

### A. 完整 Client 實現骨架

```python
# sdk_agent/client.py
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    HookMatcher,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
)
from typing import Optional, List, Dict, Any, AsyncGenerator
from pathlib import Path
import logging

from .config import SDKAgentConfig
from .tools import ALL_TOOLS
from .hooks import DEFAULT_HOOKS
from .permissions import can_use_tool

class SpringMVCAnalyzerAgent:
    """Spring MVC Analyzer Agent using Claude Agent SDK"""

    def __init__(
        self,
        config_path: Optional[str] = None,
        system_prompt: Optional[str] = None,
        hooks_enabled: bool = True,
        permission_mode: str = "acceptEdits",
        max_turns: int = 20
    ):
        self.config = SDKAgentConfig(config_path or "config/sdk_agent_config.yaml")
        self.logger = logging.getLogger("sdk_agent")
        self.client: Optional[ClaudeSDKClient] = None
        self.graph_builder = None  # 延遲初始化

        # 覆蓋配置
        if system_prompt:
            self.custom_system_prompt = system_prompt
        if not hooks_enabled:
            self.config.config["agent"]["hooks_enabled"] = False

    def _create_sdk_server(self):
        """創建 SDK MCP Server"""
        return create_sdk_mcp_server(
            name="springmvc-analyzer",
            version="1.0.0",
            tools=ALL_TOOLS
        )

    def _create_options(self) -> ClaudeAgentOptions:
        """創建 Agent Options"""
        server = self._create_sdk_server()

        # 構建 hooks
        hooks = {}
        if self.config.get("agent.hooks_enabled", True):
            for event, callbacks in DEFAULT_HOOKS.items():
                hooks[event] = [
                    HookMatcher(matcher=None, hooks=callbacks)
                ]

        return ClaudeAgentOptions(
            system_prompt=self._get_system_prompt(),
            mcp_servers={"analyzer": server},
            allowed_tools=self.config.get("agent.allowed_tools", []),
            hooks=hooks if hooks else None,
            can_use_tool=can_use_tool,
            permission_mode=self.config.get("agent.permission_mode", "acceptEdits"),
            max_turns=self.config.get("agent.max_turns", 20),
            include_partial_messages=self.config.get("agent.include_partial_messages", True),
            cwd=Path.cwd()
        )

    def _get_system_prompt(self) -> str:
        """獲取 system prompt"""
        # TODO: 載入 prompt 文件或使用默認
        return "You are a Spring MVC project analyzer..."

    async def start_interactive(self) -> None:
        """啟動交互式對話模式"""
        options = self._create_options()

        async with ClaudeSDKClient(options=options) as client:
            self.client = client
            print("🚀 SpringMVC Analyzer Agent (SDK Mode)")
            print("=" * 60)
            print("Type 'exit' or 'quit' to exit")
            print()

            while True:
                try:
                    user_input = input("\n👤 You: ")

                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("👋 Goodbye!")
                        break

                    if not user_input.strip():
                        continue

                    await client.query(user_input)

                    print("\n🤖 Agent:")

                    async for message in client.receive_response():
                        if isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, TextBlock):
                                    print(block.text)
                                elif isinstance(block, ToolUseBlock):
                                    print(f"  [Using tool: {block.name}]")

                except KeyboardInterrupt:
                    print("\n\n👋 Interrupted")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
                    self.logger.error(f"Error: {e}", exc_info=True)

    # 其他方法...
```

---

**版本**: 1.0.0
**維護者**: SpringMVC Agent Analyzer Team
**最後更新**: 2025-10-05
