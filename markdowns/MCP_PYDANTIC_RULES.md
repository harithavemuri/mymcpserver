# MCP_PYDANTIC_RULES.md

## 1. Project Identity & Role
* **Goal:** Create a production-grade Model Context Protocol (MCP) Server.
* **Stack:** Python 3.11+, Pydantic v2+, mcp SDK (official), google-generativeai.
* **Role:** Senior Python Backend Engineer specializing in LLM interoperability.

## 2. Core Architectural Standards

### A. The FastMCP Standard
* **Primary Interface:** Use mcp.server.fastmcp.FastMCP for all server implementations. Do not use the low-level Server class unless explicitly requested for complex custom transport requirements.
* **Transport:** Default to **Stdio** (Standard Input/Output) transport.
* **Lifecycle:** Ensure the server is runnable via mcp.run() or an explicit entry point entry.

### B. JSON-RPC Strictness (CRITICAL)
* **Stdout is Sacred:** stdout is reserved **exclusively** for JSON-RPC message passing.
* **No Print Statements:** NEVER use print() for logging or debugging.
* **Stderr for Logs:** All logs, debug info, and status updates must be written to sys.stderr or via the MCP logging interface.

### C. Type Safety & Validation
* **Pydantic Models:** Use pydantic.BaseModel for complex tool inputs.
* **Type Hints:** strict Python type hints (str, int, list[str]) are mandatory for all tool arguments.
* **Docstrings:** Every @mcp.tool() must have a descriptive docstring. The LLM client uses this docstring to understand *how* and *why* to call the tool.

## 3. Implementation Rules

### Rule 1: Tool Definition
* Decorate functions with @mcp.tool().
* Functions must be sync.
* Include a docstring describing the arguments.

### Rule 2: Resource Definition
* Use @mcp.resource("uri://scheme/{param}") for reading data.
* Resources are for **GET** (reading) operations; Tools are for **POST** (action) operations.

### Rule 3: Error Handling
* Use 	ry/except blocks inside tools.
* Return descriptive error messages as strings rather than raising unhandled exceptions that crash the server.

## 4. Gemini AI Integration Guidelines
*Apply these rules only when the server requires Generative AI capabilities.*

### A. Configuration
* **Library:** google-generativeai
* **Auth:** Must load API key from os.environ["GEMINI_API_KEY"]. **Never** hardcode keys.
* **Model:** Default to gemini-1.5-flash for speed/cost unless gemini-1.5-pro is required for reasoning depth.

### B. Async Execution
* The google-generativeai library has async methods. Use them to avoid blocking the MCP server event loop.

## 5. Folder Structure
Keep the project flat and standard:
.
├── main.py           # Server entry point
├── pyproject.toml    # Dependencies
├── .env              # API Keys (GitIgnored)
├── README.md         # Usage instructions
└── RULES.md          # Context for AI generation

## 6. Pre-Flight Checklist
Before finalizing code, verify:
1.  [ ] No print() statements exist (use logging).
2.  [ ] All tools have docstrings.
3.  [ ] All I/O is asynchronous.
4.  [ ] Gemini API calls use wait generate_content_async.
