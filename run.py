#!/usr/bin/env python3
"""
DigiKul Application Runner
Provides easy startup with environment checks
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("📝 Please create .env file or run: python install.py")
        return False
    
    # Check if templates directory exists
    if not os.path.exists('templates'):
        print("❌ Templates directory not found")
        print("📁 Please run: python install.py")
        return False
    
    # Check if required directories exist
    required_dirs = ['uploads', 'compressed']
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"❌ {directory} directory not found")
            print("📁 Please run: python install.py")
            return False
    
    print("✅ All requirements met")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask',
        'flask_cors', 
        'flask_socketio',
        'python_dotenv',
        'PIL',
        'pydub',
        'jwt'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            elif package == 'jwt':
                import jwt
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Please run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True

def main():
    """Main function"""
    print("🎓 DigiKul Application Runner")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("\n🚀 Starting DigiKul server...")
    print("📱 Access the platform at: http://localhost:5000")
    print("👨‍🏫 Teacher portal: http://localhost:5000/teacher")
    print("🎒 Student portal: http://localhost:5000/student")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 40)
    
    try:
        # Import and run the app
        from app import app, socketio
        
        if socketio:
            socketio.run(app, debug=True, host='0.0.0.0', port=5000)
        else:
            app.run(debug=True, host='0.0.0.0', port=5000)
            
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
