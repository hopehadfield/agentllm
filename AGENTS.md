# AGENTS.md

This file provides guidance to Claude Code when working with this repository.

## Overview

AgentLLM: LiteLLM custom provider exposing Agno agents via OpenAI-compatible API.

Architecture: `[Client] -> [LiteLLM Proxy :8890] -> [Agno Provider] -> [Agno Agent] -> [Gemini API]`

## Common Commands

```bash
# Testing
nox -s test                                    # Unit tests
nox -s integration                             # Integration tests (needs running proxy)
uv run pytest tests/test_custom_handler.py -v  # Specific test

# Development (most common)
nox -s proxy                                   # Terminal 1: local proxy with hot reload
nox -s dev_local_proxy                         # Terminal 2: OpenWebUI container

# Full container stack
nox -s dev                                     # Quick start (reuses images)
nox -s dev_build                               # Force rebuild
nox -s dev_logs                                # View logs

# Code quality
nox -s format                                  # Format
make lint                                      # Lint
```

## Critical Architecture Patterns

### Plugin System (NEW!)

AgentLLM now supports a **plugin-based architecture** for agents:

**AgentFactory Pattern:**
- Each agent implements an `AgentFactory` class
- Factories are registered via Python entry points in `pyproject.toml`
- Automatic discovery via `AgentRegistry.discover_agents()`

**Entry Point Registration:**
```toml
[project.entry-points."agentllm.agents"]
my-agent = "agentllm.agents.my_agent:MyAgentFactory"
```

**Benefits:**
- Agents as installable packages (separate repos possible)
- Auto-discovery at runtime (no manual imports needed)
- Metadata system for agent capabilities
- Clean separation of concerns

### Configurator Pattern (NEW!)

**AgentConfigurator** separates configuration management from agent execution:

**Responsibilities:**
- Configuration conversation (OAuth flows, token extraction)
- Toolkit management and collection
- Agent building with proper parameters
- Bound to user_id/session_id at construction

**BaseAgentWrapper** handles execution:
- Delegates to configurator for config management
- Provides run/arun interface
- Manages agent caching
- Handles streaming

**Key Classes:**
```python
from agentllm.agents.base import (
    AgentFactory,          # Factory for agent creation
    AgentRegistry,         # Plugin discovery
    AgentConfigurator,     # Configuration management
    BaseAgentWrapper,      # Execution interface
    BaseToolkitConfig,     # Toolkit configuration
)
```

### Custom Handler Path Resolution (GOTCHA!)

LiteLLM uses **file-based resolution**, not Python imports:

```
project_root/
├── proxy_config.yaml          # LiteLLM loads from here
├── custom_handler.py           # Stub that imports from src/
└── src/agentllm/
    └── custom_handler.py       # Actual implementation
```

**Why:** `custom_handler.agno_handler` in config → LiteLLM looks for `./custom_handler.py` → stub imports from `agentllm.custom_handler`

### Toolkit Configuration System

Base class: `BaseToolkitConfig` (`src/agentllm/agents/base/toolkit_config.py`)

Key methods:
- `is_configured(user_id)` - Check if toolkit is ready
- `extract_and_store_config(message, user_id)` - Parse and save credentials
- `get_config_prompt(user_id)` - Return prompt for missing config
- `get_toolkit(user_id)` - Return configured toolkit instance
- `is_required()` - Required toolkits prompt immediately, optional toolkits only when mentioned
- `check_authorization_request(message, user_id)` - Detect optional toolkit requests

### Streaming Format (CRITICAL!)

LiteLLM `CustomLLM` requires **GenericStreamingChunk**, NOT `ModelResponse`:

```python
{
    "text": "content",              # "text" not "content"!
    "finish_reason": "stop" or None,
    "is_finished": True or False,
    ...
}
```

## Adding New Agents

### Modern Approach (Plugin System)

