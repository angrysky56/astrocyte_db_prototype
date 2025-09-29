# Astrocyte DB MCP Tools - Usage Guide

## Overview

This MCP server provides tools for interacting with the Astrocyte Database prototype, enabling testing, querying, and monitoring through a standardized interface.

## Available Tools

### 1. query_mono_events

Query mono-originated events (simple, single-source events) from the database.

**Use cases:**
- Finding events from a specific source stream
- Analyzing event patterns within a time range
- Debugging event production issues
- Testing event archival from Redis to PostgreSQL

**Parameters:**
- `limit`: Maximum number of events to return (default: 10)
- `offset`: Number of events to skip for pagination (default: 0)
- `start_time`: ISO format timestamp to filter events after this time
- `end_time`: ISO format timestamp to filter events before this time
- `source_stream`: Filter by specific source stream name (e.g., "stream:axon_1")
- `event_type`: Filter by event type

**Example usage:**
```
Query the last 20 events from stream:axon_1
```

### 2. query_multi_events

Query multi-originated integrated events (complex events created by correlating multiple mono events).

**Use cases:**
- Analyzing event correlation patterns
- Testing Complex Event Processing (CEP) logic
- Evaluating correlation rule effectiveness
- Debugging integration issues

**Parameters:**
- `limit`: Maximum number of events to return (default: 10)
- `offset`: Number of events to skip for pagination
- `start_time`: ISO format timestamp to filter events after this time
- `end_time`: ISO format timestamp to filter events before this time
- `correlation_rule`: Filter by specific correlation rule name
- `min_confidence`: Minimum confidence score (0.0-1.0)

**Example usage:**
```
Show me high-confidence multi events with confidence > 0.8
```

### 3. get_event_statistics

Get aggregate statistics about events in the system.

**Use cases:**
- Monitoring system health and activity
- Tracking event production rates
- Validating archival processes
- Performance analysis

**Returns:**
- Total event counts (mono and multi)
- System status
- Timestamp of query

**Example usage:**
```
What's the current event count in the database?
```

### 4. check_system_health

Check the health status of all system components.

**Use cases:**
- Pre-deployment validation
- Troubleshooting connection issues
- Monitoring component availability
- Debugging infrastructure problems

**Parameters:**
- `full`: If True, performs comprehensive health check including Redis, PostgreSQL, and API status

**Returns:**
- Status of each component (API, Redis, Database)
- Overall system status
- Detailed component information

**Example usage:**
```
Check if all Astrocyte DB services are running
```

### 5. manage_docker_services

Manage Docker Compose services for the Astrocyte DB infrastructure.

**Use cases:**
- Starting/stopping database services
- Restarting services after configuration changes
- Checking service status
- Viewing service logs for debugging

**Parameters:**
- `action`: Action to perform (up, down, restart, ps, logs)
- `service`: Optional specific service name (redis, postgres)

**Example usage:**
```
Start the Docker services for Astrocyte DB
```

```
Show me the logs from the PostgreSQL service
```

### 6. get_specific_event

Retrieve a specific event by its UUID.

**Use cases:**
- Debugging specific event processing issues
- Analyzing event details
- Verifying event archival
- Testing event retrieval performance

**Parameters:**
- `event_id`: The UUID of the event to retrieve
- `event_type`: Type of event ('mono' or 'multi', default: 'mono')

**Example usage:**
```
Get details for mono event with ID abc123-def456-...
```

## Resources

### astrocyte://health

Provides current system health status as a readable text resource.

**Use cases:**
- Quick status checks
- Including health status in reports
- Monitoring dashboards

### astrocyte://stats

Provides current event statistics as a readable text resource.

**Use cases:**
- Quick statistics overview
- Performance monitoring
- Including stats in reports

## Prompts

### test_database_prompt

Generate a comprehensive testing workflow for the Astrocyte DB.

**Parameters:**
- `query_description`: Description of what to test

**Example usage:**
```
Use the test_database_prompt to test event archival from Redis to PostgreSQL
```

### analyze_correlations_prompt

Generate a workflow for analyzing event correlations.

**Parameters:**
- `time_range`: Time range to analyze (e.g., "last hour", "today")

**Example usage:**
```
Use the analyze_correlations_prompt to analyze correlations from the last hour
```

## Best Practices

### Testing Workflow

1. **Always start with health check:**
   ```
   Check system health before running tests
   ```

2. **Verify statistics:**
   ```
   Get event statistics to understand current state
   ```

3. **Query with filters:**
   ```
   Query mono events from the last hour with limit 20
   ```

4. **Analyze correlations:**
   ```
   Query multi events with min_confidence 0.7
   ```

### Debugging Workflow

1. **Check service status:**
   ```
   Check Docker service status
   ```

2. **View logs if issues found:**
   ```
   Show logs from the postgres service
   ```

3. **Restart problematic services:**
   ```
   Restart the redis service
   ```

4. **Verify recovery:**
   ```
   Check system health after restart
   ```

### Performance Testing

1. **Generate baseline statistics:**
   ```
   Get current event statistics
   ```

2. **Run load test (external tool)**

3. **Compare post-test statistics:**
   ```
   Get event statistics again
   ```

4. **Analyze event patterns:**
   ```
   Query events from the test time range
   ```

## Error Handling

All tools return JSON responses with error information when issues occur:

```json
{
  "error": "Description of the error",
  "type": "error_category"
}
```

Common error types:
- `http_error`: API communication issues
- `timeout`: Service unavailable or slow response
- `unexpected_error`: General errors requiring investigation

## Tips

1. **Use time filters effectively:** When querying events, use `start_time` and `end_time` to narrow results
2. **Pagination for large datasets:** Use `offset` and `limit` for manageable result sets
3. **Monitor confidence scores:** For multi events, use `min_confidence` to filter high-quality correlations
4. **Check health regularly:** Use `check_system_health()` before critical operations
5. **Leverage resources:** Use `astrocyte://health` and `astrocyte://stats` for quick status checks
