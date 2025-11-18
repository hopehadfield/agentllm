"""This Red Hat AI (RHAI) Roadmap slide publisher Agent."""

import os
from typing import Any

from agno.db.sqlite import SqliteDb

from agentllm.agents.base import AgentFactory, BaseAgentWrapper
from agentllm.agents.rhai_roadmap_publisher_configurator import RHAIRoadmapPublisherConfigurator
from agentllm.db import TokenStorage

# Map GEMINI_API_KEY to GOOGLE_API_KEY if not set
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


class RHAIRoadmapPublisher(BaseAgentWrapper):
    """Roadmap Publisher with toolkit configuration management.

    This class extends BaseAgentWrapper to provide a RHAI Roadmap publisher agent
    specialized for Red Hat AI (RHAI) product management.

    Toolkit Configuration:
    ---------------------
    - Google Drive: OAuth-based access to Google Docs, Sheets, and Presentations (required)
    - JIRA: API token-based access to JIRA issues (required)
    - SystemPromptExtension: Extended instructions from Google Drive document (required if configured)

    The agent helps with:
    - creating a roadmap slide based on a selection of RHAI components
    """

    def __init__(
        self,
        shared_db: SqliteDb,
        token_storage: TokenStorage,
        user_id: str,
        session_id: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **model_kwargs,
    ):
        """Initialize the Roadmap Publisher with configurator pattern.

        Args:
            shared_db: Shared database instance for session management
            token_storage: Token storage instance for credentials
            user_id: User identifier (wrapper is per-user+session)
            session_id: Session identifier (optional)
            temperature: Model temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            **model_kwargs: Additional model parameters
        """
        # Store token_storage for configurator
        self._token_storage = token_storage

        # Call parent constructor (will call _create_configurator)
        super().__init__(
            shared_db=shared_db,
            user_id=user_id,
            session_id=session_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **model_kwargs,
        )

    def _create_configurator(
        self,
        user_id: str,
        session_id: str | None,
        shared_db: SqliteDb,
        **kwargs: Any,
    ) -> RHAIRoadmapPublisherConfigurator:
        """Create RHAI Roadmap Publisher configurator instance.

        Args:
            user_id: User identifier
            session_id: Session identifier
            shared_db: Shared database
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            RHAIRoadmapPublisherConfigurator instance
        """
        return RHAIRoadmapPublisherConfigurator(
            user_id=user_id,
            session_id=session_id,
            shared_db=shared_db,
            token_storage=self._token_storage,
            **kwargs,
        )


class RHAIRoadmapPublisherFactory(AgentFactory):
    """Factory for creating RHAI Roadmap Publisher instances.

    Registered via entry points in pyproject.toml for plugin system.
    """

    @staticmethod
    def create_agent(
        shared_db: Any,
        token_storage: Any,
        user_id: str,
        session_id: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> RHAIRoadmapPublisher:
        """Create a RHAI Roadmap Publisher instance.

        Args:
            shared_db: Shared database instance (SqliteDb)
            token_storage: Token storage instance (TokenStorage)
            user_id: User ID for this agent instance
            session_id: Optional session ID for conversation history
            temperature: Optional temperature parameter for the model
            max_tokens: Optional max tokens parameter for the model
            **kwargs: Additional keyword arguments for the agent

        Returns:
            RHAIRoadmapPublisher instance
        """
        return RHAIRoadmapPublisher(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id=user_id,
            session_id=session_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @staticmethod
    def get_metadata() -> dict[str, Any]:
        """Get agent metadata for proxy configuration.

        Returns:
            Dictionary with agent metadata
        """
        return {
            "name": "rhai-roadmap-publisher",
            "description": "RHAI Roadmap Publisher for Red Hat AI product management",
            "mode": "chat",
            "requires_env": ["GEMINI_API_KEY"],
        }
