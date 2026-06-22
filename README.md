# AgentPipe

AgentPipe is a conversational data pipeline agent that lets users query, monitor and trigger data pipeline workflows using natural language.

## Overview
AgentPipe is an AI-powered data pipeline assistant that enables users to monitor, query and trigger data pipelines using natural language. It combines an LLM-powered conversational agent with REST APIs and the Model Context Protocol (MCP), allowing the same pipeline tools to be accessed from a command-line interface, FastAPI service or MCP-compatible clients.

The project demonstrates conversational AI, data engineering workflows, API development, containerization and automated testing within a production-inspired architecture.

## Key Features

### Conversational Pipeline Operations

- Query pipeline status using natural language
- Investigate failed runs
- Retrieve data quality reports
- Trigger pipeline executions
- Multi-turn conversations with session management

### REST API

- Six production-style endpoints
- Async PostgreSQL access
- Structured JSON logging
- Request validation with Pydantic
- Rate limiting

### MCP Integration

- Exposes the same pipeline tools through MCP
- Compatible with Claude Code
- Reuses the same business logic as the CLI and REST API

### Containerized Deployment

- Docker Compose stack
- Automatic schema initialization
- Automatic sample data generation
- Shared PostgreSQL instance

### Testing

- Unit tests
- Integration tests
- End-to-end workflow tests

## Project Structure
```text
agentpipe/ 
│ 
├── agent/ 
│   ├── agent.py 
│   ├── tool_definitions.py 
│   └── tools.py 
│ 
├── backend/ 
│   ├── db/ 
│        ├─── db.py
│        └─── async_db.py
│   └── simulator/ 
│        └─── pipeline_generator.py  
│ 
├── api/
│ ├── app.py
│ ├── main.py
│ ├── logger.py
│ └── models.py
│
├── database/ 
│   └── schema.sql 
│
├── tests/  
│   ├── test_tools_unit.py 
│   ├── test_api_integration.py 
│   └── test_e2e.py
│
├── Dockerfile
├── docker-compose.yml
├── docker-compose.yml 
├── cli.py
├── requirements.txt 
├── README.md 
└── .env
```