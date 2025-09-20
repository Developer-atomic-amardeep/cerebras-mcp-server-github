"""
Cerebras MCP Server - High-performance Model Control Protocol server.

A powerful integration between Cerebras Cloud SDK and FastMCP for intelligent
knowledge base management and AI-driven tool orchestration.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "High-performance Model Control Protocol server with Cerebras Cloud SDK integration"

from .client import MCPCerebrasClient
from .server import mcp

__all__ = ["MCPCerebrasClient", "mcp", "__version__"]
