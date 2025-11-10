# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentLLM is a LiteLLM custom provider that exposes Agno agents through an OpenAI-compatible API. It enables seamless integration with Open WebUI and other OpenAI-compatible clients using LiteLLM's official `CustomLLM` extension mechanism.

**Architecture Flow:**

```
[Client] -> [LiteLLM Proxy :8890] -> [Agno Provider] -> [Agno Agent] -> [Gemini API]
```

## Development Commands

### Testing

```bash
# Run unit tests
nox -s test

# Run integration tests (requires running proxy)
nox -s integration

# Run specific test
uv run pytest tests/test_custom_handler.py::TestAgnoCustomLLM -v

# Run specific test file
uv run pytest tests/test_release_manager.py -v
```

### Running the Proxy

```bash
# Start LiteLLM proxy locally
nox -s proxy

# Or directly with uv
uv run litellm --config proxy_config.yaml --port 8890
```

## Development Modes

The project supports two development modes to accommodate different workflows:

### Development Mode (Recommended for Day-to-Day Work)

**Use case:** Fast iteration on proxy/agent code with live debugging

Run the LiteLLM proxy locally and Open WebUI in a container:

```bash
# Terminal 1: Start local proxy with hot reload
nox -s proxy

# Terminal 2: Start Open WebUI (connects to local proxy)
nox -s dev_local_proxy
```

**How it works:**
- `OPENAI_API_BASE_URL` in `.env` is set to `http://host.docker.internal:8890/v1`
- Open WebUI (containerized) connects to proxy on host machine
- Works on all platforms (Mac, Linux, Windows) via `extra_hosts` configuration
- Enables fast iteration: edit code → proxy reloads → test immediately

**Advantages:**

- Instant code reloading for proxy changes
- Easy debugging with local debuggers
- Direct log access in terminal
- Lower resource usage (one less container)

### Production Mode (Full Container Stack)

**Use case:** Testing the complete containerized setup or when not modifying proxy code

Run both services in containers:

```bash
# Start both services (foreground)
nox -s dev_full

# Or in background
nox -s dev_full -- -d
```

**How it works:**
- Overrides `OPENAI_API_BASE_URL` to `http://litellm-proxy:8890/v1`
- Both services run in Docker network
- Matches production deployment architecture

**Advantages:**

- Production-like environment
- Tests full Docker setup
- Easier for non-Python developers

### Common Docker Commands

```bash
# View logs from containers
nox -s dev-logs                    # All services
nox -s dev-logs -- litellm-proxy   # Specific service

# Stop containers (preserves data)
nox -s dev-stop

# Clean everything (including volumes)
nox -s dev-clean

# Legacy command (still works, starts both services)
nox -s dev
```

### Switching Between Modes

The mode is controlled by the `OPENAI_API_BASE_URL` environment variable in `.env`:

```bash
# Development mode (local proxy)
OPENAI_API_BASE_URL=http://host.docker.internal:8890/v1

# Production mode (both containerized) - used as default by dev-full
OPENAI_API_BASE_URL=http://litellm-proxy:8890/v1
```

**No manual configuration needed** - just use the appropriate `nox` command:

- `nox -s dev_local_proxy` - Uses value from `.env` (development mode)
- `nox -s dev_full` - Automatically overrides to container mode

### Code Quality

```bash
# Run linting
make lint

# Format code
nox -s format
```

### Making Test Requests

```bash
# Test proxy health
nox -s hello
```

## Core Architecture

### LiteLLM Custom Provider Integration

The project uses LiteLLM's **official CustomLLM extension mechanism** with dynamic registration via `custom_provider_map` in `proxy_config.yaml`:

```yaml
litellm_settings:
  custom_provider_map:
    - provider: "agno"
      custom_handler: custom_handler.agno_handler  # Relative to config location
```

**Key Implementation:** `src/agentllm/custom_handler.py`

- Extends `litellm.CustomLLM` base class
- Implements: `completion()`, `streaming()`, `acompletion()`, `astreaming()`
- Manages agent caching per (agent_name, temperature, max_tokens, user_id)
- Extracts session/user context from OpenWebUI headers and metadata

#### Custom Handler Path Resolution Pattern

LiteLLM loads custom handlers using **file-based resolution** relative to the config file location, not Python module imports. This requires a specific project structure:

**File Layout:**

```
project_root/
├── proxy_config.yaml          # Config at root (required by LiteLLM)
├── custom_handler.py           # Stub file for path resolution
└── src/agentllm/
    └── custom_handler.py       # Actual implementation
```

**Why This Pattern:**

LiteLLM's `get_instance_fn()` constructs file paths relative to the config directory:

- Config at root → looks for `./custom_handler.py`
- Handler reference: `custom_handler.agno_handler`
- Stub imports from actual implementation: `from agentllm.custom_handler import agno_handler`

