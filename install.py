#!/usr/bin/env python3
"""
DigiKul Installation Script
Installs all required dependencies and sets up the environment
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required dependencies"""
    dependencies = [
        "Flask==3.1.2",
        "Flask-CORS==6.0.1", 
        "Flask-SocketIO==5.3.6",
        "python-socketio==5.10.0",
        "eventlet==0.33.3",
        "python-dotenv==1.1.1",
        "Pillow==11.3.0",
        "pydub==0.25.1",
        "PyJWT==2.10.1",
        "requests==2.32.5",
        "Werkzeug==3.1.3"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "uploads/audio",
        "uploads/images", 
        "uploads/documents",
        "compressed/audio",
        "compressed/images",
        "compressed/documents",
        "templates",
        "static"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = ".env"
    if not os.path.exists(env_file):
        env_content = """# DigiKul Environment Configuration
SECRET_KEY=dev-secret-key-change-in-production
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Optional: Customize compression settings
AUDIO_BITRATE=48k
IMAGE_QUALITY=30
PDF_COMPRESSION_LEVEL=3
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("📝 Created .env file with default settings")
        print("⚠️  Please update .env file with your actual configuration")
    else:
        print("✅ .env file already exists")
    
    return True

def main():
    """Main installation function"""
    print("🎓 DigiKul Installation Script")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Installation failed during dependency installation")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("❌ Installation failed during directory creation")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("❌ Installation failed during .env file creation")
        sys.exit(1)
    
    print("\n🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update .env file with your configuration")
    print("2. Run: python app.py")
    print("3. Open: http://localhost:5000")
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main()
