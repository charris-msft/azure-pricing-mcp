#!/usr/bin/env python3
"""
Azure Pricing MCP Server - Simplified Version

A Model Context Protocol server that provides tools for querying Azure retail pricing.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure Retail Prices API configuration
AZURE_PRICING_BASE_URL = "https://prices.azure.com/api/retail/prices"
DEFAULT_API_VERSION = "2023-01-01-preview"

class AzurePricingServer:
    """Azure Pricing MCP Server implementation."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to Azure Pricing API."""
        if not self.session:
            raise RuntimeError("HTTP session not initialized")
            
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def search_azure_prices(
        self,
        service_name: Optional[str] = None,
        service_family: Optional[str] = None,
        region: Optional[str] = None,
        sku_name: Optional[str] = None,
        currency_code: str = "USD",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search Azure retail prices with filters."""
        
        # Build filter conditions
        filter_conditions = []
        
        if service_name:
            filter_conditions.append(f"serviceName eq '{service_name}'")
        if service_family:
            filter_conditions.append(f"serviceFamily eq '{service_family}'")
        if region:
            filter_conditions.append(f"armRegionName eq '{region}'")
        if sku_name:
            filter_conditions.append(f"contains(skuName, '{sku_name}')")
        
        # Construct query parameters
        params = {
            "api-version": DEFAULT_API_VERSION,
            "currencyCode": currency_code
        }
        
        if filter_conditions:
            params["$filter"] = " and ".join(filter_conditions)
        
        if limit < 1000:
            params["$top"] = str(limit)
        
        # Make request
        data = await self._make_request(AZURE_PRICING_BASE_URL, params)
        
        # Process results
        items = data.get("Items", [])
        
        if len(items) > limit:
            items = items[:limit]
        
        return {
            "items": items,
            "count": len(items),
            "currency": currency_code,
            "filters_applied": filter_conditions
        }
    
    async def discover_service_skus(self, service_hint: str, limit: int = 30) -> Dict[str, Any]:
        """Discover SKUs with fuzzy service name matching."""
        
        # Service name mappings for common terms
        service_mappings = {
            "app service": "Azure App Service",
            "web app": "Azure App Service", 
            "web apps": "Azure App Service",
            "websites": "Azure App Service",
            "vm": "Virtual Machines",
            "virtual machine": "Virtual Machines",
            "compute": "Virtual Machines",
            "storage": "Storage",
            "blob": "Storage",
            "sql": "Azure SQL Database",
            "database": "Azure SQL Database",
            "kubernetes": "Azure Kubernetes Service",
            "aks": "Azure Kubernetes Service",
            "functions": "Azure Functions",
            "serverless": "Azure Functions",
        }
        
        # Try exact mapping first
        search_term = service_hint.lower()
        service_name = service_mappings.get(search_term, service_hint)
        
        # Search for the service
        result = await self.search_azure_prices(
            service_name=service_name,
            limit=limit
        )
        
        if result["items"]:
            # Process SKUs
            skus = {}
            for item in result["items"]:
                sku_name = item.get("skuName", "Unknown")
                if sku_name not in skus:
                    skus[sku_name] = {
                        "sku_name": sku_name,
                        "product_name": item.get("productName", "Unknown"),
                        "price": item.get("retailPrice", 0),
                        "unit": item.get("unitOfMeasure", "Unknown"),
                        "region": item.get("armRegionName", "Unknown")
                    }
            
            return {
                "service_found": service_name,
                "original_search": service_hint,
                "skus": skus,
                "total_skus": len(skus)
            }
        
        return {
            "service_found": None,
            "original_search": service_hint,
            "skus": {},
            "total_skus": 0,
            "suggestions": ["Try: 'app service', 'vm', 'storage', 'sql', 'kubernetes'"]
        }

# Create the MCP server
server = Server("azure-pricing")
pricing_server = AzurePricingServer()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="azure_price_search",
            description="Search Azure retail prices with filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Azure service name (e.g., 'Virtual Machines', 'Storage')"
                    },
                    "service_family": {
                        "type": "string", 
                        "description": "Service family (e.g., 'Compute', 'Storage')"
                    },
                    "region": {
                        "type": "string",
                        "description": "Azure region (e.g., 'eastus', 'westeurope')"
                    },
                    "sku_name": {
                        "type": "string",
                        "description": "SKU name to search for"
                    },
                    "currency_code": {
                        "type": "string",
                        "description": "Currency code (default: USD)",
                        "default": "USD"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="azure_sku_discovery",
            description="Discover available SKUs for Azure services with smart name matching",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_hint": {
                        "type": "string",
                        "description": "Service name or hint (e.g., 'app service', 'vm', 'storage')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 30)",
                        "default": 30
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls."""
    
    try:
        async with pricing_server:
            if name == "azure_price_search":
                result = await pricing_server.search_azure_prices(**arguments)
                
                if result["items"]:
                    response = f"Found {result['count']} Azure pricing results:\n\n"
                    
                    for i, item in enumerate(result["items"][:10], 1):
                        service = item.get("serviceName", "Unknown")
                        sku = item.get("skuName", "Unknown")
                        price = item.get("retailPrice", 0)
                        unit = item.get("unitOfMeasure", "Unknown")
                        region = item.get("armRegionName", "Unknown")
                        
                        response += f"{i}. {service} - {sku}\n"
                        response += f"   Price: ${price} per {unit}\n"
                        response += f"   Region: {region}\n\n"
                    
                    if result['count'] > 10:
                        response += f"... and {result['count'] - 10} more results"
                else:
                    response = "No pricing results found for the specified criteria."
                
                return CallToolResult(
                    content=[TextContent(type="text", text=response)]
                )
            
            elif name == "azure_sku_discovery":
                result = await pricing_server.discover_service_skus(**arguments)
                
                if result["service_found"]:
                    service_name = result["service_found"]
                    skus = result["skus"]
                    
                    response = f"SKU Discovery for '{result['original_search']}'\n"
                    if service_name != result['original_search']:
                        response += f"(Mapped to: {service_name})\n"
                    
                    response += f"\nFound {result['total_skus']} SKUs:\n\n"
                    
                    for i, (sku_name, sku_data) in enumerate(skus.items(), 1):
                        if i > 20:  # Limit display
                            response += f"... and {len(skus) - 20} more SKUs"
                            break
                        
                        response += f"{i:2d}. {sku_name}\n"
                        response += f"    Product: {sku_data['product_name']}\n"
                        response += f"    Price: ${sku_data['price']} per {sku_data['unit']}\n"
                        response += f"    Region: {sku_data['region']}\n\n"
                else:
                    suggestions = result.get("suggestions", [])
                    response = f"No exact match found for '{result['original_search']}'\n\n"
                    if suggestions:
                        response += "💡 Try these service names:\n"
                        for suggestion in suggestions:
                            response += f"• {suggestion}\n"
                
                return CallToolResult(
                    content=[TextContent(type="text", text=response)]
                )
            
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                    isError=True
                )
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True
        )

async def main():
    """Main entry point for the server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())