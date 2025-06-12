# Azure Pricing MCP Server Setup Script - PowerShell
# Setup and install dependencies for the Azure Pricing MCP Server

Write-Host "🚀 Setting up Azure Pricing MCP Server..." -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "🔧 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Virtual environment created successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow

# Check if requirements.txt exists
if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ requirements.txt not found" -ForegroundColor Red
    exit 1
}

# Upgrade pip first
Write-Host "   Upgrading pip..." -ForegroundColor Gray
& ".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Pip upgraded successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Pip upgrade had issues, continuing..." -ForegroundColor Yellow
}

# Install requirements
Write-Host "   Installing packages from requirements.txt..." -ForegroundColor Gray
& ".venv\Scripts\python.exe" -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ All dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Some dependencies failed to install" -ForegroundColor Red
    Write-Host "   Try running manually: .venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Gray

Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Test API connectivity:" -ForegroundColor White
Write-Host "   .venv\Scripts\python.exe test_api.py" -ForegroundColor Gray

Write-Host "2. Test full MCP server:" -ForegroundColor White  
Write-Host "   .venv\Scripts\python.exe test_server.py" -ForegroundColor Gray

Write-Host "3. Run storage query simulation:" -ForegroundColor White
Write-Host "   .venv\Scripts\python.exe simulate_storage_query.py" -ForegroundColor Gray

Write-Host "4. Configure Claude Desktop (see claude_config_example.json)" -ForegroundColor White

Write-Host "5. Start the MCP server:" -ForegroundColor White
Write-Host "   .venv\Scripts\python.exe -m azure_pricing_server" -ForegroundColor Gray

Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • README.md - Main documentation" -ForegroundColor Gray
Write-Host "   • QUICK_START.md - Setup guide" -ForegroundColor Gray
Write-Host "   • USAGE_EXAMPLES.md - Query examples" -ForegroundColor Gray

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")