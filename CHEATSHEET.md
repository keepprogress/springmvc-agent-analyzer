# Quick Reference Cheatsheet

**SpringMVC Agent Analyzer - Essential Information at a Glance**

Version: 0.1.0 | Last Updated: 2025-10-05

---

## 🎯 Core Philosophy

```
Old: Code Parsers + LLM Gap-Filling = $40/project, $12K/year maintenance
New: LLM Agents + Code Validation = $4.23/project, $2K/year maintenance
Savings: 53% analysis cost, 83% maintenance cost
```

**Key Principle**: **LLMs are PRIMARY analyzers, NOT gap-fillers**

---

## 📁 Project Structure

```
springmvc-agent-analyzer/
├── agents/              # Analysis agents (Controller, JSP, Service, etc.)
│   ├── base_agent.py   # ⭐ Abstract base class
│   ├── controller_agent.py
│   ├── jsp_agent.py
│   ├── service_agent.py
│   ├── mapper_agent.py
│   └── procedure_agent.py
│
├── core/               # Infrastructure
│   ├── model_router.py     # ⭐ Haiku→Sonnet→Opus routing
│   ├── prompt_manager.py   # ⭐ Template + Learning
│   ├── cache_manager.py    # 60-80% hit rate
│   └── cost_tracker.py     # Budget monitoring
│
├── validators/         # Lightweight syntax validators
│   ├── java_validator.py
│   ├── xml_validator.py
│   └── sql_validator.py
│
├── graph/              # Knowledge graph
│   ├── builder.py          # Build from analysis results
│   ├── query.py            # Find chains, impact, orphans
│   └── visualizer.py       # Mermaid, PyVis, GraphML
│
├── mcp/                # MCP Protocol integration
│   └── server.py           # 8 tools, Claude Code integration
│
├── prompts/            # Prompt templates & examples
│   ├── base/               # *.txt templates
│   ├── examples/           # *.json few-shot examples
│   └── learned/            # Self-improved prompts
│
├── config/             # Configuration
│   ├── config.yaml         # ⭐ Main config
│   └── oracle_config.yaml  # DB connection (not committed)
│
├── tests/              # Testing
│   ├── unit/
│   ├── integration/
│   └── fixtures/           # Test data
│
└── docs/               # Documentation
    ├── ARCHITECTURE.md
    ├── ARCHITECTURE_DIAGRAMS.md
    └── TECHNICAL_SPECIFICATION.md
```

---

## 🚀 Quick Start Commands

```bash
# Setup
cd C:/Developer/springmvc-agent-analyzer
pip install -e ".[dev]"
echo "ANTHROPIC_API_KEY=your_key" > .env

# Run setup validation
python scripts/setup.py

# Run tests
pytest tests/

# Start MCP server
python -m mcp.server

# Run benchmark
python scripts/benchmark.py
```

---

## ⚙️ Configuration Quick Reference

### config/config.yaml Key Settings

```yaml
llm:
  routing:
    screening_model: "claude-3-5-haiku-20241022"      # $0.25/1M
    analysis_model: "claude-3-5-sonnet-20250929"     # $3/1M
    critical_model: "claude-3-opus-20240229"         # $15/1M

  thresholds:
    screening_confidence: 0.9   # Haiku must score >= 0.9 to accept
    analysis_confidence: 0.85   # Sonnet must score >= 0.85 to accept

cache:
  enabled: true
  ttl_days: 30
  max_cache_size: 10000
  similarity_threshold: 0.85

cost:
  budget_per_project: 5.0
  alert_threshold: 0.8

agents:
  batch_size: 10
  max_workers: 4
  min_confidence: 0.7

graph:
  max_depth: 10
  max_paths: 100
```

---

## 💰 Cost Model

### Model Pricing

| Model | Input ($/1M tokens) | Output ($/1M tokens) | Best For |
|-------|---------------------|----------------------|----------|
| **Haiku** | $0.25 | $1.25 | Simple controllers, standard services |
| **Sonnet** | $3.00 | $15.00 | Complex JSP, nested mappers, SQL |
| **Opus** | $15.00 | $75.00 | Ambiguous deps, procedures, edge cases |

### Expected Distribution

