#!/bin/bash
# Setup development environment for Vocabulator
# Run this script after cloning the repository

set -e  # Exit on error

echo "🚀 Setting up Vocabulator development environment"
echo "=================================================="

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "❌ Error: Python 3.11+ required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version OK: $PYTHON_VERSION"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping creation."
else
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📥 Installing production dependencies..."
pip install -r requirements.txt

echo "📥 Installing development dependencies..."
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your actual API keys and configuration"
else
    echo "✅ .env file already exists"
fi

# Check Docker for LocalStack
echo "🐳 Checking Docker installation..."
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✅ Docker and Docker Compose are installed"
    echo "💡 To start LocalStack, run: docker-compose up -d localstack"
else
    echo "⚠️  Docker not found. LocalStack requires Docker to be installed."
fi

# Run setup verification test
echo ""
echo "🧪 Running setup verification tests..."
if pytest tests/test_setup.py -v; then
    echo ""
    echo "✅ Development environment setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your actual configuration"
    echo "2. Start LocalStack: docker-compose up -d localstack"
    echo "3. Run tests: pytest"
    echo "4. Start development!"
else
    echo ""
    echo "⚠️  Some tests failed. Please check the output above."
    exit 1
fi

