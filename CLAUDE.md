# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a learning project for building an **Async AI Task Runner** - a containerized, asynchronous AI task processing platform. The project follows a structured 5-day curriculum to build from basic FastAPI to a complete system with Celery, Redis, PostgreSQL, Docker, and MCP server integration.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment (if using uv, it's already managed)
source .venv/bin/activate

# Install dependencies (usually handled by uv)
pip install -e .
```

### Running the Application
```bash
# Start FastAPI server (once implemented)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative using python module
python -m uvicorn app.main:app --reload
```

### Database Operations
```bash
# Initialize Alembic (Day 2)
alembic init alembic

# Create migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Start PostgreSQL locally (Day 2)
# Ensure PostgreSQL is running and accessible
```

### Testing
```bash
# Run tests (to be implemented on Day 5)
pytest

# Run specific test
pytest tests/test_api.py
```

### Docker Operations (Day 3)
```bash
# Build and start all services
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f web
```

## Project Architecture

### Core Structure
- **`app/`**: Main FastAPI application package
  - **`main.py`**: FastAPI app, routes, and dependency injection (Day 1)
  - **`models.py`**: SQLAlchemy ORM models for database tables (Day 1)
  - **`schemas.py`**: Pydantic models for request/response validation (Day 1)
  - **`database.py`**: Database connection and session management (Day 1)

### Planned Architecture (5-Day Progression)

**Day 1**: Basic API + Database
- FastAPI with `/health` and `/tasks` endpoints
- PostgreSQL integration with SQLAlchemy
- Pydantic validation
- Alembic for database migrations

**Day 2**: Async Processing
- Celery workers for background task processing
- Redis as message broker
- Async/sync integration patterns
- Task status tracking (PENDING → COMPLETED)

**Day 3**: Containerization
- Docker configuration for all services
- Environment variable management with `.env`
- Docker Compose for multi-service orchestration
- Security best practices for API keys

**Day 4**: MCP Integration
- Model Context Protocol server implementation
- AI client integration (Claude Desktop)
- Tool exposure for external AI systems
- Resource and prompt management

**Day 5**: Testing & Polish
- Integration testing with pytest
- API documentation (Swagger UI)
- Logic migration from CLI tools
- Production-ready features

### Data Models (Planned)
```python
# Task model will track AI processing jobs
class Task:
    id: Primary key
    prompt: User input prompt
    model: AI model to use (e.g., "gpt-4")
    status: PENDING, PROCESSING, COMPLETED, FAILED
    result: AI response output
    created_at: Timestamp
    updated_at: Timestamp
```

## Development Guidelines

### Environment Variables (Day 3)
All sensitive configuration should use environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key (or other AI providers)

### Async Patterns
- FastAPI routes should be `async def`
- Database operations use SQLAlchemy async sessions
- Celery tasks are synchronous but interact with async FastAPI

### Code Organization
- Follow FastAPI best practices for dependency injection
- Keep Pydantic schemas separate from SQLAlchemy models
- Use Alembic for all database schema changes

### Security Considerations
- Never commit API keys or sensitive data
- Use environment variables for all configuration
- Validate all inputs with Pydantic models

## Technology Stack

- **API Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL with SQLAlchemy async ORM
- **Task Queue**: Celery with Redis broker
- **Containerization**: Docker + Docker Compose
- **Validation**: Pydantic for data validation
- **Migrations**: Alembic for database versioning
- **AI Integration**: OpenAI API (extensible to other providers)
- **Protocol**: Model Context Protocol (MCP) for AI client integration

## Learning Progression

This repository is designed as a structured learning experience. Each day builds upon previous concepts:

1. **Foundation**: FastAPI + Database basics
2. **Async**: Message queues and background processing
3. **Production**: Containerization and configuration
4. **Integration**: AI protocol implementation
5. **Completion**: Testing and production readiness

The project intentionally starts simple and progressively introduces more complex patterns, making it ideal for learning modern Python web development with AI integration.