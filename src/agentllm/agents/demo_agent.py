"""
Demo Agent - A simple example agent for showcasing AgentLLM features.

This agent demonstrates:
- Required configuration flow (favorite color)
- Simple utility tools (color palette generation)
- Extensive logging for debugging and education
- Session memory and conversation history
- Streaming and non-streaming responses
"""

import os

from agno.db.sqlite import SqliteDb

from agentllm.agents.base_agent import BaseAgentWrapper
from agentllm.agents.toolkit_configs.base import BaseToolkitConfig
from agentllm.agents.toolkit_configs.favorite_color_config import FavoriteColorConfig
from agentllm.db import TokenStorage

# Map GEMINI_API_KEY to GOOGLE_API_KEY if not set
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


class DemoAgent(BaseAgentWrapper):
    """
    Demo Agent for showcasing AgentLLM platform features.

    This agent is intentionally simple and well-documented to serve as:
    1. A reference implementation for creating new agents
    2. A demonstration of the platform's capabilities
    3. An educational tool with extensive logging

    Key Features Demonstrated:
    - Required toolkit configuration (FavoriteColorConfig)
    - Simple utility tools (ColorTools)
    - Session memory and conversation history
    - Streaming and non-streaming responses
    - Per-user agent isolation
    - Configuration validation and error handling
    - Extensive logging throughout execution flow (inherited from base)

    The agent extends BaseAgentWrapper, which provides all common functionality.
    This class only implements agent-specific customizations.
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
        """
        Initialize the Demo Agent with toolkit configurations.

        Args:
            shared_db: Shared database instance for session management
            token_storage: Token storage instance for credentials
            user_id: User identifier (wrapper is per-user+session)
            session_id: Session identifier (optional)
            temperature: Model temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            **model_kwargs: Additional model parameters
        """
        # Store token_storage for toolkit config initialization
        self._token_storage = token_storage

        # Call parent constructor (will call _initialize_toolkit_configs)
        super().__init__(
            shared_db=shared_db,
            user_id=user_id,
            session_id=session_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **model_kwargs,
        )

    def _initialize_toolkit_configs(self) -> list[BaseToolkitConfig]:
        """
        Initialize toolkit configurations for Demo Agent.

        Returns:
            List of toolkit configuration instances
        """
        return [
            FavoriteColorConfig(token_storage=self._token_storage),  # Required: user must configure before using agent
        ]

    def _get_agent_name(self) -> str:
        """Return agent name."""
        return "demo-agent"

    def _get_agent_description(self) -> str:
        """Return agent description."""
        return "A demo agent showcasing AgentLLM features"

    def _build_agent_instructions(self, user_id: str) -> list[str]:
        """
        Build agent-specific instructions for Demo Agent.

        Args:
            user_id: User identifier

        Returns:
            List of instruction strings
        """
        return [
            "You are the **Demo Agent** - an interactive demonstration of AgentLLM's capabilities!",
            "",
            "🎯 **Your Mission:**",
            "Guide users through an interactive demo that showcases:",
            "1. Required configuration flow (favorite color setup)",
            "2. Simple tool usage (palette generation)",
            "3. Complex reasoning capabilities (intelligent color scheme design)",
            "4. Session memory and conversation history",
            "",
            "🎭 **Interactive Demo Flow:**",
            "",
            "**STEP 1 - Configuration (Required First):**",
            "- If user hasn't configured their favorite color, warmly welcome them",
            "- Explain this is an interactive demo that will showcase AgentLLM features",
            "- Tell them the first step is choosing their favorite color from: red, blue, green, yellow, purple, orange, pink, black, white, or brown",
            "- After they configure, celebrate and move to Step 2",
            "",
            "**STEP 2 - Simple Tool Demo:**",
            "- After color is configured, suggest: 'Now let me show you a simple tool! Would you like me to generate a color palette based on your favorite color? I can create complementary, analogous, or monochromatic palettes.'",
            "- When they agree, use the generate_color_palette tool",
            "- Explain what the tool did and the result",
            "- Then transition to Step 3",
            "",
            "**STEP 3 - Complex Reasoning Demo:**",
            '- After the simple palette demo, suggest: \'Great! Now let me demonstrate my reasoning capabilities. I can design a complete color scheme for a specific purpose - like "calming meditation app", "energetic sports brand", or "professional website". What would you like me to design a color scheme for?\'',
            "- When they provide a purpose, use the design_color_scheme_for_purpose tool",
            "- This tool is complex and will trigger your step-by-step reasoning process",
            "- The user will be able to see how you think through the problem",
            "- After showing the result, explain that they just saw your reasoning in action",
            "",
            "**STEP 4 - Exploration:**",
            "- Invite them to try other things or ask questions about the platform",
            "- You can explain architecture, show other tool capabilities, or discuss implementation",
            "",
            "🛠 **Your Available Tools:**",
            "1. `generate_color_palette` - Simple tool that creates color harmonies",
            "2. `format_text_with_theme` - Formats text with color themes",
            "3. `design_color_scheme_for_purpose` - Complex tool requiring reasoning (the star of the demo!)",
            "",
            "💬 **Communication Style:**",
            "- Be enthusiastic and friendly - you're giving a demo!",
            "- Guide users proactively through the steps",
            "- Use markdown formatting for visual appeal",
            "- When using tools, briefly explain what you're doing",
            "- After Step 3, mention that the user saw your 'thinking process' in action",
            "",
            "🧠 **About Your Reasoning Capability:**",
            "- You have step-by-step reasoning enabled (reasoning=True)",
            "- When tasks are complex, you think through them visibly",
            "- The design_color_scheme_for_purpose tool is specifically designed to trigger this",
            "- This showcases how AgentLLM agents can handle complex decision-making",
            "",
            "📚 **If Asked About Implementation:**",
            "- You can explain: configuration flow, tool creation, logging, session management, reasoning",
            "- Point users to code files: demo_agent.py, color_toolkit.py, favorite_color_config.py",
            "- Be transparent about being a demo/educational agent",
            "",
            "🎨 **About Favorite Color Configuration:**",
            "- This demonstrates the **required configuration pattern**",
            "- Configuration is stored per-user and persists across sessions",
            "- Changing the color recreates your agent with updated tools",
            "- This pattern is reused for real agents (Google Drive OAuth, Jira tokens, etc.)",
            "",
            "⚡ **Key Points:**",
            "- Always guide users through the demo steps in order",
            "- Be proactive in suggesting next steps",
            "- Celebrate each completed step",
            "- Make it fun and educational!",
        ]

    def _build_model_params(self) -> dict:
        """
        Override to configure Gemini with native thinking capability.

        This extends the base model params by adding:
        - thinking_budget: Allocate tokens for thinking
        - include_thoughts: Request thought summaries in response

        These params get passed to Gemini(**model_params) in base agent.

        Returns:
            Dictionary with base model params + thinking configuration
        """
        # Get base model params (id, temperature, max_output_tokens)
        model_params = super()._build_model_params()

        # Add Gemini native thinking parameters
        model_params["thinking_budget"] = 200  # Allocate up to 200 tokens for thinking
        model_params["include_thoughts"] = True  # Request thought summaries in response

        return model_params

    def _get_agent_kwargs(self) -> dict:
        """
        Get agent kwargs without Agno's reasoning agent.

        We rely on Gemini's native thinking (configured in _build_model_params)
        instead of Agno's ReasoningAgent pattern. Gemini will include thinking
        directly in the response content formatted as <details> blocks.

        Returns:
            Dictionary with base defaults (NO reasoning=True)
        """
        # Get base defaults (db, add_history_to_context, etc.)
        kwargs = super()._get_agent_kwargs()

        # DO NOT set reasoning=True here!
        # When reasoning=True, Agno uses its ReasoningAgent which suppresses
        # Gemini's native thinking. We want Gemini's thinking to appear directly
        # in the response content as formatted <details> blocks.

        return kwargs

    def _on_config_stored(self, config: BaseToolkitConfig, user_id: str) -> None:
        pass
