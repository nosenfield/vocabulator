# Source Code (`src/`)

This directory contains the main source code for the Vocabulator MVP.

## Directory Structure

- **`api/`** - FastAPI application and REST API endpoints
- **`processing/`** - Text processing pipeline and batch processing logic
- **`ai/`** - OpenAI integration and AI/ML layer
- **`data/`** - Data access layer (DynamoDB, S3 clients, repositories)
- **`vocabulary/`** - Vocabulary domain logic and Common Core corpus
- **`utils/`** - Shared utilities (config, logging, validators)
- **`frontend/`** - Static HTML templates and report generation

## Architecture

See `_docs/architecture.md` for complete system architecture documentation.

## Development Guidelines

- Follow test-first development (TDD) workflow
- All modules must have type hints
- Use async/await for I/O operations
- See `_docs/best-practices/` for coding standards

