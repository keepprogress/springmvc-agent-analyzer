# MCP Integration Guide

## Overview

The SpringMVC Agent Analyzer provides a Model Context Protocol (MCP) server for integration with Claude Code and other MCP clients. This enables interactive code analysis directly within your development environment.

## Three Operating Modes

The project supports three distinct operating modes:

### 🔧 API Mode (MCP Server with API)
- **For users with**: Anthropic API subscription
- **Requires**: `ANTHROPIC_API_KEY` environment variable
- **How it works**: MCP server calls Anthropic API directly for analysis
- **Best for**: Autonomous batch processing, cost optimization via model routing
- **Interface**: MCP Tools in Claude Code

### 🚀 Passive Mode (MCP Server without API)
- **For users with**: Claude Code subscription (no API key)
- **Requires**: No API key needed!
- **How it works**: Claude Code performs analysis, MCP server manages graph
- **Best for**: Interactive analysis, using existing Claude Code subscription
- **Interface**: MCP Tools in Claude Code

### ⭐ SDK Agent Mode (NEW!)
- **For users with**: Claude Code subscription (no API key)
- **Requires**: `pip install claude-agent-sdk>=0.1.0`
- **How it works**: Bidirectional dialogue with autonomous agent
- **Best for**: Interactive, conversational analysis with agent autonomy
- **Interface**: Direct dialogue with SpringMVCAnalyzerAgent

**Mode Comparison:**

| Feature | API Mode | Passive Mode | SDK Agent Mode |
|---------|----------|--------------|----------------|
| **API Key Required** | ✅ Yes | ❌ No | ❌ No |
| **Subscription** | Anthropic API | Claude Code | Claude Code |
| **Interface** | MCP Tools | MCP Tools | Direct Dialogue |
| **Analysis** | Autonomous | Manual | Autonomous + Interactive |
| **Hooks Support** | ❌ | ❌ | ✅ Full |
| **Cost** | ~$4.23/project | $0 | $0 |

**Choose your mode:**
- API subscription + Batch processing → API Mode (this guide)
- Claude Code subscription + Exploration → Passive Mode ([Guide](./PASSIVE_MODE_GUIDE.md))
- Claude Code subscription + Interactive analysis → SDK Agent Mode ([Guide](./SDK_AGENT_GUIDE.md))

---

## Quick Start (API Mode)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Claude Code

Add the following to your Claude Code MCP settings (`.claude/mcp_settings.json` or via Settings UI):

