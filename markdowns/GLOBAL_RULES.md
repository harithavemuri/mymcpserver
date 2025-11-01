# Global Development Rules and Guidelines

## Table of Contents
1. [Code Modifications](#code-modifications)
2. [Version Control](#version-control)
3. [Documentation](#documentation)
4. [Code Quality](#code-quality)
5. [Security](#security)
6. [Performance](#performance)
7. [Error Handling](#error-handling)
8. [API Design](#api-design)
9. [Testing](#testing)
10. [Dependencies](#dependencies)

## Code Modifications
- **Never automatically overwrite** manually customized code without explicit confirmation
- Always **preserve existing functionality** when making changes
- When updating code, provide a **clear explanation** of changes
- Follow the **principle of least surprise** - changes should be predictable
- Document any breaking changes in the code and migration steps

## Version Control
- Write **clear, concise commit messages** in the present tense
- Follow the pattern: `type(scope): description` (e.g., `feat(auth): add login functionality`)
- Use **feature branches** for all new development
- Keep commits **small and focused** on a single concern
- **Rebase** feature branches before merging to main
- Use **meaningful branch names** (e.g., `feature/user-authentication`, `bugfix/login-validation`)

## Documentation
- Document all **public APIs** and **complex logic**
- Keep documentation **up-to-date** with code changes
- Use **JSDoc/TSDoc** for function and component documentation
- Include **usage examples** in documentation
- Document **environment variables** and configuration options
- Keep a **CHANGELOG.md** for tracking notable changes
- Keep the **README.md** updated with the latest changes and usage instructions

## Code Quality
- Follow the **SOLID principles**
- Keep functions/methods **small and focused** (ideally < 20 lines)
- Use **meaningful names** for variables, functions, and classes
- Follow the **DRY (Don't Repeat Yourself)** principle
- Apply the **KISS (Keep It Simple, Stupid)** principle
- Limit function parameters to **3 or fewer** when possible
- Avoid **deep nesting** of conditionals (prefer early returns)

## Security
- **Never hardcode** sensitive information (use environment variables)
- Validate and sanitize **all user inputs**
- Use **parameterized queries** to prevent SQL injection
- Implement proper **authentication and authorization**
- Follow the **principle of least privilege**
- Keep dependencies **updated** to avoid known vulnerabilities
- Use **HTTPS** for all network communications

## Performance
- Optimize **critical rendering paths**
- Implement **pagination** for large data sets
- Use **caching** appropriately
- Minimize **bundle size**
- Implement **lazy loading** for routes and heavy components
- Optimize **database queries**
- Use **efficient data structures** and algorithms

## Error Handling
- Handle **all possible error cases**
- Provide **meaningful error messages**
- Log errors with **sufficient context**
- Implement proper **error boundaries** in React
- Use **custom error types** for different error cases
- Fail **fast and loud** in development, gracefully in production

## API Design
- Follow **RESTful** principles
- Use **HTTP methods** appropriately (GET, POST, PUT, DELETE, PATCH)
- Version your API (e.g., `/api/v1/resource`)
- Use **kebab-case** for URLs (e.g., `/user-profiles`)
- Return **consistent response formats**
- Implement **rate limiting**
- Include **pagination** for collection endpoints
- Provide **meaningful status codes**
- Document your API using **OpenAPI/Swagger**
- Use OpenAPI 3.x for API documentation
- Ensure all endpoints include versioning in requests/responses
- Implement a healthcheck endpoint (e.g., `/healthcheck`)
- Use query parameters for filtering, sorting, and searching
- Document all endpoints with request/response examples

### Example API Response
```typescript
// Success Response
{
  "status": "success",
  "version": "1.0",
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  }
}

// Error Response
{
  "status": "error",
  "version":"1.0"
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address"
      }
    ]
  }
}
```

## Testing
- Write **unit tests** for business logic
- Write **integration tests** for critical paths
- Aim for **80%+ test coverage**
- Test **edge cases** and error conditions
- Mock **external dependencies**
- Run tests in **CI/CD pipeline**
- Keep tests **independent** and **deterministic**
- Use **pytest** for testing
- Use **coverage.py** to measure test coverage
- Use **pytest-cov** to measure test coverage
- Use **pytest-asyncio** for testing async code
- Use **pytest-mock** for mocking
- Write **unit tests** for business logic
- Write **integration tests** for critical paths
- Aim for **80%+ test coverage**
- Test **edge cases** and error conditions
- Mock **external dependencies**
- Run tests in **CI/CD pipeline**
- Keep tests **independent** and **deterministic**
- Write **unit tests** for any new functionality added automatically
- Write **integration tests** for any new functionality added automatically

## Dependencies
- Keep dependencies **to a minimum**
- Regularly **update** dependencies
- Document **why** each dependency is needed
- Be cautious with **native dependencies**
- Use **lock files** to ensure consistent installations
- Audit dependencies for **security vulnerabilities**
- Avoid **unnecessary dependencies**
- Avoid **circular dependencies**

## Code Review
- Review **all code** before merging to main
- Provide **constructive feedback**
- Keep PRs **small and focused**
- Address **all comments** before merging
- Use **automated tools** (linters, formatters, static analyzers)
- Verify that **tests pass** before merging

## Continuous Integration/Deployment
- Automate **builds and tests**
- Run **linters and formatters** in CI
- Deploy from **main branch only**
- Use **feature flags** for gradual rollouts
- Implement **blue/green deployments** or canary releases
- Monitor application **in production**

## Accessibility
- Follow **WCAG 2.1** guidelines
- Ensure **keyboard navigation** works
- Provide **text alternatives** for non-text content
- Ensure sufficient **color contrast**
- Make interactive elements **clearly identifiable**
- Test with **screen readers**

## Internationalization (i18n)
- Externalize **all user-facing strings**
- Support **right-to-left (RTL)** languages
- Handle **date, time, and number** formats
- Consider **plurals and gender** in translations
- Test with **different languages**

## Logging and Monitoring
- Log **meaningful information**
- Use **structured logging**
- Include **request IDs** for tracing
- Set up **alerts** for critical errors
- Monitor **application performance**
- Keep logs **secure** and **private**

## Development Workflow
- Use **lint-staged** for pre-commit hooks
- Automate **code formatting**
- Run tests **before pushing**
- Keep the **main branch stable**
- Use **meaningful PR descriptions**
- Link PRs to **related issues**

## Code Organization
- Group related files **by feature**
- Keep **test files** next to the code they test
- Separate **business logic** from UI
- Use **barrel files** for cleaner imports
- Follow a consistent **naming convention**
- Keep configuration **separate** from code


## Performance Budget
- Set **performance budgets** for:
  - Bundle size
  - Load time
  - Time to interactive
  - Memory usage
- Monitor and **enforce** these budgets
- Optimize for **slow networks** and **low-end devices**

## Security Headers
- Implement **Content Security Policy (CSP)**
- Use **HTTP Strict Transport Security (HSTS)**
- Set **X-Content-Type-Options: nosniff**
- Use **X-Frame-Options: DENY**
- Implement **X-XSS-Protection**
- Use **Referrer-Policy**
- Set **Feature-Policy** headers

## Environment Configuration
- Use **environment variables** for configuration
- Never commit **secrets** to version control
- Provide **example configuration** files
- Validate configuration **at startup**
- Document **all configuration options**

## Error Tracking
- Implement **client-side error tracking**
- Track **server-side errors**
- Set up **alerts** for critical errors
- Include **stack traces** and **context**
- Monitor **error rates** and trends

## Backup and Recovery
- Regular **database backups**
- Test **restore procedures**
- Document **disaster recovery** plans
- Implement **point-in-time recovery**
- Store backups **securely** and **offsite**

## Compliance and Privacy
- Follow **GDPR** requirements
- Implement **data retention** policies
- Provide **data export** functionality
- Allow users to **delete their data**
- Document **data processing** activities
- Obtain **explicit consent** when required