**Docker Layout:**

```
/app/
├── proxy_config.yaml
├── custom_handler.py           # Stub (same as local)
├── agentllm/
│   └── custom_handler.py       # Actual implementation
```

- Same pattern as local dev, ensures consistency across environments

This pattern ensures compatibility across local development and Docker environments while keeping code organized.

### Agent Architecture

**ReleaseManager Wrapper Pattern** (`src/agentllm/agents/release_manager.py`):

- Wraps Agno `Agent` instances with configuration management
- Maintains per-user agents with toolkit isolation
- Intercepts `run()` and `arun()` calls to handle toolkit configuration
- Configuration flow:
  1. Extract configuration from user messages (OAuth codes, API tokens)
  2. Check for required toolkit configurations
  3. Prompt for missing configuration or delegate to wrapped agent
  4. Invalidate and recreate agents when new tools are authorized

**Session Management:**

- Shared SQLite database: `tmp/agno_sessions.db`
- Enables conversation history via `db=shared_db`
- Session/user context extracted from OpenWebUI headers

### Toolkit Configuration System

**Base Architecture** (`src/agentllm/agents/toolkit_configs/base.py`):

- Abstract `BaseToolkitConfig` class for service-agnostic toolkit management
- Each toolkit implements:
  - `is_configured()` - Check if user has configured this toolkit
  - `extract_and_store_config()` - Extract credentials from messages
  - `get_config_prompt()` - Prompt for missing configuration
  - `get_toolkit()` - Return configured toolkit instance
  - `check_authorization_request()` - Detect authorization requests
  - `get_agent_instructions()` - Provide toolkit-specific instructions

**Toolkit Types:**

- **Required:** Prompt immediately on first use (e.g., Google Drive)
- **Optional:** Only prompt when user mentions toolkit features (e.g., Jira)

**Current Implementations:**

- `GoogleDriveConfig` - OAuth-based Google Drive access
- `JiraConfig` - API token-based Jira access
- `SystemPromptExtensionConfig` - Extended system prompt from Google Docs
  - Fetches additional agent instructions from a Google Drive document
  - Configured via `RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL` environment variable
  - Depends on `GoogleDriveConfig` (must be registered after it)
  - Required toolkit, but silent if env var not set or GDrive not configured
  - Fails agent creation if env var set, GDrive configured, but fetch fails
  - Caches fetched prompts per user, invalidates on GDrive credential changes

### Release Manager System Prompt Architecture

The Release Manager uses a **dual-prompt architecture** that separates stable agent capabilities from dynamic operational instructions:

**Embedded System Prompt** (in `release_manager.py` lines 154-191):
- **What it contains:** Core identity, responsibilities, available tools, behavioral guidelines
- **Purpose:** "Who you are and what you can do"
- **Characteristics:** Stable, version-controlled, changes rarely
- **Examples:**
  - Identity as RHDH Release Manager
  - Core responsibilities (Y-stream, Z-stream management)
  - Available tools (Jira, Google Drive, GitHub)
  - Output and behavioral guidelines
  - Self-awareness about the dual-prompt system

**External System Prompt** (fetched from Google Drive):
- **What it contains:** Jira query patterns, response instructions, communication guidelines, process workflows
- **Purpose:** "How to respond to specific questions and what sources to query"
- **Characteristics:** Updated when processes or patterns change (NOT for specific release data)
- **Examples:**
  - Jira query patterns (reusable templates with placeholders like `RELEASE_VERSION`)
  - Response instructions for common questions ("When user asks X, query Y, format as Z")
  - Communication guidelines (Slack channels, meeting formats)
  - Escalation triggers and risk identification patterns

**Important Design Principles:**
- External prompt does **NOT** contain hardcoded release data (versions, dates) - the agent queries live sources dynamically
- External prompt is pure agent instructions, not user management documentation
- Agent is self-aware: knows about the dual-prompt system and can suggest updates to users

**Documentation:**
- `docs/release_manager_system_prompt.md` - Pure agent instruction template (what to copy to Google Doc)
- `docs/release_manager_prompt_guide.md` - User guide for setup and maintenance
- Setup: Copy the template to a Google Doc and configure via `RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL`

**Design Benefits:**
- **Code changes** for capability updates (new tools, behavior changes)
- **Doc updates** for process changes (new Jira patterns, updated workflows)
- Easy testing of prompt changes without code deployment
- Clear separation between agent identity and operational instructions
- Agent can inform users about the external prompt and guide them to update it

#### Technical Setup (External System Prompt)

**Initial Setup:**

1. **Create Google Drive Document**:
   - Copy content from `docs/release_manager_system_prompt.md`
   - Create a new Google Drive document with this content
   - Share with read access for all Release Manager users
   - (Optional) Also copy `docs/release_manager_prompt_guide.md` for content maintainers

