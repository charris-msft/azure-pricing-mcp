# Azure Pricing MCP Server 💰

A Model Context Protocol (MCP) server that provides tools for querying Azure retail pricing information using the Azure Retail Prices API.

## 🚀 Quick Start

1. **Clone/Download** this repository
2. **Run setup**: `setup.bat` (Windows) or `python setup.py` (Linux/Mac)
3. **Configure Claude Desktop** (see [QUICK_START.md](QUICK_START.md))
4. **Ask Claude**: "What's the price of a Standard_D2s_v3 VM in East US?"

## ✨ Features

- **🔍 Azure Price Search**: Search for Azure service prices with flexible filtering
- **⚖️ Service Comparison**: Compare prices across different regions and SKUs
- **💡 Cost Estimation**: Calculate estimated costs based on usage patterns
- **💰 Savings Plan Information**: Get Azure savings plan pricing when available
- **🌍 Multi-Currency**: Support for multiple currencies (USD, EUR, etc.)
- **📊 Real-time Data**: Uses live Azure Retail Prices API

## 🛠️ Tools Available

| Tool | Description | Example Use |
|------|-------------|-------------|
| `azure_price_search` | Search Azure retail prices with filters | Find VM prices in specific regions |
| `azure_price_compare` | Compare prices across regions/SKUs | Compare storage costs across regions |
| `azure_cost_estimate` | Estimate costs based on usage | Calculate monthly costs for 8hr/day usage |

## 📋 Installation

### Automated Setup (Recommended)
```bash
# Windows
setup.bat

# Linux/Mac  
python setup.py
```

### Manual Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## 🔧 Configuration

Add to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "azure-pricing": {
      "command": "python",
      "args": ["-m", "azure_pricing_server"],
      "cwd": "/path/to/azure_pricing"
    }
  }
}
```

## 💬 Example Queries

Once configured with Claude, you can ask:

- **Basic Pricing**: "What's the price of Azure SQL Database?"
- **Comparisons**: "Compare VM prices between East US and West Europe"
- **Cost Estimation**: "Estimate costs for running a D4s_v3 VM 12 hours per day"
- **Savings**: "What are the reserved instance savings for virtual machines?"
- **GPU Pricing**: "Show me all GPU-enabled VMs with pricing"

## 🧪 Testing

Test API connectivity:
```bash
python test_api.py
```

Test full MCP server:
```bash
.venv\Scripts\python.exe test_server.py
```

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Step-by-step setup guide
- **[USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)** - Detailed usage examples and API responses
- **[claude_config_example.json](claude_config_example.json)** - Example Claude Desktop configuration

## 🔌 API Integration

This server uses the official Azure Retail Prices API:
- **Endpoint**: `https://prices.azure.com/api/retail/prices`
- **Version**: `2023-01-01-preview` (supports savings plans)
- **Authentication**: None required (public API)
- **Rate Limits**: Generous limits for retail pricing data

## 🌟 Key Features

### Smart Filtering
- Filter by service name, family, region, SKU
- Support for partial matches and contains operations
- Case-sensitive filtering for precise results

### Cost Optimization
- Automatic savings plan detection
- Reserved instance pricing comparisons
- Multi-region cost analysis

### Developer Friendly
- Comprehensive error handling
- Detailed logging for troubleshooting
- Flexible parameter support

## 🤝 Contributing

This project follows the Spec-Driven Development (SDD) methodology. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙋‍♂️ Support

- Check [QUICK_START.md](QUICK_START.md) for setup issues
- Review [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for query patterns
- Open an issue for bugs or feature requests

---

*Built with the Model Context Protocol (MCP) for seamless integration with Claude and other AI assistants.*