- **70% Haiku** - Simple cases (saves 92% vs Sonnet)
- **25% Sonnet** - Medium complexity (saves 80% vs Opus)
- **5% Opus** - Complex/ambiguous

### Cost Examples

```
Single Controller File:
  Haiku:  ~1500 tokens input, ~400 tokens output = $0.002
  Sonnet: ~1500 tokens input, ~400 tokens output = $0.015
  Opus:   ~1500 tokens input, ~400 tokens output = $0.075

100 Files (with 60% cache):
  40 Haiku queries   × $0.002 = $0.08
  10 Sonnet queries  × $0.015 = $0.15
  2 Opus queries     × $0.075 = $0.15
  Total: ~$0.38 (vs $40 for parser approach)
```

---

## 🔄 Model Router Decision Flow

```
Input: Query with complexity level
  │
  ▼
┌─────────────┐
│ Cache Check │──── HIT ────► Return (Cost: $0)
└─────┬───────┘
      │ MISS
      ▼
┌──────────────────┐
│ Complexity?      │
└──┬───┬───┬───────┘
   │   │   │
Simple Medium Complex
   │   │   │
   └───┴───┘
      │
      ▼
┌─────────────┐
│ Try Haiku   │
└─────┬───────┘
      │
      ▼
┌──────────────────┐
│ Confidence >= 0.9? │──── YES ────► Return Haiku Result
└─────┬────────────┘
      │ NO
      ▼
┌─────────────┐
│ Try Sonnet  │
└─────┬───────┘
      │
      ▼
┌──────────────────────┐
│ Confidence >= 0.85?  │──── YES ────► Return Sonnet Result
└─────┬────────────────┘
      │ NO
      ▼
┌─────────────┐
│ Try Opus    │
└─────┬───────┘
      │
      ▼
  Return Opus Result
```

---

## 📊 Agent Analysis Output Format

### Common Structure

```json
{
  "file_path": "src/controllers/UserController.java",
  "agent_name": "controller",
  "timestamp": "2025-10-05T10:30:45Z",
  "cached": false,

  "analysis": {
    // Agent-specific structure (see below)
  },

  "metadata": {
    "confidence": 0.92,
    "model_used": "claude-3-5-haiku-20241022",
    "cost": 0.00234,
    "tokens": {"input": 1245, "output": 356},
    "escalations": 0,
    "validation": {
      "syntax_valid": true,
      "issues": []
    }
  }
}
```

### Controller Analysis

```json
{
  "analysis": {
    "class_name": "UserController",
    "package": "com.example.controller",
    "class_level_mapping": "/users",
    "mappings": [
      {
        "method_name": "listUsers",
        "path": "/users/list",
        "http_method": "GET",
        "parameters": [],
        "return_type": "ModelAndView"
      }
    ],
    "dependencies": [
      {"field_name": "userService", "type": "UserService"}
    ],
    "confidence": 0.92,
    "notes": "Standard Spring MVC pattern"
  }
}
```

### JSP Analysis

```json
{
  "analysis": {
    "includes": [
      {"type": "static", "target": "header.jsp"}
    ],
    "ajax_calls": [
      {
        "type": "jquery",
        "url": "/users/list",
        "method": "GET",
        "line_number": 45
      }
    ],
    "forms": [
      {"action": "/users/save", "method": "POST"}
    ],
    "confidence": 0.88
  }
}
```

---

## 🗺️ Knowledge Graph Schema

### Node Types

| Type | Properties | Example ID |
|------|-----------|-----------|
| **JSP** | `file_path`, `includes`, `ajax_count` | `jsp_userList` |
| **CONTROLLER** | `class_name`, `mappings` | `ctrl_UserController_listUsers` |
| **SERVICE** | `class_name`, `transactional` | `svc_UserService_listUsers` |
| **MAPPER** | `interface`, `xml_file`, `statements` | `map_UserMapper_selectAll` |
| **TABLE** | `columns`, `primary_key` | `tbl_USERS` |
| **PROCEDURE** | `operation_type`, `trigger_method` | `proc_SYNC_USER_DATA` |

### Edge Types

