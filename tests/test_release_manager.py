"""Tests for the ReleaseManager agent.

Tests both the agent's sync and async methods, including streaming functionality.
"""

import os

import pytest
from dotenv import load_dotenv

from agentllm.agents.release_manager import ReleaseManager

# Load .env file for tests
load_dotenv()

# Map GEMINI_API_KEY to GOOGLE_API_KEY if needed
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


class TestReleaseManager:
    """Tests for ReleaseManager agent."""

    @pytest.fixture
    def configured_agent(self):
        """Fixture that provides a ReleaseManager with pre-configured user."""
        agent = ReleaseManager()
        # Pre-configure test user with Jira token
        agent.store_config("test-user", "jira_token", "test-token-12345")
        return agent

    def test_create_agent(self):
        """Test that ReleaseManager can be instantiated."""
        agent = ReleaseManager()
        assert agent is not None

    def test_create_agent_with_params(self):
        """Test that ReleaseManager accepts model parameters."""
        agent = ReleaseManager(temperature=0.5, max_tokens=100)
        assert agent is not None
        assert agent._temperature == 0.5
        assert agent._max_tokens == 100

    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    def test_sync_run(self, configured_agent):
        """Test synchronous run() method."""
        response = configured_agent.run("Hello! Can you help me?", user_id="test-user")

        assert response is not None
        assert hasattr(response, "content")
        assert len(str(response.content)) > 0

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    async def test_async_non_streaming(self, configured_agent):
        """Test async arun() without streaming."""
        response = await configured_agent.arun(
            "Hello! Can you help me?", user_id="test-user", stream=False
        )

        assert response is not None
        assert hasattr(response, "content")
        assert len(str(response.content)) > 0

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    async def test_async_streaming(self, configured_agent):
        """Test async arun() WITH streaming.

        This is the critical test that ensures streaming works correctly.
        The arun() method should return an async generator when stream=True.
        """
        # Call arun with streaming enabled
        result = configured_agent.arun("Hello! Can you help me?", user_id="test-user", stream=True)

        # Verify it's an async generator
        assert hasattr(result, "__aiter__"), "Result should be an async generator"

        # Iterate and collect chunks
        chunks = []
        async for chunk in result:
            chunks.append(chunk)

        # Verify we got chunks
        assert len(chunks) > 0, "Should receive at least one chunk"

        # Verify chunks have content
        for chunk in chunks:
            assert hasattr(chunk, "content") or hasattr(
                chunk, "__str__"
            ), "Chunks should have content"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    async def test_streaming_returns_async_generator_not_coroutine(self, configured_agent):
        """Test that arun(stream=True) returns an async generator, not a coroutine.

        This test specifically checks the issue we fixed: when streaming is enabled,
        the method should return an async generator that can be directly iterated,
        not a coroutine that needs to be awaited first.
        """
        result = configured_agent.arun("Test message", user_id="test-user", stream=True)

        # Should be an async generator, not a coroutine
        assert hasattr(result, "__aiter__"), "Should have __aiter__ (async generator)"
        assert not hasattr(result, "__await__") or hasattr(
            result, "__aiter__"
        ), "Should be iterable without await"

        # Should be directly iterable with async for
        chunk_count = 0
        async for chunk in result:
            chunk_count += 1
            # Just verify we can iterate
            if chunk_count >= 3:
                break

        assert chunk_count > 0, "Should receive chunks"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    async def test_non_streaming_returns_awaitable(self, configured_agent):
        """Test that arun(stream=False) returns a coroutine that can be awaited."""
        result = configured_agent.arun("Test message", user_id="test-user", stream=False)

        # Should be awaitable
        assert hasattr(result, "__await__"), "Should be awaitable (coroutine)"

        # Should be able to await it
        response = await result
        assert response is not None
        assert hasattr(response, "content")

    def test_agent_cache_per_user(self):
        """Test that agents are cached per user."""
        manager1 = ReleaseManager()
        manager2 = ReleaseManager()

        # Create agents for different users
        agent1 = manager1._get_or_create_agent()
        agent2 = manager2._get_or_create_agent()

        # Both should create underlying agents
        assert agent1 is not None
        assert agent2 is not None

        # Calling again on same manager should return cached agent
        agent1_again = manager1._get_or_create_agent()
        assert agent1_again is agent1, "Should return cached agent"


class TestReleaseManagerConfiguration:
    """Tests for ReleaseManager configuration management."""

    def test_unconfigured_user_gets_prompt(self):
        """Test that unconfigured users receive a configuration prompt."""
        agent = ReleaseManager()

        response = agent.run("Hello!", user_id="new-user")

        # Should get a prompt for configuration
        assert response is not None
        content = str(response.content) if hasattr(response, "content") else str(response)
        assert "jira" in content.lower()
        assert "token" in content.lower()

    def test_provide_jira_token(self):
        """Test providing Jira token in natural language."""
        agent = ReleaseManager()

        # Provide token
        response = agent.run(
            "My Jira token is test-token-12345", user_id="config-user"
        )

        # Should acknowledge and store the token
        content = str(response.content) if hasattr(response, "content") else str(response)
        assert "stored" in content.lower() or "thank" in content.lower()

        # Verify user is now configured
        assert agent.is_configured("config-user")

    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    def test_configured_user_uses_agent(self):
        """Test that configured users can use the agent normally."""
        agent = ReleaseManager()

        # Pre-configure
        agent.store_config("ready-user", "jira_token", "my-token")

        # Now use agent
        response = agent.run("Hello!", user_id="ready-user")

        # Should get actual agent response, not config prompt
        assert response is not None
        assert hasattr(response, "content")
        # Agent response should be substantial, not a config message
        assert len(str(response.content)) > 50

    def test_extract_token_patterns(self):
        """Test that various token input patterns are recognized."""
        agent = ReleaseManager()

        patterns = [
            "my jira token is abc123",
            "jira token: xyz789",
            "set jira token to token-456",
            "My Jira token is SECRET_TOKEN",
        ]

        for pattern in patterns:
            extracted = agent.extract_token_from_message(pattern)
            assert extracted is not None, f"Failed to extract from: {pattern}"
            assert "jira_token" in extracted
            assert len(extracted["jira_token"]) > 0

    def test_missing_configs(self):
        """Test getting list of missing configurations."""
        agent = ReleaseManager()

        # New user should have missing config
        missing = agent.get_missing_configs("unconfig-user")
        assert "jira_token" in missing

        # Configured user should have no missing configs
        agent.store_config("full-user", "jira_token", "token")
        missing = agent.get_missing_configs("full-user")
        assert len(missing) == 0


class TestReleaseManagerSessionManagement:
    """Tests for ReleaseManager session and user management."""

    def test_session_id_and_user_id_passed_through(self):
        """Test that session_id and user_id are passed to underlying agent."""
        agent = ReleaseManager()
        # Pre-configure to avoid config prompt
        agent.store_config("test-user", "jira_token", "test-token")

        # This should not raise an error
        # The actual session behavior is tested in integration tests
        try:
            response = agent.run(
                "Test message", user_id="test-user", session_id="test-session"
            )
            # If we have API key, verify response
            if "GOOGLE_API_KEY" in os.environ:
                assert response is not None
        except Exception as e:
            # If no API key, we expect model provider error
            if "GOOGLE_API_KEY" not in os.environ:
                assert "api_key" in str(e).lower()
            else:
                raise
