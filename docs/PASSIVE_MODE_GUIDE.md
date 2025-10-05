# Passive Mode Guide for Claude Code Subscription Users

## Overview

This guide is for users who have **Claude Code subscription** (not Anthropic API subscription) and want to use the SpringMVC Agent Analyzer with their existing subscription.

## What is Passive Mode?

The SpringMVC Agent Analyzer operates in two modes:

### API Mode (Default)
- MCP server calls Anthropic API directly
- Requires `ANTHROPIC_API_KEY` environment variable
- Requires separate API subscription (pay-per-token)
- Uses hierarchical model routing (Haiku → Sonnet → Opus)

### Passive Mode (For Claude Code Subscription Users) ⭐
- MCP server provides tools for Claude Code to use
- **No API key required**
- **No additional API subscription needed**
- Uses your existing Claude Code subscription (Sonnet 4.5)
- Claude Code performs analysis, MCP server manages graph

## Why Use Passive Mode?

**You should use Passive Mode if:**
- ✅ You have Claude Code subscription (not API subscription)
- ✅ You only have access to one model (e.g., Sonnet 4.5)
- ✅ You want to avoid paying for API calls separately
- ✅ You don't have `ANTHROPIC_API_KEY`

**Benefits:**
- No duplicate LLM costs (already paying for Claude Code)
- Simpler setup (no API key configuration)
- Full graph analysis capabilities
- Use your familiar Claude Code interface

## Setup

### 1. Configure Passive Mode

Edit `config/config.yaml`:

```yaml
# Server Mode Configuration
server:
  mode: "passive"  # Change from "api" to "passive"

# Rest of configuration...
```

### 2. Configure Claude Code MCP Settings

Add to `.claude/mcp_settings.json`:

```json
{
  "mcpServers": {
    "springmvc-analyzer": {
      "command": "python",
      "args": ["/path/to/springmvc-agent-analyzer/run_mcp_server.py"]
    }
  }
}
```

**Note**: No `ANTHROPIC_API_KEY` needed!

### 3. Restart Claude Code

The MCP server will start in Passive mode.

## Available Tools (Passive Mode)

### 1. `read_file_with_prompt`

Read a file and get the analysis prompt template.

**Usage:**
```
Use read_file_with_prompt to analyze src/main/java/com/example/UserController.java
```

**Returns:**
- File content
- Appropriate prompt template
- Instructions for analysis

**Example workflow:**
```
User: "Analyze UserController.java"
↓
1. Claude Code calls: read_file_with_prompt
2. Gets: file content + controller analysis prompt
3. Claude Code analyzes using the prompt
4. Generates structured JSON result
```

### 2. `submit_analysis`

Submit your analysis results to build the knowledge graph.

**Usage:**
After analyzing a file, submit results:
```
Use submit_analysis with:
- file_path: "src/main/java/com/example/UserController.java"
- agent_type: "controller"
- analysis: {<your analysis JSON>}
- confidence: 0.95
```

### 3. `build_graph`

Build the knowledge graph from all submitted analyses.

**Usage:**
```
Use build_graph to construct the knowledge graph from analyzed files
```

**Returns:**
- Number of nodes added
- Number of edges added
- Graph statistics

### 4. Graph Query Tools

Same as API mode:
- `query_graph` - Query nodes, relationships, statistics
- `find_dependencies` - Find all dependencies of a node
- `analyze_impact` - Analyze impact of changing a node
- `export_graph` - Export graph to visualization format

## Typical Workflow

### Scenario 1: Analyze Single File

```
User: "Please analyze UserController.java"

Step 1: Claude Code calls read_file_with_prompt
- MCP server returns file content + prompt template

Step 2: Claude Code analyzes the file
- Uses Sonnet 4.5 to analyze (internal to Claude Code)
- Generates structured JSON result

Step 3: Claude Code calls submit_analysis
- Submits results to MCP server
- MCP server stores for graph building

Step 4: Claude Code calls build_graph
- MCP server constructs graph from results
```

### Scenario 2: Analyze Directory

```
User: "Analyze all controllers in src/main/java/controllers/"

Step 1: Claude Code lists files
- Uses file system tools to find *.java files

Step 2: For each file:
  a. Call read_file_with_prompt
  b. Analyze using Sonnet 4.5
  c. Call submit_analysis

Step 3: Call build_graph
- Build complete knowledge graph

Step 4: Call query_graph
- Show graph statistics and insights
```

### Scenario 3: Impact Analysis

```
User: "If I change UserService, what will be affected?"

Step 1: Claude Code calls analyze_impact
- MCP server queries graph for dependents

Step 2: Claude Code presents results
- Lists all affected Controllers, JSPs, etc.
- Shows dependency chains
```

