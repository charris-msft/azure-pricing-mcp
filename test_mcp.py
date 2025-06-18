#!/usr/bin/env python3
"""Test script to simulate MCP tool calls and find the NoneType error."""

import asyncio
import json
import sys
sys.path.append('.')

from azure_pricing_server import pricing_server, AzurePricingServer

async def test_mcp_tool_call():
    """Test the exact MCP tool call that's causing the error."""
    
    # Test the exact call that was failing
    arguments = {
        "service_name": "Virtual Machines",
        "sku_name": "Standard_F16", 
        "price_type": "Consumption",
        "limit": 10
    }
    
    print("Testing MCP tool call with arguments:")
    print(json.dumps(arguments, indent=2))
    print()
    
    try:
        async with pricing_server:
            result = await pricing_server.search_azure_prices(**arguments)
            print("Raw result:")
            print(json.dumps(result, indent=2))
            print()
            
            # Now test the formatting part that happens in the tool handler
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
                print("Formatted items:")
                print(json.dumps(formatted_items, indent=2))
            else:
                print("No items to format")
                
    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()

async def test_edge_cases():
    """Test edge cases that might cause NoneType errors."""
    
    print("\n=== Testing Edge Cases ===\n")
    
    edge_cases = [
        {"service_name": None, "sku_name": "Standard_F16"},
        {"service_name": "Virtual Machines", "sku_name": None},
        {"service_name": "", "sku_name": "Standard_F16"},
        {"service_name": "Virtual Machines", "sku_name": ""},
        {},  # Empty arguments
    ]
    
    for i, args in enumerate(edge_cases, 1):
        print(f"Edge case {i}: {args}")
        try:
            async with pricing_server:
                result = await pricing_server.search_azure_prices(**args)
                print(f"  Success: {result['count']} items found")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
        print()

if __name__ == "__main__":
    asyncio.run(test_mcp_tool_call())
    asyncio.run(test_edge_cases())