```json
{
  "mcpServers": {
    "springmvc-analyzer": {
      "command": "python",
      "args": ["/path/to/springmvc-agent-analyzer/run_mcp_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 3. Restart Claude Code

The MCP server will be available after restarting Claude Code.

## Available Tools

### `analyze_file`

Analyze a single file with the appropriate agent.

**Parameters:**
- `file_path` (required): Path to the file to analyze
- `agent_type` (optional): Agent type (`controller`, `jsp`, `service`, `mapper`, `procedure`, or `auto`)

**Example:**
```
Use the analyze_file tool to analyze src/main/java/com/example/UserController.java
```

### `analyze_directory`

Analyze all files in a directory and build the knowledge graph.

**Parameters:**
- `directory_path` (required): Path to directory
- `pattern` (optional): File pattern (default: `**/*.java`)

**Example:**
```
Use analyze_directory to analyze all Java files in src/main/java/
```

### `query_graph`

Query the knowledge graph.

**Parameters:**
- `query_type` (required): Type of query (`stats`, `find_node`, `neighbors`, `paths`)
- `node_id` (optional): Node ID for node-specific queries
- `target_id` (optional): Target node ID for path queries

**Examples:**
```
Use query_graph with query_type="stats" to see graph statistics

Use query_graph with query_type="neighbors" and node_id="com.example.UserController"
to find neighbors of UserController
```

### `find_dependencies`

Find all dependencies of a node (transitive closure).

**Parameters:**
- `node_id` (required): Node ID to analyze
- `max_depth` (optional): Maximum traversal depth

**Example:**
```
Use find_dependencies for node_id="com.example.UserService" to find all its dependencies
```

### `analyze_impact`

Analyze the impact of changing a node.

**Parameters:**
- `node_id` (required): Node ID to analyze
- `max_depth` (optional): Maximum traversal depth

**Example:**
```
Use analyze_impact for node_id="com.example.UserService" to see what would be affected
if we change this service
```

### `export_graph`

Export the knowledge graph to a visualization format.

**Parameters:**
- `output_path` (required): Path to output file
- `format` (required): Format (`graphml`, `gexf`, `json`, `dot`, `d3`, `cytoscape`)

**Example:**
```
Use export_graph to save the graph to output/graph.json in d3 format
```

## Available Resources

### `analysis://results`

Access all file analysis results as JSON.

**Example:**
```
Read the analysis://results resource to see all analysis results
```

### `graph://stats`

Access knowledge graph statistics and metrics.

**Example:**
```
Read the graph://stats resource to see graph statistics
```

## Usage Examples

### Example 1: Analyze a Controller

```
Please analyze the file src/main/java/com/example/controllers/UserController.java
and show me:
1. What services it depends on
2. What JSP views it renders
3. What endpoints it exposes
```

Claude Code will use:
1. `analyze_file` to analyze the controller
2. `query_graph` to get dependencies and relationships

### Example 2: Impact Analysis

```
If I modify UserService.java, what other components will be affected?
```

Claude Code will use:
1. `analyze_impact` with node_id for UserService
2. Return all directly and transitively affected components

### Example 3: Generate Visualization

```
Create a D3.js visualization of the entire application architecture
```

Claude Code will use:
1. `analyze_directory` to analyze all files
2. `export_graph` with format="d3" to generate visualization JSON
3. Optionally generate HTML viewer

## Logging

Server logs are written to:
- `stderr` (for Claude Code console)
- `mcp_server.log` (file in project root)

Set `PYTHONUNBUFFERED=1` for real-time log output.

## Troubleshooting

### Server won't start

1. Check that all dependencies are installed: `pip install -r requirements.txt`
2. Check that `ANTHROPIC_API_KEY` is set
3. Check logs in `mcp_server.log`

### Analysis fails

1. Ensure files are valid Java/JSP/SQL/XML
2. Check that prompt templates exist in `prompts/base/`
3. Verify API key has sufficient credits
4. Check cache in `.cache/` for stale results

### Graph queries return empty

1. Run `analyze_directory` first to build the graph
2. Check node IDs are correct (use `query_graph` with `query_type="stats"`)
3. Verify relationships were extracted (check graph stats)

## Performance Tips

1. **Use cache**: Analysis results are cached by file content hash
2. **Batch operations**: Use `analyze_directory` instead of multiple `analyze_file` calls
3. **Limit graph depth**: Use `max_depth` parameter for large graphs
4. **Export for visualization**: Use `export_graph` instead of querying individual nodes

## Security Considerations

1. **API Key**: Store `ANTHROPIC_API_KEY` securely (use environment variables, not config files)
2. **Path Traversal**: Server validates paths to prevent directory traversal attacks
3. **Input Validation**: All inputs are validated before processing
4. **File Access**: Server only accesses files within the configured project directory

## Advanced Configuration

Create a custom config file `config/mcp_config.yaml`:

```yaml
models:
  # Model selection for different complexity levels
  haiku: "claude-3-5-haiku-20241022"
  sonnet: "claude-3-5-sonnet-20241022"
  opus: "claude-opus-4-20250514"

agents:
  # Minimum confidence threshold
  min_confidence: 0.7

  # Structure validation penalty
  structure_validation_penalty: 0.6

cache:
  # Cache directory
  cache_dir: ".cache"

  # Max cache size in MB
  max_size_mb: 1000

  # Cache TTL in seconds (24 hours)
  ttl_seconds: 86400
```

Pass custom config to server:

```python
server = SpringMVCAnalyzerServer(config_path="config/mcp_config.yaml")
```

## API Reference

For detailed API documentation, see:
- [MCP Protocol Specification](https://modelcontextprotocol.io/docs)
- [Agent Documentation](./AGENTS.md)
- [Graph Schema](./GRAPH_SCHEMA.md)
