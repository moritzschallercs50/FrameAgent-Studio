#!/bin/bash

# FrameAgent Studio - Startup Script

echo "🎬 FrameAgent Studio - Starting..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update requirements
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✨ Starting Flask server..."
echo "🌐 Open http://localhost:5000 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the Flask app
python app.py

