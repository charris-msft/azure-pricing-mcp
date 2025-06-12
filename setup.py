#!/usr/bin/env python3
"""
Setup and run script for Azure Pricing MCP Server
"""

import subprocess
import sys
import os
from pathlib import Path

def create_venv():
    """Create virtual environment if it doesn't exist."""
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("🔧 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")

def get_python_executable():
    """Get the Python executable path for the virtual environment."""
    if os.name == 'nt':  # Windows
        return Path(".venv") / "Scripts" / "python.exe"
    else:  # Unix/Linux/Mac
        return Path(".venv") / "bin" / "python"

def install_dependencies():
    """Install required dependencies."""
    python_exe = get_python_executable()
    print("📦 Installing dependencies...")
    subprocess.run([str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("✅ Dependencies installed")

def run_server():
    """Run the MCP server."""
    python_exe = get_python_executable()
    print("🚀 Starting Azure Pricing MCP Server...")
    print("   (Use Ctrl+C to stop)")
    subprocess.run([str(python_exe), "-m", "azure_pricing_server"], check=True)

def main():
    """Main setup and run function."""
    try:
        print("🔄 Setting up Azure Pricing MCP Server...")
        create_venv()
        install_dependencies()
        run_server()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()