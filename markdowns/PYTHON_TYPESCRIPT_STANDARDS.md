# Python + TypeScript Backend Coding Standards

> **Note**: These standards complement the project's [Global Development Rules](./GLOBAL_RULES.md). Please review them for additional guidelines on code modifications, version control, and other development practices.

## Table of Contents
1. [General Guidelines](#general-guidelines)
2. [TypeScript Usage](#typescript-usage)
3. [Python Standards](#python-standards)
4. [API Design](#api-design)
5. [Error Handling](#error-handling)
6. [Testing](#testing)
7. [Performance](#performance)
8. [Security](#security)

## General Guidelines
- Follow the Single Responsibility Principle
- Write clean, self-documenting code
- Use meaningful variable and function names
- Keep functions small and focused
- Follow the DRY (Don't Repeat Yourself) principle
- Use linters and formatters (ESLint, Prettier, Black, isort)
- Write comprehensive docstrings and comments
- Follow the [Code Modifications](./GLOBAL_RULES.md#code-modifications) guidelines in GLOBAL_RULES.md

## Commandline Usage
- Use `pip` for package management
- Use `venv` for virtual environments
- Use `git` for version control
- Use `pytest` for testing
- Run one command at a time
- Always update the requirements.txt file after adding a new package
- Use `pip freeze > requirements.txt` to update the requirements.txt file
- Use `pip install -r requirements.txt` to install the required packages
- Use `pip install --upgrade pip` to upgrade pip
- Use `pip install --upgrade setuptools` to upgrade setuptools
- Use `pip install --upgrade wheel` to upgrade wheel
- Use `pip install --upgrade --force-reinstall -r requirements.txt` to upgrade all packages

## TypeScript Usage
- Enable `strict` mode in `tsconfig.json`
- Use interfaces for request/response types
- Prefer `type` for complex type definitions
- Use TypeScript utility types
- Avoid using `any` type
- Use `readonly` for immutable data
- Use enums or const assertions for fixed sets of values

## Python Standards
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Use highest minor version of Python 3.11 if there is need for pydantic package in other situations use Python 3.12
- Use Python 3.12+ features (pattern matching, type union operator, etc.)
- Use dataclasses or Pydantic models for data structures
- Use pathlib for file system operations
- Use environment variables for configuration
- Use `logging` instead of print statements

## Code Organization
```
project/
  src/
    api/
      controllers/
      middlewares/
      routes/
      validators/
    core/
      config/
      database/
      errors/
      services/
    models/
      schemas/
      repositories/
    utils/
      helpers.py
      logger.py
  tests/
    unit/
    integration/
    fixtures/
  .env.example
  main.py
  requirements.txt
```

## API Design

Follow the [Global API Design Guidelines](./GLOBAL_RULES.md#api-design) for comprehensive API standards. Additional Python/TypeScript specific guidelines:

## Error Handling
- Use custom error classes
- Log all errors with appropriate context
- Return user-friendly error messages
- Handle edge cases and invalid inputs
- Use proper HTTP status codes
- Implement global error handling middleware

## Testing
- Write unit tests for business logic
- Write integration tests for API endpoints
- Use fixtures for test data
- Mock external dependencies
- Aim for at least 80% test coverage
- Run tests in CI/CD pipeline

## Performance
- Use async/await for I/O operations
- Implement caching where appropriate
- Optimize database queries
- Use connection pooling
- Implement rate limiting
- Monitor application performance

## Security
- Validate all user input
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Use HTTPS in production
- Set secure HTTP headers
- Implement CORS properly
- Keep dependencies up to date
- Store secrets securely (use environment variables)

## Logging
- Use structured logging
- Include request IDs for tracing
- Log important events and errors
- Don't log sensitive information
- Configure appropriate log levels
- Rotate log files

## Documentation
- Write API documentation with OpenAPI/Swagger
- Document environment variables
- Include setup instructions in README.md
- Document API endpoints with examples
- Keep documentation up to date

## Version Control
- Write meaningful commit messages
- Use feature branches
- Create pull requests for code review
- Squash and merge pull requests
- Follow semantic versioning
- Keep the main branch stable
- Use git tags for releases
