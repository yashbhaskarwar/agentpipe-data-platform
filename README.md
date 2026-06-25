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

## System Architechture
```text
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                         │
│                                                                 │
│   CLI (cli.py)          REST API (:8000)    MCP Clients        │
│   python cli.py         FastAPI/uvicorn     Claude Code/Cursor  │
└────────┬────────────────────────┬──────────────────┬───────────┘
         │                        │                  │
         v                        v                  v
┌────────────────┐    ┌───────────────────┐  ┌──────────────────┐
│  agent/        │    │  api/             │  │  mcp_server.py   │
│  agent.py      │<───│  app.py           │  │                  │
│                │    │                   │  │  Exposes same 5  │
│  Claude API    │    │  6 endpoints      │  │  tools over      │
│  tool-calling  │    │  Rate limiting    │  │  stdio/MCP       │
│  loop          │    │  JSON logging     │  │  protocol        │
└────────┬───────┘    └────────┬──────────┘  └───────┬──────────┘
         │                     │                      │
         v                     v                      v
┌─────────────────────────────────────────────────────────────────┐
│                       agent/tools.py                            │
│   get_pipeline_status  │  get_failed_runs  │  get_run_summary  │
│   get_data_quality_issues  │  trigger_pipeline_run             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              v                                 v
   ┌──────────────────┐              ┌──────────────────────┐
   │ backend/db/db.py │              │backend/db/async_db.py│
   │  psycopg2 (sync) │              │  asyncpg (async)     │
   │  CLI + tools     │              │  FastAPI layer only  │
   └────────┬─────────┘              └──────────┬───────────┘
            │                                   │
            └──────────────┬────────────────────┘
                           v
              ┌────────────────────────┐
              │     PostgreSQL         │
              │                        │
              │  pipeline_runs         │
              │  pipeline_tasks        │
              │  data_quality_checks   │
              └────────────────────────┘
```

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

## How to Run

1. Configure environment variables
Update .env with:
Anthropic API key
PostgreSQL credentials

2. Start the application
docker compose up -d

Thiswill start:
PostgreSQL
FastAPI service
MCP server

The database schema is initialized automatically and sample pipeline data is seeded during the first startup.

3. Verify the deployment
curl http://localhost:8000/health
Interactive API documentation is available at:
http://localhost:8000/docs

## Technology Stack

AI | Claude API 
API | FastAPI 
Database | PostgreSQL 
Async DB | asyncpg 
Sync DB | psycopg2 
MCP | Python MCP SDK 
Containerization | Docker 
Testing | pytest 
Configuration | python-dotenv 

## Design Highlights

- Separate synchronous and asynchronous database layers
- Thread pool execution for blocking LLM operations
- Stateless REST API with session-based conversations
- Containerized deployment with automatic database seeding

## Notes
- The same tool layer is shared across the CLI, REST API and MCP server, avoiding duplicate business logic.
- FastAPI uses asynchronous database access (asyncpg), while the conversational agent uses synchronous PostgreSQL access (psycopg2) to match the Claude tool-calling workflow.
- This project is intended as a production-inspired portfolio demonstrating conversational AI, data engineering, API design, containerization and software testing.