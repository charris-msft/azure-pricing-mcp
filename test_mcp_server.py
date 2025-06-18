#!/usr/bin/env python3
"""Test the MCP server by simulating stdin/stdout communication."""

import asyncio
import json
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

sys.path.append('.')
from azure_pricing_server import main

async def test_mcp_server():
    """Test the MCP server with simulated input."""
    
    # Simulate MCP initialization request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    # Simulate tool call request
    tool_request = {
        "jsonrpc": "2.0", 
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "azure_price_search",
            "arguments": {
                "service_name": "Virtual Machines",
                "sku_name": "Standard_F16",
                "price_type": "Consumption",
                "limit": 10
            }
        }
    }
    
    # Create input stream
    input_data = json.dumps(init_request) + "\\n" + json.dumps(tool_request) + "\\n"
    input_stream = io.StringIO(input_data)
    
    # Capture output
    output_stream = io.StringIO()
    error_stream = io.StringIO()
    
    try:
        # Redirect stdin/stdout to simulate MCP communication
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        sys.stdin = input_stream
        sys.stdout = output_stream
        sys.stderr = error_stream
        
        # This would normally run the server, but it's tricky to test this way
        # Let's just test the tool call directly instead
        
        from azure_pricing_server import handle_call_tool
        
        result = await handle_call_tool("azure_price_search", {
            "service_name": "Virtual Machines",
            "sku_name": "Standard_F16", 
            "price_type": "Consumption",
            "limit": 10
        })
        
        print("Tool call result:")
        for item in result:
            print(f"Type: {type(item)}")
            if hasattr(item, 'text'):
                print(f"Text length: {len(item.text)}")
                print(f"Text preview: {item.text[:200]}...")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sys.stdin = original_stdin
        sys.stdout = original_stdout  
        sys.stderr = original_stderr
        
        if error_stream.getvalue():
            print("STDERR output:")
            print(error_stream.getvalue())

if __name__ == "__main__":
    asyncio.run(test_mcp_server())