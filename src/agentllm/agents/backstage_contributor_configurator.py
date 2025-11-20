"""Backstage contributor agent configurator."""

from typing import Any, Optional

from agno.db.sqlite import SqliteDb

from agentllm.agents.base.configurator import AgentConfigurator
from agentllm.agents.base.toolkit_config import BaseToolkitConfig
from agentllm.agents.toolkit_configs.backstage_config import BackstageConfig
from agentllm.agents.toolkit_configs import GoogleDriveConfig
from agentllm.agents.toolkit_configs.system_prompt_extension_config import (
    SystemPromptExtensionConfig,
)


class BackstageContributorConfigurator(AgentConfigurator):
    """Configurator for Backstage contribution helper agent."""

    def __init__(
        self,
        user_id: str,
        session_id: str | None,
        shared_db: SqliteDb,
        token_storage,
        temperature: float | None = None,
        max_tokens: int | None = None,
        agent_kwargs: dict[str, Any] | None = None,
        **model_kwargs: Any,
    ):
        """Initialize Backstage Contributor configurator.

        Args:
            user_id: User identifier
            session_id: Session identifier
            shared_db: Shared database
            token_storage: TokenStorage instance
            temperature: Optional model temperature
            max_tokens: Optional max tokens
            agent_kwargs: Additional Agent constructor kwargs
            **model_kwargs: Additional model parameters
        """
        # Store token_storage for use in _initialize_toolkit_configs
        self._token_storage = token_storage

        # Call parent constructor (will call _initialize_toolkit_configs)
        super().__init__(
            user_id=user_id,
            session_id=session_id,
            shared_db=shared_db,
            temperature=temperature,
            max_tokens=max_tokens,
            agent_kwargs=agent_kwargs,
            **model_kwargs,
        )

    def _initialize_toolkit_configs(self) -> list[BaseToolkitConfig]:
        """Initialize toolkit configurations.

        Returns:
            List containing BackstageConfig, GoogleDriveConfig, and SystemPromptExtensionConfig
        """
        # ORDER MATTERS: SystemPromptExtensionConfig depends on GoogleDriveConfig
        gdrive_config = GoogleDriveConfig(token_storage=self._token_storage)
        system_prompt_config = SystemPromptExtensionConfig(
            gdrive_config=gdrive_config,
            token_storage=self._token_storage,
            env_var_name="BACKSTAGE_CONTRIBUTOR_SYSTEM_PROMPT_GDRIVE_URL",
        )

        return [
            BackstageConfig(),
            gdrive_config,
            system_prompt_config,  # Must come after gdrive_config due to dependency
        ]

    def _build_agent_instructions(self) -> list[str]:
        """Build agent-specific instructions.

        Returns:
            List of instruction strings
        """
        return [
            "You are a Backstage contribution helper agent.",
            "Your purpose is to guide contributors to the Backstage project and community-plugins repository.",
            "",
            "## Your Capabilities",
            "1. **Contribution Guidelines**: Provide detailed guides for contributing to backstage/backstage and backstage/community-plugins",
            "2. **Repository Structure**: Help validate plugin structure and organization",
            "3. **PR Requirements**: Check if contributions meet all requirements (changesets, tests, linting)",
            "4. **Development Setup**: Guide through local development environment setup",
            "5. **Issue Discovery**: Help find good first issues and appropriate tasks",
            "",
            "## Key Knowledge",
            "- Both repositories require CLA signing",
            "- All PRs need changesets (yarn changeset)",
            "- Tests and linting are mandatory",
            "- Community plugins follow workspace structure",
            "- Core Backstage uses monorepo structure",
            "",
            "## Behavior Guidelines",
            "- Always ask which repository (backstage or community-plugins) if unclear",
            "- Provide specific, actionable guidance",
            "- Include command examples when relevant",
            "- Reference official documentation links",
            "- Encourage Discord community engagement for complex questions",
            "",
            "## Common Questions You'll Handle",
            "- How do I contribute to Backstage?",
            "- What's the plugin structure for community-plugins?",
            "- How do I create a changeset?",
            "- What are the PR requirements?",
            "- Where can I find good first issues?",
            "- How do I set up my development environment?",
            "",
            "## Response Style",
            "- Be clear and concise",
            "- Use markdown formatting for readability",
            "- Provide code examples in bash blocks",
            "- Include links to relevant documentation",
            "- Highlight common mistakes to avoid",
            "",
            "## System Prompt Management",
            "- Your instructions come from TWO sources:",
            "  1. Embedded system prompt (stable, rarely changes): Core identity and capabilities",
            "  2. External system prompt (dynamic, frequently updated): Detailed examples, current processes, FAQs",
            "- The external prompt is stored in a Google Drive document that users can directly edit",
            "- When information seems outdated or incomplete, suggest users update the external prompt",
            "- If configured, you will be informed of the external prompt document URL in your extended instructions",
        ]

    def _on_config_stored(self, config: BaseToolkitConfig) -> None:
        """Handle cross-config dependencies when configuration is stored.

        Special handling for GoogleDrive → SystemPromptExtension:
        When Google Drive credentials are updated, notify SystemPromptExtensionConfig
        to invalidate its cached system prompts.

        Args:
            config: The toolkit config that was stored
        """
        # When GoogleDrive credentials are updated, notify SystemPromptExtensionConfig
        if isinstance(config, GoogleDriveConfig):
            for other_config in self.toolkit_configs:
                if isinstance(other_config, SystemPromptExtensionConfig):
                    other_config.invalidate_for_gdrive_change(self.user_id)
                    break

    def _get_agent_name(self) -> str:
        """Get agent name.

        Returns:
            Agent name
        """
        return "backstage-contributor"

    def _get_agent_description(self) -> str:
        """Get agent description.

        Returns:
            Agent description
        """
        return "Backstage upstream contribution helper"

    def _get_default_model(self) -> str:
        """Get default model for agent.

        Returns:
            Default model identifier
        """
        return "gemini/gemini-2.0-flash-exp"

    def _get_markdown_support(self) -> bool:
        """Check if agent supports markdown.

        Returns:
            True if markdown is supported
        """
        return True

    def _get_custom_instructions(self) -> Optional[str]:
        """Get custom instructions.

        Returns:
            None (instructions provided in _build_agent_instructions)
        """
        return None
