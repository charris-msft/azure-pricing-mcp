"""
Entry point for running the simplified Azure Pricing MCP Server as a module.
Usage: python -m azure_pricing_server_simple
"""

import asyncio
from azure_pricing_server_simple import main

if __name__ == "__main__":
    asyncio.run(main())