#!/bin/bash
# Quick Start Script for Life Tracking Dashboard
# Mac/Linux version

echo "============================================================"
echo "   Life Tracking Dashboard - Starting..."
echo "============================================================"
echo ""

# Check if database exists
if [ ! -f activities.db ]; then
    echo "Setting up database for first time..."
    python database_setup.py
    echo ""
    echo "⚠️  SAVE THE PASSWORD SHOWN ABOVE!"
    echo ""
    read -p "Press ENTER to continue..."
fi

echo "Starting dashboard server..."
echo ""
echo "🌐 Dashboard will be available at:"
echo "   http://localhost:8000"
echo ""
echo "🔐 Login with your credentials"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python dashboard.py
