"""Backstage toolkit configuration."""

from typing import Optional

from agentllm.agents.base.toolkit_config import BaseToolkitConfig
from agentllm.tools.backstage_toolkit import BackstageToolkit


class BackstageConfig(BaseToolkitConfig):
    """Configuration for Backstage contribution toolkit."""

    def __init__(self):
        """Initialize BackstageConfig.

        No configuration required for Backstage toolkit (public repo guidance).
        """
        super().__init__()

    def is_configured(self, user_id: str) -> bool:
        """Check if Backstage toolkit is configured.

        Args:
            user_id: User identifier

        Returns:
            Always True (no configuration required for public repo guidance)
        """
        return True

    def extract_and_store_config(self, message: str, user_id: str) -> bool:
        """Extract and store configuration from message.

        Args:
            message: User message
            user_id: User identifier

        Returns:
            False (no configuration needed)
        """
        return False

    def get_config_prompt(self, user_id: str) -> Optional[str]:
        """Get configuration prompt.

        Args:
            user_id: User identifier

        Returns:
            None (no configuration required)
        """
        return None

    def get_toolkit(self, user_id: str) -> BackstageToolkit:
        """Get Backstage toolkit instance.

        Args:
            user_id: User identifier

        Returns:
            Configured BackstageToolkit
        """
        return BackstageToolkit()

    def is_required(self) -> bool:
        """Check if toolkit is required.

        Returns:
            False (toolkit is always available, no setup needed)
        """
        return False

    def check_authorization_request(self, message: str, user_id: str) -> bool:
        """Check if message requests Backstage guidance.

        Args:
            message: User message
            user_id: User identifier

        Returns:
            True if message mentions Backstage/contribution
        """
        keywords = ["backstage", "contribution", "contribute", "upstream", "community plugin"]
        return any(keyword in message.lower() for keyword in keywords)
