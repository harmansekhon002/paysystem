#!/bin/bash

# Start Payroll System

echo "🚀 Starting Payroll System..."
echo ""

# Start backend in background
echo "Starting backend server..."
cd backend
"../../../.venv/bin/python" app.py &
BACKEND_PID=$!
cd ..

echo "✅ Backend running on http://localhost:5001"
echo ""

# Wait for backend to start
sleep 2

# Open frontend
echo "Opening application..."
open frontend/index.html

echo ""
echo "✨ Payroll System is ready!"
echo ""
echo "To stop the backend, run: kill $BACKEND_PID"
echo "Or just close this terminal window"
echo ""