| Type | Source → Target | Attributes |
|------|----------------|-----------|
| **INCLUDES** | JSP → JSP | `type` |
| **AJAX_CALL** | JSP → CONTROLLER | `url`, `http_method` |
| **INVOKES** | CONTROLLER → SERVICE | `method` |
| **CALLS** | SERVICE → MAPPER | `method` |
| **QUERIES** | MAPPER → TABLE | `operation`, `columns` |
| **EXECUTES** | MAPPER → PROCEDURE | `statement_type` |

---

## 🧪 Testing Quick Commands

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific test
pytest tests/unit/test_base_agent.py -v

# With coverage
pytest --cov=agents --cov=core --cov-report=html

# Benchmark POC
python scripts/benchmark.py --files=20 --output=benchmark_results.json
```

---

## 📝 Prompt Template Format

### Location
`prompts/base/<agent>_analysis.txt`

### Template Structure

```
You are a [DOMAIN] expert analyzer.

Analyze the following [FILE_TYPE] and extract [TARGETS].

# Task

Extract:
1. [Item 1]
2. [Item 2]
...

# Input

File: {file_path}

```[language]
{code}
```

# Output Format

Return ONLY valid JSON (no markdown, no explanation):

{{
  "field1": "type",
  "field2": [...],
  "confidence": 0.0-1.0,
  "notes": "string"
}}

# Confidence Guidelines

- 0.9-1.0: Very clear, standard pattern
- 0.8-0.9: Clear with minor ambiguity
- 0.7-0.8: Some ambiguity, reasonable inference
- < 0.7: High ambiguity, low confidence
```

### Few-Shot Examples Format

`prompts/examples/<agent>_analysis.json`

```json
[
  {
    "description": "Brief description",
    "input": "Code snippet",
    "output": {
      "expected_field1": "value",
      "confidence": 0.95
    }
  }
]
```

---

## 🔍 Common Queries

### Find Call Chain

```python
from graph.query import QueryEngine

query = QueryEngine(graph)
chains = query.find_call_chains(
    start_node="jsp_userList",
    end_node="tbl_USERS",
    max_depth=10,
    max_paths=100
)

# Result: [
#   ["jsp_userList", "ctrl_UserController_listUsers",
#    "svc_UserService_listUsers", "map_UserMapper_selectAll", "tbl_USERS"]
# ]
```

### Impact Analysis

```python
impact = query.find_impact("tbl_USERS")

# Result: {
#   "direct": ["map_UserMapper_selectAll", "map_UserMapper_insert"],
#   "indirect": ["svc_UserService_listUsers"],
#   "ui": ["jsp_userList", "jsp_userEdit"]
# }
```

### Find Orphans

```python
orphans = query.find_orphans(node_type="JSP")

# Result: ["jsp_oldReport", "jsp_unused"]
```

---

## 🐛 Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in code
logger = logging.getLogger("agents.controller")
logger.setLevel(logging.DEBUG)
```

### Check Cache Stats

```python
from core.cache_manager import CacheManager

cache = CacheManager()
stats = cache.get_stats()

print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Cache files: {stats['cache_files']}")
```

### Check Cost

```python
from core.cost_tracker import CostTracker

tracker = CostTracker()
tracker.print_summary()

# Output:
# Total Cost: $2.34
# Cached: 60 queries (60%)
# Budget: $5.00 (53.2% remaining)
```

### Validate Prompt

```python
from core.prompt_manager import PromptManager

pm = PromptManager()
prompt = pm.build_prompt(
    template_name="controller_analysis",
    context={"file_path": "test.java", "code": "..."},
    include_examples=True
)

print(f"Prompt length: {len(prompt)} chars")
print(f"Estimated tokens: {len(prompt) / 4}")  # Rough estimate
```

---

## ⚡ Performance Optimization Tips

### 1. Maximize Cache Usage

```python
# Avoid force_refresh unless necessary
result = agent.analyze(file_path, force_refresh=False)  # Default

# Clear stale cache periodically
cache.clear(older_than_days=30)
```

### 2. Batch Similar Files

```python
# Group files by type for better LLM context
controllers = glob.glob("**/*Controller.java")
for batch in chunks(controllers, batch_size=10):
    results = parallel_analyze(batch)
```

### 3. Use Appropriate Complexity

```python
# Simple files
result = agent._query_llm(prompt, complexity="simple")  # Tries Haiku first

# Complex files
result = agent._query_llm(prompt, complexity="complex")  # Starts with Sonnet
```

