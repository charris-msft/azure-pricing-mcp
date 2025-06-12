"""Azure Pricing MCP Server

A Model Context Protocol server for querying Azure retail pricing information.
"""

from .azure_pricing_server import main

__version__ = "1.0.0"
__all__ = ["main"]