2. **Configure Environment Variable**:
   ```bash
   # In .env file
   RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL=https://docs.google.com/document/d/1ABC123xyz/edit
   # Or just the document ID
   RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL=1ABC123xyz
   ```

3. **Verify Prerequisites**:
   - `GDRIVE_CLIENT_ID` and `GDRIVE_CLIENT_SECRET` configured
   - Users must authorize Google Drive access when first interacting with agent
   - Agent will automatically fetch and cache the prompt on first use

**How Updates Work:**

- **Edit Google Doc** → **Save** → **Agent fetches on next recreation**
- No application restart or code deployment required
- Updates take effect when:
  - User reconfigures Google Drive access (invalidates cache)
  - Agent is restarted (clears cache)
  - Application is redeployed

**Cache Behavior:**

- Prompt is cached per user after first fetch
- Cache persists until agent recreation
- To force refresh: User can re-authorize Google Drive access

**Troubleshooting:**

Common issues and solutions:
- **"Failed to fetch extended system prompt"**:
  - Check document sharing permissions
  - Verify `RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL` is correct
  - Ensure user has authorized Google Drive access
  - Check application logs for specific error message

- **Changes not reflected**:
  - Verify Google Doc shows latest edits
  - Check if agent was recreated after change
  - Test with new conversation to force agent initialization

- **Agent not fetching prompt**:
  - Prompt is cached until agent recreation
  - Normal behavior - updates only fetch on agent recreation

**Production vs Development:**

Consider separate prompts for different environments:
```bash
# Development .env
RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL=https://docs.google.com/document/d/[DEV_DOC_ID]/edit

# Production .env
RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL=https://docs.google.com/document/d/[PROD_DOC_ID]/edit
```

This allows testing prompt changes before deploying to production.

### Token Storage

**Centralized Credential Storage** (`src/agentllm/db/token_storage.py`):

- SQLite-backed storage for OAuth credentials and API tokens
- Reuses Agno's `SqliteDb` engine for single database
- Tables: `jira_tokens`, `gdrive_tokens`
- Operations: `upsert_*_token()`, `get_*_token()`, `delete_*_token()`

### Streaming Support

LiteLLM's `CustomLLM` requires **GenericStreamingChunk format** (not `ModelResponse`):

```python
{
    "text": "content here",           # Use "text", not "content"
    "finish_reason": "stop" or None,
    "index": 0,
    "is_finished": True or False,
    "tool_use": None,
    "usage": {...}
}
```

**Implementation:**

- Sync streaming (`streaming()`): Returns complete response as single chunk
- Async streaming (`astreaming()`): True real-time streaming using `agent.arun(stream=True)`

## Project Structure

```
src/agentllm/
├── custom_handler.py              # LiteLLM CustomLLM implementation
├── proxy_config.yaml              # LiteLLM proxy configuration
├── agents/
│   ├── release_manager.py         # ReleaseManager wrapper class
│   └── toolkit_configs/
│       ├── base.py                # Abstract base class
│       ├── gdrive_config.py       # Google Drive OAuth config
│       ├── jira_config.py         # Jira API token config
│       └── system_prompt_extension_config.py  # System prompt extension
├── tools/
│   ├── gdrive_toolkit.py          # Google Drive tools
│   ├── gdrive_utils.py            # OAuth flow utilities
│   └── jira_toolkit.py            # Jira tools
└── db/
    └── token_storage.py           # SQLite token storage
```

## Adding New Agents

1. Create agent file in `src/agentllm/agents/`:

```python
from agno.agent import Agent
from agno.models.google import Gemini
from agentllm.agents.release_manager import shared_db

def create_my_agent(temperature=None, max_tokens=None, **kwargs):
    model_params = {"id": "gemini-2.5-flash"}
    if temperature is not None:
        model_params["temperature"] = temperature
    if max_tokens is not None:
        model_params["max_tokens"] = max_tokens

    return Agent(
        name="my-agent",
        model=Gemini(**model_params),
        description="My custom agent",
        instructions=["Your instructions"],
        db=shared_db,
        add_history_to_context=True,
        num_history_runs=10,
    )
```

2. Update `custom_handler.py` to import and instantiate new agent

3. Add to `proxy_config.yaml`:

```yaml
- model_name: agno/my-agent
  litellm_params:
    model: agno/my-agent
    custom_llm_provider: agno
```

## Environment Setup

Required environment variables (see `.env.example`):