### 4. Parallel Processing

```python
# Use max_workers for large codebases
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(agent.analyze, file_paths))
```

---

## 🚨 Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `APIError` | Anthropic API issue | Check API key, retry with backoff |
| `JSONDecodeError` | LLM response malformed | Lower temperature, refine prompt |
| `ConfidenceTooLow` | Ambiguous code | Escalate to higher model |
| `CacheMiss` | File changed | Normal, will re-analyze |
| `ValidationError` | Syntax invalid | Check validator, may need manual review |

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def analyze_with_retry(file_path):
    return await agent.analyze(file_path)
```

---

## 📅 Implementation Checklist

### Phase 1: Foundation (Week 1-2)
- [ ] `agents/base_agent.py` - Abstract base class
- [ ] `core/model_router.py` - Hierarchical routing
- [ ] `core/prompt_manager.py` - Template management
- [ ] `core/cache_manager.py` - Semantic caching
- [ ] `core/cost_tracker.py` - Budget monitoring
- [ ] `scripts/setup.py` - Setup validation
- [ ] Integration tests pass

### Phase 2: Controller POC (Week 3-4) ⭐ CRITICAL
- [ ] `agents/controller_agent.py` - Full implementation
- [ ] `prompts/base/controller_analysis.txt` - Template
- [ ] `prompts/examples/controller_analysis.json` - Examples
- [ ] `validators/java_validator.py` - Syntax validator
- [ ] 20 test fixtures created
- [ ] Gold standard created
- [ ] Benchmark >= 90% accuracy
- [ ] Cost <= $1 for 20 files
- [ ] **Decision**: Proceed or pivot?

### Phase 3: Expand Agents (Week 5-8)
- [ ] JSP Agent (Week 5)
- [ ] Service Agent (Week 6)
- [ ] Mapper Agent (Week 7)
- [ ] Procedure Agent (Week 8)

### Phase 4: Knowledge Graph (Week 9-10)
- [ ] Graph Builder
- [ ] Query Engine
- [ ] Visualizer

### Phase 5: MCP Integration (Week 11-12)
- [ ] MCP Server
- [ ] 8 MCP tools registered
- [ ] Claude Code integration works

### Phase 6: Production (Week 13-14)
- [ ] >= 80% test coverage
- [ ] All documentation complete
- [ ] Real-world validation successful

---

## 🎯 Success Criteria (Final)

**Must-Have** (80% required):
- ✅ Accuracy >= 90% (across all agents)
- ✅ Cost <= $5 per project (100 files)
- ✅ Cache hit rate >= 60%
- ✅ Maintenance <= 2 hrs/month

**Nice-to-Have** (Bonus):
- ✅ Cost <= $3 per project
- ✅ Cache hit rate >= 70%
- ✅ Accuracy >= 95%

**Failure Triggers** (Immediate review):
- ❌ Accuracy < 80%
- ❌ Cost > $10 per project
- ❌ Cache hit rate < 40%

---

## 🔗 Quick Links

| Resource | Location |
|----------|----------|
| **Detailed Plan** | `IMPLEMENTATION_PLAN.md` |
| **Architecture** | `docs/ARCHITECTURE.md` |
| **Diagrams** | `docs/ARCHITECTURE_DIAGRAMS.md` |
| **Tech Spec** | `docs/TECHNICAL_SPECIFICATION.md` |
| **Quick Start** | `QUICKSTART.md` |
| **Old Project** | `C:/Developer/springmvc-knowledge-graph` |
| **Anthropic Docs** | https://docs.anthropic.com |
| **MCP Protocol** | https://github.com/anthropics/mcp |

---

## 💡 Remember

1. **LLM-First**: Let Claude do the heavy lifting, don't over-engineer parsers
2. **Cost-Conscious**: Use Haiku when possible, escalate only when needed
3. **Cache Everything**: 60% hit rate = 60% cost savings
4. **Validate Lightly**: Syntax only, not semantics
5. **Learn Continuously**: Save successful patterns as few-shot examples
6. **Measure Everything**: Track cost, accuracy, confidence, latency

---

**Last Updated**: 2025-10-05
**Version**: 0.1.0
**For Questions**: See `README.md` or `QUICKSTART.md`

---

**Print this page and keep it handy during implementation!** 📌
