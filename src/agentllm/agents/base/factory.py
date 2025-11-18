"""Agent factory base class for plugin system."""

from abc import ABC, abstractmethod
from typing import Any


class AgentFactory(ABC):
    """Abstract base class for agent factories.

    Each agent package must implement a factory that creates agent instances.
    The factory is registered via entry points in pyproject.toml.

    Example entry point registration in pyproject.toml:
        [project.entry-points."agentllm.agents"]
        my-agent = "my_package.agents:MyAgentFactory"
    """

    @staticmethod
    @abstractmethod
    def create_agent(
        shared_db: Any,
        token_storage: Any,
        user_id: str,
        session_id: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Create an agent instance.

        Args:
            shared_db: Shared database instance (SqliteDb)
            token_storage: Token storage instance (TokenStorage)
            user_id: User ID for this agent instance
            session_id: Optional session ID for conversation history
            temperature: Optional temperature parameter for the model
            max_tokens: Optional max tokens parameter for the model
            **kwargs: Additional keyword arguments for the agent

        Returns:
            Agent instance (subclass of BaseAgentWrapper)
        """
        pass

    @staticmethod
    def get_metadata() -> dict[str, Any]:
        """Get agent metadata for proxy configuration.

        Returns:
            Dictionary with agent metadata:
                - name: Agent name (e.g., "release-manager")
                - description: Agent description
                - mode: Agent mode (e.g., "chat")
                - requires_env: List of required environment variables
        """
        return {
            "name": "unknown",
            "description": "No description provided",
            "mode": "chat",
            "requires_env": [],
        }
