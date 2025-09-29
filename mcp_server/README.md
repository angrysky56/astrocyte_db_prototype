# Astrocyte DB MCP Server

A Model Context Protocol (MCP) server for the Astrocyte Database prototype, providing standardized tools for testing, querying, and monitoring the database system through Claude Desktop or other MCP-compatible clients.

## Features

- **Event Querying**: Query both mono-originated and multi-originated integrated events
- **System Monitoring**: Check health status and retrieve statistics
- **Service Management**: Control Docker Compose services
- **Real-time Resources**: Access system health and statistics as MCP resources
- **Guided Workflows**: Pre-built prompts for testing and analysis

## Prerequisites

- Python 3.12+
- Astrocyte DB infrastructure running (Docker Compose)
- Astrocyte DB API server running on `http://localhost:8000`

## Installation

The MCP server dependencies are included in the main Astrocyte DB project. Ensure you have:

```bash
cd /home/ty/Repositories/ai_workspace/astrocyte_db_prototype

# Create and activate virtual environment
uv venv --python 3.12 --seed
source .venv/bin/activate

# Install dependencies (includes httpx for the MCP server)
uv pip install -e .
```

## Configuration

### Claude Desktop Integration

1. Copy the example configuration:
   ```bash
   cat example_mcp_config.json
   ```

2. Add to your Claude Desktop configuration file:
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

3. Update the `--directory` path in the config to match your installation path

4. Restart Claude Desktop

### Verify Installation

After restarting Claude Desktop, you should see the Astrocyte DB MCP server in the available tools. Test with:

```
Check Astrocyte DB system health
```

## Available Tools

### Event Queries

- **query_mono_events**: Query mono-originated events with filtering
- **query_multi_events**: Query multi-originated integrated events
- **get_specific_event**: Retrieve a specific event by UUID

### System Monitoring

- **check_system_health**: Check health of all components
- **get_event_statistics**: Get aggregate event statistics

### Service Management

- **manage_docker_services**: Control Docker Compose services

## Resources

- **astrocyte://health**: Current system health status
- **astrocyte://stats**: Current event statistics

## Prompts

- **test_database_prompt**: Generate testing workflows
- **analyze_correlations_prompt**: Generate correlation analysis workflows

## Usage Examples

### Basic Testing Workflow

```
1. Check system health
2. Get current event statistics
3. Query the last 20 mono events
4. Query multi events with confidence > 0.8
```

### Debugging Workflow

```
1. Check Docker service status
2. If issues found, show logs from the problematic service
3. Restart the service
4. Verify recovery with health check
```

### Analysis Workflow

```
Use the analyze_correlations_prompt to analyze correlations from the last hour
```

## Architecture

The MCP server acts as a bridge between Claude Desktop and the Astrocyte DB API:

```
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│    Claude    │◄──MCP─►│  MCP Server  │◄──HTTP─►│  Astrocyte   │
│   Desktop    │        │              │        │   DB API     │
└──────────────┘        └──────────────┘        └──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   Docker     │
                        │  (Redis +    │
                        │  PostgreSQL) │
                        └──────────────┘
```

## Development

### Running Standalone

For development and testing, you can run the MCP server directly:

```bash
cd /home/ty/Repositories/ai_workspace/astrocyte_db_prototype
source .venv/bin/activate
python mcp_server/server.py
```

### Logging

The MCP server logs to stderr as required by the MCP specification. Logs include:
- Tool invocations
- API communication status
- Error details
- System events

### Error Handling

All tools return JSON responses with structured error information:

```json
{
  "error": "Error description",
  "type": "error_category"
}
```

Error types:
- `http_error`: API communication issues
- `timeout`: Service timeout
- `unexpected_error`: General errors

## Troubleshooting

### MCP Server Not Appearing in Claude Desktop

1. Check Claude Desktop configuration file path
2. Verify JSON syntax is valid
3. Ensure the directory path is absolute and correct
4. Restart Claude Desktop after configuration changes

### Connection Errors

1. Verify Astrocyte DB API is running:
   ```bash
   curl http://localhost:8000/health/
   ```

2. Check Docker services:
   ```bash
   docker-compose ps
   ```

3. Start services if needed:
   ```bash
   docker-compose up -d
   ```

### No Events Returned

1. Verify events exist:
   ```bash
   curl http://localhost:8000/events/stats
   ```

2. Run the demo workflow to generate test data:
   ```bash
   python examples/demo_workflow.py
   ```

## AI Guidance

The MCP server includes AI guidance documentation in the `ai_guidance/` directory:

- `tool_usage_guide.md`: Comprehensive guide for using all tools effectively

## Contributing

When adding new tools or features:

1. Add proper type hints and docstrings
2. Include error handling with structured responses
3. Log important events to stderr
4. Update the AI guidance documentation
5. Test with Claude Desktop

## License

Part of the Astrocyte DB prototype project.

## Related Documentation

- [Astrocyte DB STATUS.md](../STATUS.md): Complete system status and capabilities
- [Astrocyte DB README.md](../README.md): Full project documentation
- [MCP Specification](https://modelcontextprotocol.io): Model Context Protocol details
