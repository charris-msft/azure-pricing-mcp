# Quick Start Guide - Azure Pricing MCP Server

## Prerequisites

- Python 3.8 or higher
- Claude Desktop app (for using the MCP server)

## Installation

### Option 1: Automated Setup (Windows)
```bash
# Run the setup script
setup.bat
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Testing the Setup

### Test 1: API Connectivity
```bash
# Test basic API connectivity (minimal dependencies)
python test_api.py
```

### Test 2: Full MCP Server
```bash
# Test complete MCP server functionality
.venv\Scripts\python.exe test_server.py
```

## Claude Desktop Configuration

1. Find your Claude Desktop config file:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Add the MCP server configuration:
```json
{
  "mcpServers": {
    "azure-pricing": {
      "command": "python",
      "args": ["-m", "azure_pricing_server"],
      "cwd": "C:\\git\\mcp\\azure_pricing"
    }
  }
}
```

3. Restart Claude Desktop

## Usage

Once configured, you can ask Claude questions like:

- "What's the price of a Standard_D2s_v3 VM in East US?"
- "Compare Azure storage prices between regions"
- "Estimate monthly costs for running a web application"
- "What are the cheapest compute options available?"

## Available Tools

1. **azure_price_search** - Search prices with filters
2. **azure_price_compare** - Compare prices across regions/SKUs  
3. **azure_cost_estimate** - Estimate costs based on usage

## Troubleshooting

### Common Issues

**"Import errors" when running:**
- Make sure you're using the virtual environment
- Run: `.venv\Scripts\python.exe` instead of just `python`

**"No results found":**
- Check service name spelling (case-sensitive)
- Try broader search terms
- Verify region names

**"Server not responding in Claude":**
- Check Claude Desktop config file syntax
- Verify the file path in the config
- Restart Claude Desktop after changes

### Getting Help

1. Check the logs when running the server
2. Test with `test_api.py` first
3. Review `USAGE_EXAMPLES.md` for query examples
4. Ensure all dependencies are installed

## Next Steps

- Review `USAGE_EXAMPLES.md` for detailed usage patterns
- Customize the server for your specific needs
- Integrate with your existing cost management workflows