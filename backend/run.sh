#!/bin/bash

# Run Flask Backend Script
echo "🚀 Starting Fulfil ShipHero Mediator Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if Flask app exists
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please check your backend setup."
    exit 1
fi

# Run Flask
echo "🔥 Starting Flask server..."
echo "📍 Backend will be available at: http://localhost:5000"
echo "🔑 Default admin: admin / admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

venv/bin/python -m flask --app app run
