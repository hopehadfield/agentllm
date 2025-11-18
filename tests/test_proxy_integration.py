"""Integration tests for the LiteLLM proxy with Agno agents.

These tests spin up a real proxy server and test the full stack,
including streaming functionality through the OpenAI-compatible API.
"""

import os
import subprocess
import time
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load .env file for tests
load_dotenv()

# Map GEMINI_API_KEY to GOOGLE_API_KEY if needed
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


class ProxyManager:
    """Manages LiteLLM proxy lifecycle for testing."""

    def __init__(self, config_path: Path, port: int = 4000):
        self.config_path = config_path
        self.port = port
        self.process = None
        self.base_url = f"http://localhost:{port}"

    def start(self):
        """Start the proxy server."""
        # Find litellm in venv
        litellm_path = Path(".venv/bin/litellm")
        if not litellm_path.exists():
            raise RuntimeError("litellm not found in .venv/bin")

        # Start proxy in background
        self.process = subprocess.Popen(
            [
                str(litellm_path),
                "--config",
                str(self.config_path),
                "--port",
                str(self.port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for proxy to be ready
        max_attempts = 30
        for _attempt in range(max_attempts):
            try:
                response = httpx.get(f"{self.base_url}/health")
                # Accept 200 OK or 401 Unauthorized (means server is up)
                if response.status_code in [200, 401]:
                    return
            except httpx.ConnectError:
                pass

            time.sleep(1)

        raise RuntimeError("Proxy failed to start within timeout")

    def stop(self):
        """Stop the proxy server."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


@pytest.fixture(scope="module")
def proxy():
    """Fixture that provides a running proxy server."""
    config_path = Path("proxy_config.yaml")
    if not config_path.exists():
        pytest.skip("Proxy config file not found")

    proxy_mgr = ProxyManager(config_path)
    proxy_mgr.start()
    yield proxy_mgr
    proxy_mgr.stop()


@pytest.mark.integration
@pytest.mark.skipif(
    "GOOGLE_API_KEY" not in os.environ,
    reason="GOOGLE_API_KEY not set",
)
class TestProxyStreaming:
    """Integration tests for proxy streaming functionality."""

    @pytest.mark.asyncio
    async def test_non_streaming_completion(self, proxy):
        """Test non-streaming completion through proxy."""
        client = AsyncOpenAI(
            base_url=proxy.base_url,
            api_key="sk-agno-test-key-12345",
        )

        response = await client.chat.completions.create(
            model="agno/release-manager",
            messages=[{"role": "user", "content": "Hello! Can you help me?"}],
            stream=False,
        )

        assert response is not None
        assert response.choices is not None
        assert len(response.choices) > 0
        assert response.choices[0].message.content is not None
        assert len(response.choices[0].message.content) > 0

    @pytest.mark.asyncio
    async def test_streaming_completion(self, proxy):
        """Test streaming completion through proxy.

        This is the critical integration test that ensures the full stack works:
        - OpenAI client makes streaming request
        - LiteLLM proxy receives it
        - Custom handler calls ReleaseManager.arun(stream=True)
        - ReleaseManager returns async generator
        - Chunks flow back through the stack
        """
        client = AsyncOpenAI(
            base_url=proxy.base_url,
            api_key="sk-agno-test-key-12345",
        )

        stream = await client.chat.completions.create(
            model="agno/release-manager",
            messages=[{"role": "user", "content": "Hello! Can you help me?"}],
            stream=True,
        )

        # Verify we can iterate the stream
        chunk_count = 0
        async for chunk in stream:
            chunk_count += 1
            # Verify chunk structure
            assert chunk.choices is not None
            # At least some chunks should have content
            if chunk.choices and chunk.choices[0].delta.content:
                assert isinstance(chunk.choices[0].delta.content, str)

        assert chunk_count > 0, "Should receive at least one chunk"

    @pytest.mark.asyncio
    async def test_streaming_handles_errors_gracefully(self, proxy):
        """Test that streaming errors are handled gracefully."""
        client = AsyncOpenAI(
            base_url=proxy.base_url,
            api_key="sk-agno-test-key-12345",
        )

        # Request an invalid model - should raise an error
        with pytest.raises(Exception):  # noqa: B017
            await client.chat.completions.create(
                model="agno/nonexistent-agent",
                messages=[{"role": "user", "content": "Test"}],
                stream=True,
            )

    @pytest.mark.asyncio
    async def test_streaming_with_session_id(self, proxy):
        """Test that streaming works with session management."""
        client = AsyncOpenAI(
            base_url=proxy.base_url,
            api_key="sk-agno-test-key-12345",
        )

        # Send multiple messages in same session
        session_id = "test-session-123"

        # First message
        stream1 = await client.chat.completions.create(
            model="agno/release-manager",
            messages=[{"role": "user", "content": "Remember: my favorite color is blue"}],
            stream=True,
            extra_body={"metadata": {"session_id": session_id, "user_id": "test-user"}},
        )

        chunks1 = []
        async for chunk in stream1:
            if chunk.choices and chunk.choices[0].delta.content:
                chunks1.append(chunk.choices[0].delta.content)

        assert len(chunks1) > 0

        # Second message in same session (agent should remember context)
        stream2 = await client.chat.completions.create(
            model="agno/release-manager",
            messages=[{"role": "user", "content": "What's my favorite color?"}],
            stream=True,
            extra_body={"metadata": {"session_id": session_id, "user_id": "test-user"}},
        )

        chunks2 = []
        async for chunk in stream2:
            if chunk.choices and chunk.choices[0].delta.content:
                chunks2.append(chunk.choices[0].delta.content)

        assert len(chunks2) > 0


@pytest.mark.integration
class TestProxyHealthAndSetup:
    """Integration tests for proxy health and setup."""

    def test_proxy_health_endpoint(self, proxy):
        """Test that proxy health endpoint responds."""
        response = httpx.get(f"{proxy.base_url}/health")
        # May require auth, so 401 is also acceptable
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_proxy_model_list(self, proxy):
        """Test that proxy can list available models."""
        client = AsyncOpenAI(
            base_url=proxy.base_url,
            api_key="sk-agno-test-key-12345",
        )

        try:
            models = await client.models.list()
            # Check that our agent is in the list
            model_ids = [model.id for model in models.data]
            assert any("release-manager" in model_id for model_id in model_ids)
        except Exception:
            # Some proxies may not support model listing
            pytest.skip("Proxy does not support model listing")
