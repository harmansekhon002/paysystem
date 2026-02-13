#!/usr/bin/env python3
"""
Cross-platform launcher for Payroll System
Works on Windows, macOS, and Linux
Just double-click to run!
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    print("=" * 50)
    print("   💰 Payroll System - Starting Up...")
    print("=" * 50)
    print()
    
    # Determine Python executable path based on OS
    if sys.platform == "win32":
        python_exe = script_dir / ".venv" / "Scripts" / "python.exe"
        venv_activate = script_dir / ".venv" / "Scripts" / "activate.bat"
    else:
        python_exe = script_dir / ".venv" / "bin" / "python"
        venv_activate = script_dir / ".venv" / "bin" / "activate"
    
    # Check if virtual environment exists
    if not python_exe.exists():
        print("⚙️  Setting up virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"])
        
        print("📦 Installing dependencies...")
        subprocess.run([str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Setup complete!")
        print()
    
    # Start the backend server
    print("🚀 Starting backend server...")
    backend_script = script_dir / "backend" / "app.py"
    
    if sys.platform == "win32":
        # On Windows, open a new command window
        backend_process = subprocess.Popen(
            ["start", "cmd", "/k", str(python_exe), str(backend_script)],
            shell=True
        )
    else:
        # On macOS/Linux, run in background
        backend_process = subprocess.Popen(
            [str(python_exe), str(backend_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    # Wait for server to start
    print("⏳ Waiting for server to initialize...")
    time.sleep(3)
    
    # Open frontend in browser
    frontend_path = script_dir / "frontend" / "index.html"
    print("🌐 Opening application in your browser...")
    webbrowser.open(f"file://{frontend_path}")
    
    print()
    print("=" * 50)
    print("   ✅ Application is running!")
    print("   📱 Check your browser")
    if sys.platform != "win32":
        print("   🛑 Press Ctrl+C to stop")
    print("=" * 50)
    
    if sys.platform != "win32":
        try:
            # Keep the script running on macOS/Linux
            backend_process.wait()
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            backend_process.terminate()
            backend_process.wait()
            print("✅ Stopped successfully!")

if __name__ == "__main__":
    main()
