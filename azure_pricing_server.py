#!/usr/bin/env python3
"""
Azure Pricing MCP Server

A Model Context Protocol server that provides tools for querying Azure retail pricing.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode, quote

import aiohttp
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.session import ServerSession
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure Retail Prices API configuration
AZURE_PRICING_BASE_URL = "https://prices.azure.com/api/retail/prices"
DEFAULT_API_VERSION = "2023-01-01-preview"
MAX_RESULTS_PER_REQUEST = 1000

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
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during request: {e}")
            raise
    
    async def search_azure_prices(
        self,
        service_name: Optional[str] = None,
        service_family: Optional[str] = None,
        region: Optional[str] = None,
        sku_name: Optional[str] = None,
        price_type: Optional[str] = None,
        currency_code: str = "USD",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search Azure retail prices with various filters."""
        
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
        if price_type:
            filter_conditions.append(f"priceType eq '{price_type}'")
        
        # Construct query parameters
        params = {
            "api-version": DEFAULT_API_VERSION,
            "currencyCode": currency_code
        }
        
        if filter_conditions:
            params["$filter"] = " and ".join(filter_conditions)
        
        # Limit results
        if limit < MAX_RESULTS_PER_REQUEST:
            params["$top"] = str(limit)
        
        # Make request
        data = await self._make_request(AZURE_PRICING_BASE_URL, params)
        
        # Process results
        items = data.get("Items", [])
        
        # If we have more results than requested, truncate
        if len(items) > limit:
            items = items[:limit]
        
        return {
            "items": items,
            "count": len(items),
            "has_more": bool(data.get("NextPageLink")),
            "currency": currency_code,
            "filters_applied": filter_conditions
        }
    
    async def compare_prices(
        self,
        service_name: str,
        sku_name: Optional[str] = None,
        regions: Optional[List[str]] = None,
        currency_code: str = "USD"
    ) -> Dict[str, Any]:
        """Compare prices across different regions or SKUs."""
        
        comparisons = []
        
        if regions:
            # Compare across regions
            for region in regions:
                try:
                    result = await self.search_azure_prices(
                        service_name=service_name,
                        sku_name=sku_name,
                        region=region,
                        currency_code=currency_code,
                        limit=10
                    )
                    
                    if result["items"]:
                        # Get the first item for comparison
                        item = result["items"][0]
                        comparisons.append({
                            "region": region,
                            "sku_name": item.get("skuName"),
                            "retail_price": item.get("retailPrice"),
                            "unit_of_measure": item.get("unitOfMeasure"),
                            "product_name": item.get("productName"),
                            "meter_name": item.get("meterName")
                        })
                except Exception as e:
                    logger.warning(f"Failed to get prices for region {region}: {e}")
        else:
            # Compare different SKUs within the same service
            result = await self.search_azure_prices(
                service_name=service_name,
                currency_code=currency_code,
                limit=20
            )
            
            # Group by SKU
            sku_prices = {}
            for item in result["items"]:
                sku = item.get("skuName")
                if sku and sku not in sku_prices:
                    sku_prices[sku] = {
                        "sku_name": sku,
                        "retail_price": item.get("retailPrice"),
                        "unit_of_measure": item.get("unitOfMeasure"),
                        "product_name": item.get("productName"),
                        "region": item.get("armRegionName"),
                        "meter_name": item.get("meterName")
                    }
            
            comparisons = list(sku_prices.values())
        
        # Sort by price
        comparisons.sort(key=lambda x: x.get("retail_price", 0))
        
        return {
            "comparisons": comparisons,
            "service_name": service_name,
            "currency": currency_code,
            "comparison_type": "regions" if regions else "skus"
        }
    
    async def estimate_costs(
        self,
        service_name: str,
        sku_name: str,
        region: str,
        hours_per_month: float = 730,  # Default to full month
        currency_code: str = "USD"
    ) -> Dict[str, Any]:
        """Estimate monthly costs based on usage."""
        
        # Get pricing information
        result = await self.search_azure_prices(
            service_name=service_name,
            sku_name=sku_name,
            region=region,
            currency_code=currency_code,
            limit=5
        )
        
        if not result["items"]:
            return {
                "error": f"No pricing found for {sku_name} in {region}",
                "service_name": service_name,
                "sku_name": sku_name,
                "region": region
            }
        
        item = result["items"][0]
        hourly_rate = item.get("retailPrice", 0)
        
        # Calculate estimates
        monthly_cost = hourly_rate * hours_per_month
        daily_cost = hourly_rate * 24
        yearly_cost = monthly_cost * 12
        
        # Check for savings plans
        savings_plans = item.get("savingsPlan", [])
        savings_estimates = []
        
        for plan in savings_plans:
            plan_hourly = plan.get("retailPrice", 0)
            plan_monthly = plan_hourly * hours_per_month
            plan_yearly = plan_monthly * 12
            savings_percent = ((hourly_rate - plan_hourly) / hourly_rate) * 100 if hourly_rate > 0 else 0
            
            savings_estimates.append({
                "term": plan.get("term"),
                "hourly_rate": plan_hourly,
                "monthly_cost": plan_monthly,
                "yearly_cost": plan_yearly,
                "savings_percent": round(savings_percent, 2),
                "annual_savings": round((yearly_cost - plan_yearly), 2)
            })
        
        return {
            "service_name": service_name,
            "sku_name": item.get("skuName"),
            "region": region,
            "product_name": item.get("productName"),
            "unit_of_measure": item.get("unitOfMeasure"),
            "currency": currency_code,
            "on_demand_pricing": {
                "hourly_rate": hourly_rate,
                "daily_cost": round(daily_cost, 2),
                "monthly_cost": round(monthly_cost, 2),
                "yearly_cost": round(yearly_cost, 2)
            },
            "usage_assumptions": {
                "hours_per_month": hours_per_month,
                "hours_per_day": round(hours_per_month / 30.44, 2)  # Average days per month
            },
            "savings_plans": savings_estimates
        }

    async def discover_skus(
        self,
        service_name: str,
        region: Optional[str] = None,
        price_type: str = "Consumption",
        limit: int = 100
    ) -> Dict[str, Any]:
        """Discover available SKUs for a specific Azure service."""
        
        # Build filter conditions
        filter_conditions = [f"serviceName eq '{service_name}'"]
        
        if region:
            filter_conditions.append(f"armRegionName eq '{region}'")
        
        if price_type:
            filter_conditions.append(f"priceType eq '{price_type}'")
        
        # Construct query parameters
        params = {
            "api-version": DEFAULT_API_VERSION,
            "currencyCode": "USD"
        }
        
        if filter_conditions:
            params["$filter"] = " and ".join(filter_conditions)
        
        # Limit results
        if limit < MAX_RESULTS_PER_REQUEST:
            params["$top"] = str(limit)
        
        # Make request
        data = await self._make_request(AZURE_PRICING_BASE_URL, params)
        
        # Process and deduplicate SKUs
        skus = {}
        items = data.get("Items", [])
        
        for item in items:
            sku_name = item.get("skuName")
            arm_sku_name = item.get("armSkuName")
            product_name = item.get("productName")
            region = item.get("armRegionName")
            price = item.get("retailPrice", 0)
            unit = item.get("unitOfMeasure")
            meter_name = item.get("meterName")
            
            if sku_name and sku_name not in skus:
                skus[sku_name] = {
                    "sku_name": sku_name,
                    "arm_sku_name": arm_sku_name,
                    "product_name": product_name,
                    "sample_price": price,
                    "unit_of_measure": unit,
                    "meter_name": meter_name,
                    "sample_region": region,
                    "available_regions": [region] if region else []
                }
            elif sku_name and region and region not in skus[sku_name]["available_regions"]:
                # Add region to existing SKU
                skus[sku_name]["available_regions"].append(region)
        
        # Convert to list and sort by SKU name
        sku_list = list(skus.values())
        sku_list.sort(key=lambda x: x["sku_name"])
        
        return {
            "service_name": service_name,
            "skus": sku_list,
            "total_skus": len(sku_list),
            "price_type": price_type,
            "region_filter": region
        }

    async def search_azure_prices_with_fuzzy_matching(
        self,
        service_name: Optional[str] = None,
        service_family: Optional[str] = None,
        region: Optional[str] = None,
        sku_name: Optional[str] = None,
        price_type: Optional[str] = None,
        currency_code: str = "USD",
        limit: int = 50,
        suggest_alternatives: bool = True
    ) -> Dict[str, Any]:
        """
        Search Azure retail prices with fuzzy matching and suggestions.
        If exact matches aren't found, suggests similar services.
        """
        
        # First try exact search
        exact_result = await self.search_azure_prices(
            service_name=service_name,
            service_family=service_family,
            region=region,
            sku_name=sku_name,
            price_type=price_type,
            currency_code=currency_code,
            limit=limit
        )
        
        # If we got results, return them
        if exact_result["items"]:
            return exact_result
        
        # If no results and suggest_alternatives is True, try fuzzy matching
        if suggest_alternatives and (service_name or service_family):
            return await self._find_similar_services(
                service_name=service_name,
                service_family=service_family,
                currency_code=currency_code,
                limit=limit
            )
        
        return exact_result
    
    async def _find_similar_services(
        self,
        service_name: Optional[str] = None,
        service_family: Optional[str] = None,
        currency_code: str = "USD",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Find services with similar names or suggest alternatives."""
        
        # Common service name mappings
        service_mappings = {
            # User input -> Correct Azure service name
            "app service": "Azure App Service",
            "web app": "Azure App Service",
            "web apps": "Azure App Service",
            "app services": "Azure App Service",
            "websites": "Azure App Service",
            "web service": "Azure App Service",
            
            "virtual machine": "Virtual Machines",
            "vm": "Virtual Machines",
            "vms": "Virtual Machines",
            "compute": "Virtual Machines",
            
            "storage": "Storage",
            "blob": "Storage",
            "blob storage": "Storage",
            "file storage": "Storage",
            "disk": "Storage",
            
            "sql": "Azure SQL Database",
            "sql database": "Azure SQL Database",
            "database": "Azure SQL Database",
            "sql server": "Azure SQL Database",
            
            "cosmos": "Azure Cosmos DB",
            "cosmosdb": "Azure Cosmos DB",
            "cosmos db": "Azure Cosmos DB",
            "document db": "Azure Cosmos DB",
            
            "kubernetes": "Azure Kubernetes Service",
            "aks": "Azure Kubernetes Service",
            "k8s": "Azure Kubernetes Service",
            "container service": "Azure Kubernetes Service",
            
            "functions": "Azure Functions",
            "function app": "Azure Functions",
            "serverless": "Azure Functions",
            
            "redis": "Azure Cache for Redis",
            "cache": "Azure Cache for Redis",
            
            "ai": "Azure AI services",
            "cognitive": "Azure AI services",
            "cognitive services": "Azure AI services",
            "openai": "Azure OpenAI",
            
            "networking": "Virtual Network",
            "network": "Virtual Network",
            "vnet": "Virtual Network",
            
            "load balancer": "Load Balancer",
            "lb": "Load Balancer",
            
            "application gateway": "Application Gateway",
            "app gateway": "Application Gateway",
        }
        
        suggestions = []
        search_term = service_name.lower() if service_name else ""
        
        # Try exact mapping first
        if search_term in service_mappings:
            correct_name = service_mappings[search_term]
            result = await self.search_azure_prices(
                service_name=correct_name,
                currency_code=currency_code,
                limit=limit
            )
            
            if result["items"]:
                result["suggestion_used"] = correct_name
                result["original_search"] = service_name
                result["match_type"] = "exact_mapping"
                return result
        
        # Try partial matching for common terms
        partial_matches = []
        for user_term, azure_service in service_mappings.items():
            if search_term in user_term or user_term in search_term:
                partial_matches.append(azure_service)
        
        # Remove duplicates and try each match
        for azure_service in list(set(partial_matches)):
            result = await self.search_azure_prices(
                service_name=azure_service,
                currency_code=currency_code,
                limit=5
            )
            
            if result["items"]:
                suggestions.append({
                    "service_name": azure_service,
                    "match_reason": f"Partial match for '{service_name}'",
                    "sample_items": result["items"][:3]
                })
        
        # If still no matches, do a broad search and look for similar services
        if not suggestions:
            broad_result = await self.search_azure_prices(
                service_family=service_family,
                currency_code=currency_code,
                limit=100
            )
            
            # Find services that contain the search term
            matching_services = set()
            for item in broad_result.get("items", []):
                service = item.get("serviceName", "")
                product = item.get("productName", "")
                
                if (search_term in service.lower() or 
                    search_term in product.lower() or
                    any(word in service.lower() for word in search_term.split())):
                    matching_services.add(service)
            
            # Create suggestions from found services
            for service in list(matching_services)[:5]:  # Limit to top 5
                service_result = await self.search_azure_prices(
                    service_name=service,
                    currency_code=currency_code,
                    limit=3
                )
                
                if service_result["items"]:
                    suggestions.append({
                        "service_name": service,
                        "match_reason": f"Contains '{search_term}'",
                        "sample_items": service_result["items"][:2]
                    })
        
        return {
            "items": [],
            "count": 0,
            "has_more": False,
            "currency": currency_code,
            "original_search": service_name or service_family,
            "suggestions": suggestions,
            "match_type": "suggestions_only"
        }
    
    async def discover_service_skus(
        self,
        service_hint: str,
        region: Optional[str] = None,
        currency_code: str = "USD",
        limit: int = 30
    ) -> Dict[str, Any]:
        """
        Discover SKUs for a service with intelligent service name matching.
        
        Args:
            service_hint: User's description of the service (e.g., "app service", "web app")
            region: Optional specific region to filter by
            currency_code: Currency for pricing
            limit: Maximum number of results
        """
        
        # Use fuzzy matching to find the right service
        result = await self.search_azure_prices_with_fuzzy_matching(
            service_name=service_hint,
            region=region,
            currency_code=currency_code,
            limit=limit
        )
        
        # If we found exact matches, process SKUs
        if result["items"]:
            skus = {}
            service_used = result.get("suggestion_used", service_hint)
            
            for item in result["items"]:
                sku_name = item.get("skuName", "Unknown")
                arm_sku = item.get("armSkuName", "Unknown")
                product = item.get("productName", "Unknown")
                price = item.get("retailPrice", 0)
                unit = item.get("unitOfMeasure", "Unknown")
                item_region = item.get("armRegionName", "Unknown")
                
                if sku_name not in skus:
                    skus[sku_name] = {
                        "sku_name": sku_name,
                        "arm_sku_name": arm_sku,
                        "product_name": product,
                        "prices": [],
                        "regions": set()
                    }
                
                skus[sku_name]["prices"].append({
                    "price": price,
                    "unit": unit,
                    "region": item_region
                })
                skus[sku_name]["regions"].add(item_region)
            
            # Convert sets to lists for JSON serialization
            for sku_data in skus.values():
                sku_data["regions"] = list(sku_data["regions"])
                # Keep only the cheapest price for summary - handle empty sequences
                valid_prices = [p["price"] for p in sku_data["prices"] if p["price"] > 0]
                if valid_prices:
                    sku_data["min_price"] = min(valid_prices)
                else:
                    # If no valid prices > 0, use the first price (even if 0) or default to 0
                    sku_data["min_price"] = sku_data["prices"][0]["price"] if sku_data["prices"] else 0
                sku_data["sample_unit"] = sku_data["prices"][0]["unit"] if sku_data["prices"] else "Unknown"
            
            return {
                "service_found": service_used,
                "original_search": service_hint,
                "skus": skus,
                "total_skus": len(skus),
                "currency": currency_code,
                "match_type": result.get("match_type", "exact")
            }
        
        # If no exact matches, return suggestions
        return {
            "service_found": None,
            "original_search": service_hint,
            "skus": {},
            "total_skus": 0,
            "currency": currency_code,
            "suggestions": result.get("suggestions", []),
            "match_type": "no_match"
        }

# Create the MCP server
server = Server("azure-pricing")

# Global server instance
pricing_server = AzurePricingServer()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="azure_price_search",
            description="Search Azure retail prices with various filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Azure service name (e.g., 'Virtual Machines', 'Storage')"
                    },
                    "service_family": {
                        "type": "string",
                        "description": "Service family (e.g., 'Compute', 'Storage', 'Networking')"
                    },
                    "region": {
                        "type": "string",
                        "description": "Azure region (e.g., 'eastus', 'westeurope')"
                    },
                    "sku_name": {
                        "type": "string",
                        "description": "SKU name to search for (partial matches supported)"
                    },
                    "price_type": {
                        "type": "string",
                        "description": "Price type: 'Consumption', 'Reservation', or 'DevTestConsumption'"
                    },
                    "currency_code": {
                        "type": "string",
                        "description": "Currency code (default: USD)",
                        "default": "USD"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="azure_price_compare",
            description="Compare Azure prices across regions or SKUs",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Azure service name to compare"
                    },
                    "sku_name": {
                        "type": "string",
                        "description": "Specific SKU to compare (optional)"
                    },
                    "regions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of regions to compare (if not provided, compares SKUs)"
                    },
                    "currency_code": {
                        "type": "string",
                        "description": "Currency code (default: USD)",
                        "default": "USD"
                    }
                },
                "required": ["service_name"]
            }
        ),
        Tool(
            name="azure_cost_estimate",
            description="Estimate Azure costs based on usage patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Azure service name"
                    },
                    "sku_name": {
                        "type": "string",
                        "description": "SKU name"
                    },
                    "region": {
                        "type": "string",
                        "description": "Azure region"
                    },
                    "hours_per_month": {
                        "type": "number",
                        "description": "Expected hours of usage per month (default: 730 for full month)",
                        "default": 730
                    },
                    "currency_code": {
                        "type": "string",
                        "description": "Currency code (default: USD)",
                        "default": "USD"
                    }
                },
                "required": ["service_name", "sku_name", "region"]
            }
        ),
        Tool(
            name="azure_discover_skus",
            description="Discover available SKUs for a specific Azure service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Azure service name"
                    },
                    "region": {
                        "type": "string",
                        "description": "Azure region (optional)"
                    },
                    "price_type": {
                        "type": "string",
                        "description": "Price type (default: 'Consumption')",
                        "default": "Consumption"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of SKUs to return (default: 100)",
                        "default": 100
                    }
                },
                "required": ["service_name"]
            }
        ),
        Tool(
            name="azure_sku_discovery",
            description="Discover available SKUs for Azure services with intelligent name matching",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_hint": {
                        "type": "string",
                        "description": "Service name or description (e.g., 'app service', 'web app', 'vm', 'storage'). Supports fuzzy matching."
                    },
                    "region": {
                        "type": "string",
                        "description": "Optional Azure region to filter results"
                    },
                    "currency_code": {
                        "type": "string",
                        "description": "Currency code (default: USD)",
                        "default": "USD"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 30)",
                        "default": 30
                    }
                },
                "required": ["service_hint"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list:
    """Handle tool calls."""
    
    try:
        async with pricing_server:
            if name == "azure_price_search":
                result = await pricing_server.search_azure_prices(**arguments)
                
                # Format the response
                if result["items"]:
                    formatted_items = []
                    for item in result["items"]:
                        formatted_items.append({
                            "service": item.get("serviceName"),
                            "product": item.get("productName"),
                            "sku": item.get("skuName"),
                            "region": item.get("armRegionName"),
                            "location": item.get("location"),
                            "price": item.get("retailPrice"),
                            "unit": item.get("unitOfMeasure"),
                            "type": item.get("type"),
                            "savings_plans": item.get("savingsPlan", [])
                        })
                    
                    if result["count"] > 0:
                        return [
                            TextContent(
                                type="text",
                                text=f"Found {result['count']} Azure pricing results:\n\n" +
                                     json.dumps(formatted_items, indent=2)
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text",
                                text="No pricing results found for the specified criteria."
                            )
                        ]
            
            elif name == "azure_price_compare":
                result = await pricing_server.compare_prices(**arguments)
                return [
                    TextContent(
                        type="text",
                        text=f"Price comparison for {result['service_name']}:\n\n" +
                             json.dumps(result["comparisons"], indent=2)
                    )
                ]
            
            elif name == "azure_cost_estimate":
                result = await pricing_server.estimate_costs(**arguments)
                
                if "error" in result:
                    return [
                        TextContent(
                            type="text",
                            text=f"Error: {result['error']}"
                        )
                    ]
                
                # Format cost estimate
                estimate_text = f"""
Cost Estimate for {result['service_name']} - {result['sku_name']}
Region: {result['region']}
Product: {result['product_name']}
Unit: {result['unit_of_measure']}
Currency: {result['currency']}

Usage Assumptions:
- Hours per month: {result['usage_assumptions']['hours_per_month']}
- Hours per day: {result['usage_assumptions']['hours_per_day']}

On-Demand Pricing:
- Hourly Rate: ${result['on_demand_pricing']['hourly_rate']}
- Daily Cost: ${result['on_demand_pricing']['daily_cost']}
- Monthly Cost: ${result['on_demand_pricing']['monthly_cost']}
- Yearly Cost: ${result['on_demand_pricing']['yearly_cost']}
"""
                
                if result['savings_plans']:
                    estimate_text += "\nSavings Plans Available:\n"
                    for plan in result['savings_plans']:
                        estimate_text += f"""
{plan['term']} Term:
- Hourly Rate: ${plan['hourly_rate']}
- Monthly Cost: ${plan['monthly_cost']}
- Yearly Cost: ${plan['yearly_cost']}
- Savings: {plan['savings_percent']}% (${plan['annual_savings']} annually)
"""
                
                return [
                    TextContent(
                        type="text",
                        text=estimate_text
                    )
                ]
            
            elif name == "azure_discover_skus":
                result = await pricing_server.discover_skus(**arguments)
                
                # Format the response
                skus = result.get("skus", [])
                if skus:
                    return [
                        TextContent(
                            type="text",
                            text=f"Found {result['total_skus']} SKUs for {result['service_name']}:\n\n" +
                                 json.dumps(skus, indent=2)
                        )
                    ]
                else:
                    return [
                        TextContent(
                            type="text",
                            text="No SKUs found for the specified service."
                        )
                    ]
            
            elif name == "azure_sku_discovery":
                result = await pricing_server.discover_service_skus(**arguments)
                
                if result["service_found"]:
                    # Format successful SKU discovery
                    service_name = result["service_found"]
                    original_search = result["original_search"]
                    skus = result["skus"]
                    total_skus = result["total_skus"]
                    match_type = result.get("match_type", "exact")
                    
                    response_text = f"SKU Discovery for '{original_search}'"
                    
                    if match_type == "exact_mapping":
                        response_text += f" (mapped to: {service_name})"
                    
                    response_text += f"\n\nFound {total_skus} SKUs for {service_name}:\n\n"
                    
                    # Group SKUs by product
                    products = {}
                    for sku_name, sku_data in skus.items():
                        product = sku_data["product_name"]
                        if product not in products:
                            products[product] = []
                        products[product].append((sku_name, sku_data))
                    
                    for product, product_skus in products.items():
                        response_text += f"📦 {product}:\n"
                        for sku_name, sku_data in sorted(product_skus)[:10]:  # Limit to 10 per product
                            min_price = sku_data.get("min_price", 0)
                            unit = sku_data.get("sample_unit", "Unknown")
                            region_count = len(sku_data.get("regions", []))
                            
                            response_text += f"   • {sku_name}\n"
                            response_text += f"     Price: ${min_price} per {unit}"
                            if region_count > 1:
                                response_text += f" (available in {region_count} regions)"
                            response_text += "\n"
                        response_text += "\n"
                    
                    return [
                        TextContent(
                            type="text",
                            text=response_text
                        )
                    ]
                else:
                    # Format suggestions when no exact match
                    suggestions = result.get("suggestions", [])
                    original_search = result["original_search"]
                    
                    if suggestions:
                        response_text = f"No exact match found for '{original_search}'\n\n"
                        response_text += "🔍 Did you mean one of these services?\n\n"
                        
                        for i, suggestion in enumerate(suggestions[:5], 1):
                            service_name = suggestion["service_name"]
                            match_reason = suggestion["match_reason"]
                            sample_items = suggestion["sample_items"]
                            
                            response_text += f"{i}. {service_name}\n"
                            response_text += f"   Reason: {match_reason}\n"
                            
                            if sample_items:
                                response_text += "   Sample SKUs:\n"
                                for item in sample_items[:3]:
                                    sku = item.get("skuName", "Unknown")
                                    price = item.get("retailPrice", 0)
                                    unit = item.get("unitOfMeasure", "Unknown")
                                    response_text += f"     • {sku}: ${price} per {unit}\n"
                            response_text += "\n"
                        
                        response_text += "💡 Try using one of the exact service names above."
                    else:
                        response_text = f"No matches found for '{original_search}'\n\n"
                        response_text += "💡 Try using terms like:\n"
                        response_text += "• 'app service' or 'web app' for Azure App Service\n"
                        response_text += "• 'vm' or 'virtual machine' for Virtual Machines\n"
                        response_text += "• 'storage' or 'blob' for Storage services\n"
                        response_text += "• 'sql' or 'database' for SQL Database\n"
                        response_text += "• 'kubernetes' or 'aks' for Azure Kubernetes Service"
                    
                    return [
                        TextContent(
                            type="text",
                            text=response_text
                        )
                    ]
            
            else:
                return [
                    TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )
                ]
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )
        ]

async def main():
    """Main entry point for the server."""
    # Use stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())