1. **Create AgentConfigurator** (`src/agentllm/agents/my_agent_configurator.py`):
   ```python
   from agentllm.agents.base import AgentConfigurator, BaseToolkitConfig

   class MyAgentConfigurator(AgentConfigurator):
       def _initialize_toolkit_configs(self) -> list[BaseToolkitConfig]:
           return []  # Add toolkit configs here

       def _build_agent_instructions(self) -> list[str]:
           return ["You are my agent.", "Your purpose is..."]

       def _get_agent_name(self) -> str:
           return "my-agent"

       def _get_agent_description(self) -> str:
           return "My agent description"
   ```

2. **Create BaseAgentWrapper** (`src/agentllm/agents/my_agent.py`):
   ```python
   from agentllm.agents.base import BaseAgentWrapper
   from .my_agent_configurator import MyAgentConfigurator

   class MyAgent(BaseAgentWrapper):
       def _create_configurator(self, user_id, session_id, shared_db, **kwargs):
           return MyAgentConfigurator(
               user_id=user_id,
               session_id=session_id,
               shared_db=shared_db,
               **kwargs
           )
   ```

3. **Create AgentFactory** (in same file):
   ```python
   from agentllm.agents.base import AgentFactory

   class MyAgentFactory(AgentFactory):
       @staticmethod
       def create_agent(shared_db, token_storage, user_id, session_id=None,
                       temperature=None, max_tokens=None, **kwargs):
           return MyAgent(
               shared_db=shared_db,
               user_id=user_id,
               session_id=session_id,
               temperature=temperature,
               max_tokens=max_tokens,
               **kwargs
           )

       @staticmethod
       def get_metadata():
           return {
               "name": "my-agent",
               "description": "My agent description",
               "mode": "chat",
               "requires_env": ["SOME_API_KEY"],
           }
   ```

4. **Register in `pyproject.toml`**:
   ```toml
   [project.entry-points."agentllm.agents"]
   my-agent = "agentllm.agents.my_agent:MyAgentFactory"
   ```

5. **Add to `proxy_config.yaml`**:
   ```yaml
   - model_name: agno/my-agent
     litellm_params:
       model: agno/my-agent
       custom_llm_provider: agno
   ```

6. **The agent will be auto-discovered** by `AgentRegistry` at runtime!

### Legacy Approach (Direct Import)

1. Create `src/agentllm/agents/my_agent.py`:
   - Follow wrapper pattern (see `demo_agent.py` for reference)
   - Use `shared_db` for session memory
   - Pass through `temperature` and `max_tokens` to model

2. Import in `src/agentllm/custom_handler.py`

3. Add to `proxy_config.yaml`:
   ```yaml
   - model_name: agno/my-agent
     litellm_params:
       model: agno/my-agent
       custom_llm_provider: agno
   ```

## Key Files

```
src/agentllm/
├── custom_handler.py              # LiteLLM CustomLLM (caching, streaming)
├── agents/
│   ├── base/                      # NEW: Plugin system base classes
│   │   ├── factory.py             #   AgentFactory ABC
│   │   ├── registry.py            #   AgentRegistry (plugin discovery)
│   │   ├── configurator.py        #   AgentConfigurator (config management)
│   │   ├── wrapper.py             #   BaseAgentWrapper (execution interface)
│   │   └── toolkit_config.py      #   BaseToolkitConfig (re-export)
│   ├── release_manager.py         # Production agent wrapper
│   ├── demo_agent.py              # Reference implementation
│   └── toolkit_configs/           # Toolkit config implementations
├── tools/                         # Agno toolkits
└── db/token_storage.py            # SQLite credential storage
```

## Environment

```bash
GEMINI_API_KEY=...                 # Required
LITELLM_MASTER_KEY=...             # Proxy auth (default: sk-agno-test-key-12345)
```

See `.env.secrets.template` for full config.

## TDD Workflow

1. Write failing test
2. Implement feature
3. `nox -s test`
4. Refactor

Always use `uv run` for Python commands.
