# AgentPipe

AgentPipe is a conversational data pipeline agent that lets users query, monitor and trigger data pipeline workflows using natural language.

## Phase 1 

- Define pipeline tracking schema
- Set up PostgreSQL development environment
- Build initial database connection utilities
- Prepare project for future LLM-based pipeline control features

## Phase 2: Conversational Agent

- Database query tools
- Claude tool definitions
- Multi-turn tool calling workflow
- Tool dispatch framework
- Interactive CLI interface
- Conversation history management

## Phase 3: REST API & Platform Services

- FastAPI application layer
- Async PostgreSQL database access
- Pipeline monitoring endpoints
- Data quality monitoring endpoints
- Pipeline trigger API
- Conversational agent API endpoint
- Structured request logging
- Request rate limiting
- Standardized API response models

## Phase 4: MCP Integration & Deployment

- Model Context Protocol (MCP) server
- Dockerized application deployment
- Multi-service Docker Compose stack
- Automatic database seeding
- Unit, integration, and end-to-end testing
- Deployment and developer documentation

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