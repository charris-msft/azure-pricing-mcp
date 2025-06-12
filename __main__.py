"""
Entry point for running the Azure Pricing MCP Server as a module.
Usage: python -m azure_pricing_server
"""

import asyncio
from azure_pricing_server import main

if __name__ == "__main__":
    asyncio.run(main())