#!/bin/bash
# Quick Snowflake Integration Test
# Runs the Python test suite for Snowflake connectivity

set -e

echo "🧪 Snowflake Integration Test Suite"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "mcp-server/test-snowflake.py" ]; then
    echo "❌ Error: Must run from dentalERP root directory"
    exit 1
fi

# Check if Python virtual environment exists
if [ ! -d "mcp-server/venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    cd mcp-server
    python3 -m venv venv
    echo "✅ Virtual environment created"
    cd ..
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
cd mcp-server
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import snowflake.connector" 2>/dev/null; then
    echo "📦 Installing Snowflake dependencies..."
    pip install -q snowflake-connector-python
    echo "✅ Dependencies installed"
fi

# Run tests
echo ""
echo "🚀 Running Snowflake tests..."
echo ""
python test-snowflake.py

# Deactivate virtual environment
deactivate

echo ""
echo "✅ Test suite complete!"
