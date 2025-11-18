"""Agent Registry - Plugin Discovery System.

This module provides the AgentRegistry class which discovers and manages
agents registered via Python entry points.
"""

from importlib.metadata import entry_points
from typing import Any

from loguru import logger

from .factory import AgentFactory


class AgentRegistry:
    """Registry for discovering and managing agent plugins.

    Agents are discovered via Python entry points in the "agentllm.agents" group.
    Each entry point should reference an AgentFactory subclass.

    Example entry point registration in pyproject.toml:

        [project.entry-points."agentllm.agents"]
        my-agent = "my_package.agents:MyAgentFactory"
    """

    ENTRY_POINT_GROUP = "agentllm.agents"

    def __init__(self):
        """Initialize the agent registry."""
        self._factories: dict[str, type[AgentFactory]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def discover_agents(self) -> None:
        """Discover agents via entry points.

        This method scans all installed packages for entry points in the
        "agentllm.agents" group and loads the corresponding factories.
        """
        logger.info(f"Discovering agents via entry points (group: {self.ENTRY_POINT_GROUP})")

        discovered_eps = entry_points()

        # Handle different versions of importlib.metadata
        if hasattr(discovered_eps, "select"):
            # Python 3.10+
            agent_eps = discovered_eps.select(group=self.ENTRY_POINT_GROUP)
        else:
            # Python 3.9
            agent_eps = discovered_eps.get(self.ENTRY_POINT_GROUP, [])

        for ep in agent_eps:
            try:
                logger.debug(f"Loading entry point: {ep.name} = {ep.value}")
                factory_class = ep.load()

                # Validate factory
                if not issubclass(factory_class, AgentFactory):
                    logger.error(f"Entry point {ep.name} does not reference an AgentFactory subclass")
                    continue

                # Register factory
                self._factories[ep.name] = factory_class

                # Get metadata
                try:
                    metadata = factory_class.get_metadata()
                    self._metadata[ep.name] = metadata
                except Exception as e:
                    logger.warning(f"Failed to get metadata for agent {ep.name}: {e}")
                    self._metadata[ep.name] = {
                        "name": ep.name,
                        "description": "No description available",
                        "mode": "chat",
                    }

                logger.info(f"✓ Registered agent: {ep.name}")

            except Exception as e:
                logger.error(f"Failed to load entry point {ep.name}: {e}")

        logger.info(f"Discovered {len(self._factories)} agent(s)")

    def get_factory(self, agent_name: str) -> type[AgentFactory] | None:
        """Get agent factory by name.

        Args:
            agent_name: Name of the agent (e.g., "release-manager")

        Returns:
            AgentFactory class, or None if not found
        """
        return self._factories.get(agent_name)

    def get_all_factories(self) -> dict[str, type[AgentFactory]]:
        """Get all registered agent factories.

        Returns:
            Dictionary mapping agent names to factory classes
        """
        return self._factories.copy()

    def get_metadata(self, agent_name: str) -> dict[str, Any] | None:
        """Get metadata for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Metadata dictionary, or None if agent not found
        """
        return self._metadata.get(agent_name)

    def get_all_metadata(self) -> dict[str, dict[str, Any]]:
        """Get metadata for all registered agents.

        Returns:
            Dictionary mapping agent names to metadata dictionaries
        """
        return self._metadata.copy()

    def list_agents(self) -> list[str]:
        """List all registered agent names.

        Returns:
            List of agent names
        """
        return list(self._factories.keys())

    def is_registered(self, agent_name: str) -> bool:
        """Check if an agent is registered.

        Args:
            agent_name: Name of the agent

        Returns:
            True if agent is registered, False otherwise
        """
        return agent_name in self._factories
