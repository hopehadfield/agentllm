"""Base toolkit configuration - re-exports from toolkit_configs.base for backwards compatibility."""

# Re-export existing BaseToolkitConfig for backwards compatibility
from agentllm.agents.toolkit_configs.base import BaseToolkitConfig

__all__ = ["BaseToolkitConfig"]