## Prompt Templates

In Passive mode, prompt templates are available as MCP resources:

- `prompts://controller` - Controller analysis prompt
- `prompts://jsp` - JSP analysis prompt
- `prompts://service` - Service analysis prompt
- `prompts://mapper` - MyBatis Mapper analysis prompt
- `prompts://procedure` - Stored Procedure analysis prompt

**Access via:**
```
Read the prompts://controller resource to see the analysis template
```

## Comparison: API Mode vs Passive Mode

| Feature | API Mode | Passive Mode |
|---------|----------|--------------|
| **API Key Required** | ✅ Yes | ❌ No |
| **API Subscription** | ✅ Required | ❌ Not needed |
| **Model Selection** | Haiku/Sonnet/Opus | Claude Code (Sonnet 4.5) |
| **Cost** | Pay per API call | Included in subscription |
| **Who Analyzes** | MCP server agents | Claude Code |
| **Graph Building** | ✅ Automatic | ✅ Via build_graph tool |
| **Graph Queries** | ✅ Yes | ✅ Yes |
| **Visualization** | ✅ Yes | ✅ Yes |
| **Autonomous Batch** | ✅ Yes | ❌ Interactive |

## Example: Complete Analysis Session

```markdown
User: I need to analyze my SpringMVC project in src/main/java/

Claude Code:
I'll help you analyze your SpringMVC project. Let me start by reading
the first controller.

[Calls: read_file_with_prompt for UserController.java]
[Receives: file content + controller analysis prompt]

Now analyzing UserController.java...
[Analyzes using built-in Sonnet 4.5]

Found:
- Class: UserController
- Base URL: /users
- Methods: list, create, update, delete
- Services: UserService
- Views: users/list.jsp, users/form.jsp

[Calls: submit_analysis with structured results]

Shall I continue with the other controllers?

User: Yes, analyze all of them

Claude Code:
[Repeats for each controller...]
[Calls: submit_analysis for each]

Now building the knowledge graph...
[Calls: build_graph]

Graph built successfully:
- 15 nodes (5 Controllers, 8 JSPs, 2 Services)
- 23 edges (dependencies and relationships)

Would you like me to:
1. Show impact analysis for a specific component?
2. Export the graph for visualization?
3. Find circular dependencies?
```

## Troubleshooting

### Server won't start in Passive mode

**Check:**
1. `config/config.yaml` has `server.mode: "passive"`
2. No `ANTHROPIC_API_KEY` in environment (not needed)
3. Python dependencies installed: `pip install -r requirements.txt`

### Analysis results not stored

**Solution:**
- Ensure you call `submit_analysis` after each file analysis
- Check file_path matches exactly
- Verify analysis JSON structure matches agent schema

### Graph is empty

**Common causes:**
1. Forgot to call `build_graph` after submitting analyses
2. No analyses submitted yet
3. Analysis results don't match expected schema

**Solution:**
```
1. Use read_file_with_prompt for each file
2. Analyze and call submit_analysis
3. Call build_graph to construct graph
4. Call query_graph to verify
```

## FAQ

**Q: Can I mix API mode and Passive mode?**
A: No, choose one mode per MCP server instance. You can run two separate instances if needed.

**Q: Is Passive mode slower?**
A: Analysis speed is similar (both use Claude Sonnet). Passive mode requires more back-and-forth between Claude Code and MCP server, but each analysis is comparable.

**Q: Can I switch modes later?**
A: Yes, just edit `config/config.yaml` and restart the MCP server.

**Q: Does Passive mode have all features?**
A: Almost all! Graph queries, visualization, impact analysis all work. The main difference is interactive vs autonomous batch processing.

**Q: What if I get an API subscription later?**
A: Simply switch to `mode: "api"` in config and add `ANTHROPIC_API_KEY`. You can reuse all your existing graph data.

## Best Practices

1. **Analyze systematically**: Process files in order (Controllers → Services → Mappers)
2. **Build graph incrementally**: Call `build_graph` after each batch of files
3. **Verify results**: Use `query_graph` to check graph stats regularly
4. **Save prompts**: Read prompt resources once and reuse the templates
5. **Export regularly**: Use `export_graph` to save progress

## Next Steps

1. Configure Passive mode: Edit `config/config.yaml`
2. Start MCP server: Ensure Claude Code can connect
3. Analyze your first file: Use `read_file_with_prompt`
4. Build your graph: Submit analyses and call `build_graph`
5. Explore dependencies: Use graph query tools

For more information, see:
- [MCP Integration Guide](./MCP_INTEGRATION.md)
- [Architecture Documentation](./ARCHITECTURE.md)
- [Technical Specification](./TECHNICAL_SPECIFICATION.md)
