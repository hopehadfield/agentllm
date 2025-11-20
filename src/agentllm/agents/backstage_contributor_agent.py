"""Backstage contribution helper agent."""

from typing import Any, Optional

from agentllm.agents.base.factory import AgentFactory
from agentllm.agents.base.wrapper import BaseAgentWrapper
from agentllm.agents.backstage_contributor_configurator import BackstageContributorConfigurator


class BackstageContributorAgent(BaseAgentWrapper):
    """Agent wrapper for Backstage contribution guidance."""

    def __init__(
        self,
        shared_db,
        token_storage,
        user_id: str,
        session_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **model_kwargs,
    ):
        """Initialize the Backstage Contributor Agent.

        Args:
            shared_db: Shared database instance for session management
            token_storage: Token storage instance for Google Drive credentials
            user_id: User identifier
            session_id: Session identifier (optional)
            temperature: Model temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            **model_kwargs: Additional model parameters
        """
        # Store token_storage for configurator
        self._token_storage = token_storage

        # Call parent constructor
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
        session_id: Optional[str] = None,
        shared_db=None,
        **kwargs,
    ) -> BackstageContributorConfigurator:
        """Create configurator for Backstage contributor agent.

        Args:
            user_id: User identifier
            session_id: Session identifier
            shared_db: Shared database instance
            **kwargs: Additional arguments

        Returns:
            BackstageContributorConfigurator instance
        """
        return BackstageContributorConfigurator(
            user_id=user_id,
            session_id=session_id,
            shared_db=shared_db,
            token_storage=self._token_storage,
            **kwargs,
        )


class BackstageContributorAgentFactory(AgentFactory):
    """Factory for creating Backstage contributor agent instances."""

    @staticmethod
    def create_agent(
        shared_db,
        token_storage,
        user_id: str,
        session_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> BackstageContributorAgent:
        """Create BackstageContributorAgent instance.

        Args:
            shared_db: Shared database instance
            token_storage: Token storage instance
            user_id: User identifier
            session_id: Session identifier
            temperature: Model temperature
            max_tokens: Maximum tokens for response
            **kwargs: Additional arguments

        Returns:
            BackstageContributorAgent instance
        """
        return BackstageContributorAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id=user_id,
            session_id=session_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @staticmethod
    def get_metadata() -> dict:
        """Get agent metadata.

        Returns:
            Agent metadata dictionary
        """
        return {
            "name": "backstage-contributor",
            "description": "Backstage upstream contribution helper for backstage/backstage and backstage/community-plugins repositories",
            "mode": "chat",
            "requires_env": [],  # No env vars required
            "capabilities": [
                "contribution_guidelines",
                "repo_structure_validation",
                "pr_requirements_check",
                "development_setup",
                "issue_discovery",
            ],
        }