- `GEMINI_API_KEY` - Required for all models (get from <https://aistudio.google.com/apikey>)
- `LITELLM_MASTER_KEY` - API key for proxy access (default: `sk-agno-test-key-12345`)

## OpenWebUI Configuration

OpenWebUI is configured exclusively through environment variables (no configuration files). The project uses a standardized configuration approach across local development and production environments.

### Core Configuration Variables

**LiteLLM Proxy Connection:**
```bash
OPENAI_API_BASE_URL=http://host.docker.internal:8890/v1  # Local dev
OPENAI_API_KEY=${LITELLM_MASTER_KEY}
```

**Branding & Defaults:**
```bash
WEBUI_NAME=Sidekick Agent
WEBUI_URL=http://localhost:8080                # Required for OAuth redirects
DEFAULT_MODELS=agno/release-manager
```

**Authentication:**
```bash
WEBUI_AUTH=true
ENABLE_SIGNUP=false                            # OAuth-only signup
ENABLE_OAUTH_SIGNUP=true
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
```

**Security Settings:**
```bash
# Local development (HTTP)
WEBUI_SESSION_COOKIE_SAME_SITE=lax
WEBUI_SESSION_COOKIE_SECURE=false              # Set to true in production
WEBUI_AUTH_COOKIE_SECURE=false                 # Set to true in production
```

**Logging:**
```bash
LOG_LEVEL=DEBUG                                # Use INFO in production
UVICORN_LOG_LEVEL=debug
GLOBAL_LOG_LEVEL=DEBUG
```

### Disabled Features

**RAG and Web Search:**
```bash
ENABLE_RAG_WEB_SEARCH=false
RAG_EMBEDDING_MODEL=""
RAG_EMBEDDING_ENGINE=""
```

**Why RAG is Disabled:**
- AgentLLM uses **agent-level tools** (Google Drive, Jira) for document access
- Agent tools are superior because they:
  - Work programmatically across all clients (not just OpenWebUI)
  - Don't require manual document uploads per user
  - Provide real-time access to source systems
  - Are controlled by the agent with proper context

**Other Disabled Features:**
```bash
ENABLE_OLLAMA_API=false                        # Using LiteLLM proxy instead
ENABLE_COMMUNITY_SHARING=false                 # Security best practice
OFFLINE_MODE=true                              # Production only - prevents downloads
```

### Local vs Production Configuration

**Local Development:**
- Uses `OPENAI_API_BASE_URL=http://host.docker.internal:8890/v1`
- Cookie security disabled (HTTP mode)
- Verbose logging (DEBUG level)
- OAuth optional (can use basic auth)

**Production (Kubernetes):**
- Uses `OPENAI_API_BASE_URL=http://litellm-proxy-service:8890/v1`
- Cookie security enabled (HTTPS mode)
- Reduced logging (INFO level)
- OAuth required (signup disabled)
- `WEBUI_URL` auto-configured by deploy script from OpenShift route

### Configuration Methods

OpenWebUI supports three ways to set environment variables:

1. **`.env` file** - Used locally via Docker Compose `env_file:` directive
2. **Kubernetes ConfigMaps/Secrets** - Used in production deployment
3. **Docker Compose `environment:`** - Direct variable specification

See `.env.example` for complete local configuration template.

## Key Implementation Details

### Session Context Extraction

Session/user context is extracted from multiple sources (priority order):

1. Request body metadata (from OpenWebUI pipe functions)
2. OpenWebUI headers (`X-OpenWebUI-User-Id`, `X-OpenWebUI-Chat-Id`)
3. LiteLLM metadata
4. User field

See `_extract_session_info()` in `custom_handler.py`

### Agent Caching Strategy

- Agents cached by: `(agent_name, temperature, max_tokens, user_id)`
- Per-user isolation ensures credential separation
- Cache invalidation on toolkit authorization changes

### Configuration Flow

1. User sends message
2. ReleaseManager checks for embedded configuration (OAuth codes, tokens)
3. If found: extract, validate, store, invalidate agent cache
4. If required toolkit unconfigured: return prompt
5. If optional toolkit requested but unconfigured: return prompt
6. Otherwise: get/create agent and run

## Testing Approach

Project follows Test-Driven Development (TDD):

1. Write failing test
2. Implement feature
3. Run tests: `nox -s test`
4. Refactor as needed

## Package Manager

This project uses **uv** for dependency management. Always use `uv run` or `uv sync` for Python commands.

## Context7 Documentation Server

**When to use:**

- Working with external libraries/frameworks
- Implementing new integrations or features with third-party tools
- Need current documentation beyond training cutoff
- Troubleshooting library-specific issues

Libraries in this project:

- Agno: mcp__context7__get_library_docs(context7CompatibleLibraryID="/websites/agno")
- LiteLLM: mcp__context7__get_library_docs(context7CompatibleLibraryID="/berriai/litellm")
- OpenWebUI: mcp__context7__get_library_docs(context7CompatibleLibraryID="/websites/openwebui")
