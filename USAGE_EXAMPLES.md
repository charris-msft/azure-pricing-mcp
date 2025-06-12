# Azure Pricing MCP Server Usage Examples

## Example Queries for Claude

Once you have the MCP server configured with Claude Desktop, you can ask questions like:

### Basic Price Queries

**"What's the price of a Standard_D2s_v3 VM in East US?"**
- Uses: `azure_price_search` tool
- Filters by service name, SKU, and region

**"Show me Azure Storage pricing options"**
- Uses: `azure_price_search` tool with service family filter

**"What are the current prices for Azure SQL Database?"**
- Uses: `azure_price_search` tool with service name filter

### Price Comparisons

**"Compare VM prices between East US and West Europe"**
- Uses: `azure_price_compare` tool
- Compares same services across different regions

**"What are the cheapest compute options available?"**
- Uses: `azure_price_search` with service family "Compute"
- Results sorted by price

**"Compare different VM sizes for my workload"**
- Uses: `azure_price_compare` tool to compare SKUs

### Cost Estimations

**"What would it cost to run a Standard_D4s_v3 VM for 8 hours a day?"**
- Uses: `azure_cost_estimate` tool
- Calculates based on specific usage patterns

**"Estimate monthly costs for my development environment"**
- Multiple tool calls for different services
- Aggregates costs across services

**"What are the savings with Azure reserved instances?"**
- Uses reservation pricing from the API
- Shows savings compared to on-demand

### Advanced Queries

**"Show me all GPU-enabled VMs with pricing"**
- Uses filtered search for GPU SKUs
- Compares different GPU options

**"What's the cost difference between different storage tiers?"**
- Compares Standard, Premium, and Ultra SSD pricing
- Shows performance vs cost trade-offs

**"Which regions offer the best pricing for my workload?"**
- Multi-region price comparison
- Factors in data transfer costs

## Sample API Responses

### Price Search Response
```json
{
  "items": [
    {
      "service": "Virtual Machines",
      "product": "Virtual Machines Dv3 Series",
      "sku": "D2s v3",
      "region": "eastus",
      "location": "US East",
      "price": 0.096,
      "unit": "1 Hour",
      "type": "Consumption",
      "savings_plans": [
        {
          "retailPrice": 0.0672,
          "term": "1 Year"
        },
        {
          "retailPrice": 0.0528,
          "term": "3 Years"
        }
      ]
    }
  ],
  "count": 1,
  "currency": "USD"
}
```

### Cost Estimate Response
```
Cost Estimate for Virtual Machines - D2s v3
Region: eastus
Product: Virtual Machines Dv3 Series
Unit: 1 Hour
Currency: USD

Usage Assumptions:
- Hours per month: 240
- Hours per day: 8

On-Demand Pricing:
- Hourly Rate: $0.096
- Daily Cost: $0.77
- Monthly Cost: $23.04
- Yearly Cost: $276.48

Savings Plans Available:

1 Year Term:
- Hourly Rate: $0.0672
- Monthly Cost: $16.13
- Yearly Cost: $193.54
- Savings: 30% ($82.94 annually)

3 Years Term:
- Hourly Rate: $0.0528
- Monthly Cost: $12.67
- Yearly Cost: $152.06
- Savings: 45% ($124.42 annually)
```

## Common Service Names

When using the tools, these are common Azure service names (case-sensitive):

- `Virtual Machines`
- `Storage`
- `Azure Database for MySQL`
- `Azure Database for PostgreSQL`
- `Azure SQL Database`
- `Azure Cosmos DB`
- `Azure Cache for Redis`
- `Application Gateway`
- `Load Balancer`
- `Azure Kubernetes Service`
- `Container Instances`
- `App Service`
- `Azure Functions`
- `Logic Apps`
- `Azure AI services`
- `Azure OpenAI`

## Common Service Families

- `Compute`
- `Storage`
- `Databases`
- `Networking`
- `Analytics`
- `AI + Machine Learning`
- `Integration`
- `Security`
- `Management and Governance`

## Popular Azure Regions

- `eastus` - US East
- `westus` - US West  
- `westus2` - US West 2
- `centralus` - US Central
- `westeurope` - West Europe
- `northeurope` - North Europe
- `eastasia` - East Asia
- `southeastasia` - Southeast Asia
- `japaneast` - Japan East
- `australiaeast` - Australia East

## Tips for Best Results

1. **Be Specific**: Include exact service names and SKU names when possible
2. **Use Filters**: Combine multiple filters for precise results
3. **Consider Regions**: Pricing varies significantly by region
4. **Check Savings Plans**: Always look for reserved instance and savings plan options
5. **Factor in Usage**: Use realistic usage patterns for cost estimates
6. **Compare Options**: Always compare different SKUs and regions
7. **Currency**: Specify currency if you need non-USD pricing

## Troubleshooting

If you get no results:
- Check service name spelling (case-sensitive)
- Try broader searches (remove some filters)
- Verify region names are correct
- Some services may not be available in all regions

For cost estimates:
- Ensure the service and SKU combination exists
- Check that the region supports the service
- Verify usage hours are reasonable (0-8760 per year)