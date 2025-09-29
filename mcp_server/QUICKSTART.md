# Astrocyte DB MCP Server - Quick Start

## 🎯 Overview

The MCP server has been successfully created and integrated with the Astrocyte DB prototype. It provides standardized tools for testing, querying, and monitoring the database through Claude Desktop.

## 📁 What Was Created

```
astrocyte_db_prototype/
├── mcp_server/
│   ├── __init__.py              # Package initialization
│   ├── server.py                # Main MCP server (470 lines)
│   ├── README.md                # Comprehensive documentation
│   └── ai_guidance/
│       └── tool_usage_guide.md  # Tool usage guide for Claude
├── example_mcp_config.json      # Claude Desktop configuration
└── pyproject.toml               # Updated with MCP dependencies
```

## 🚀 Installation Steps

### 1. Install Dependencies

```bash
cd /home/ty/Repositories/ai_workspace/astrocyte_db_prototype
source .venv/bin/activate
uv pip install -e .
```

This will install:
- `mcp[cli]>=1.2.0` - Model Context Protocol SDK
- `httpx==0.28.1` - Async HTTP client (moved from dev dependencies)

### 2. Configure Claude Desktop

Add this to your Claude Desktop config (`~/.config/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "astrocyte-db": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/ty/Repositories/ai_workspace/astrocyte_db_prototype",
        "run",
        "python",
        "mcp_server/server.py"
      ],
      "env": {
        "PYTHONPATH": "/home/ty/Repositories/ai_workspace/astrocyte_db_prototype"
      }
    }
  }
}
```

**Note**: The path `/home/ty/Repositories/ai_workspace/astrocyte_db_prototype` is hardcoded in the example. When you add this to your config, it will work for your system.

### 3. Restart Claude Desktop

After adding the configuration, restart Claude Desktop to load the MCP server.

## ✅ Testing the Installation

### Start the Infrastructure

```bash
# Terminal 1: Start Docker services
cd /home/ty/Repositories/ai_workspace/astrocyte_db_prototype
docker-compose up -d

# Verify services are running
docker-compose ps
```

### Start the API Server

```bash
# Terminal 2: Start FastAPI server
cd /home/ty/Repositories/ai_workspace/astrocyte_db_prototype
source .venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Generate Test Data (Optional)

```bash
# Terminal 3: Run demo workflow to generate events
cd /home/ty/Repositories/ai_workspace/astrocyte_db_prototype
source .venv/bin/activate
python examples/demo_workflow.py
```

### Test in Claude Desktop

Once Claude Desktop is restarted, try these prompts:

1. **Basic health check:**
   ```
   Check Astrocyte DB system health
   ```

2. **Get statistics:**
   ```
   What are the current event statistics in the Astrocyte DB?
   ```

3. **Query events:**
   ```
   Show me the last 10 mono events from the Astrocyte DB
   ```

4. **Check Docker services:**
   ```
   Check the status of Astrocyte DB Docker services
   ```

## 🛠 Available Tools

The MCP server provides these tools:

### Event Queries
- `query_mono_events` - Query mono-originated events
- `query_multi_events` - Query multi-originated integrated events
- `get_specific_event` - Get a specific event by UUID

### System Monitoring
- `check_system_health` - Check health of all components
- `get_event_statistics` - Get aggregate event statistics

### Service Management
- `manage_docker_services` - Control Docker Compose services

### Resources
- `astrocyte://health` - Current system health status
- `astrocyte://stats` - Current event statistics

### Prompts
- `test_database_prompt` - Generate testing workflows
- `analyze_correlations_prompt` - Generate correlation analysis workflows

## 📚 Documentation

- **MCP Server README**: `mcp_server/README.md`
- **Tool Usage Guide**: `mcp_server/ai_guidance/tool_usage_guide.md`
- **Astrocyte DB Status**: `STATUS.md`
- **Astrocyte DB README**: `README.md`

## 🔧 Troubleshooting

### MCP Server Not Appearing

1. Check Claude Desktop config path:
   ```bash
   cat ~/.config/Claude/claude_desktop_config.json
   ```

2. Verify JSON syntax is valid

3. Check Claude Desktop logs (if available)

### Connection Errors

1. Verify API is running:
   ```bash
   curl http://localhost:8000/health/
   ```

2. Check Docker services:
   ```bash
   docker-compose ps
   ```

3. View server logs:
   ```bash
   docker-compose logs redis postgres
   ```

### Import Errors

If you get import errors, ensure dependencies are installed:
```bash
source .venv/bin/activate
uv pip install -e .
```

## 🎯 Next Steps

1. **Test the MCP server** with Claude Desktop
2. **Generate test data** using `examples/demo_workflow.py`
3. **Query events** to verify archival from Redis to PostgreSQL
4. **Analyze correlations** using the multi-event queries
5. **Monitor system health** during load testing

## 💡 Tips

- Use the AI guidance documentation for comprehensive tool usage examples
- Check system health before running tests
- Use time filters when querying events to narrow results
- Leverage the prompts for guided workflows
- The MCP server automatically handles errors and returns structured JSON responses

## 🔗 Related Files

- Main server implementation: `mcp_server/server.py`
- Claude Desktop config example: `example_mcp_config.json`
- Tool usage guide: `mcp_server/ai_guidance/tool_usage_guide.md`
- Project dependencies: `pyproject.toml`

---

**The MCP server is ready to use!** Start the infrastructure, add the config to Claude Desktop, and begin testing the Astrocyte DB through the standardized MCP interface.
