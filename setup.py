#!/usr/bin/env python3
"""
Setup script for FAP News - helps with initial configuration
"""

import json
import os
import sys
from pathlib import Path


def print_header():
    """Print welcome header"""
    print("\n" + "=" * 60)
    print(" 🗞️  FAP News - Initial Setup")
    print("=" * 60 + "\n")


def check_python_version():
    """Check if Python version is 3.11+"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required!")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print("✅ Python version OK")


def create_env_file():
    """Create .env file from user input"""
    print("\n📝 Creating .env file...")
    
    if Path(".env").exists():
        overwrite = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if overwrite.lower() != 'y':
            print("Skipping .env creation")
            return
    
    print("\nPlease provide the following information:")
    print("(You can skip optional items by pressing Enter)\n")
    
    # Telegram Bot Token
    bot_token = input("Telegram Bot Token (required): ").strip()
    while not bot_token:
        print("❌ Bot token is required!")
        bot_token = input("Telegram Bot Token: ").strip()
    
    # Admin User ID
    admin_id = input("Your Telegram User ID (required): ").strip()
    while not admin_id or not admin_id.isdigit():
        print("❌ Please enter a valid numeric user ID")
        admin_id = input("Your Telegram User ID: ").strip()
    
    # Groq API Key (optional)
    groq_key = input("Groq API Key (optional, press Enter to skip): ").strip()
    
    # Write .env file
    with open(".env", "w") as f:
        f.write("# FAP News Configuration\n")
        f.write(f"TELEGRAM_BOT_TOKEN={bot_token}\n")
        f.write(f"ADMIN_USER_ID={admin_id}\n")
        if groq_key:
            f.write(f"GROQ_API_KEY={groq_key}\n")
    
    print("\n✅ .env file created successfully!")


def create_config_file():
    """Create config.json from example"""
    print("\n📝 Creating config.json...")
    
    if Path("config.json").exists():
        overwrite = input("⚠️  config.json already exists. Overwrite? (y/N): ")
        if overwrite.lower() != 'y':
            print("Skipping config.json creation")
            return
    
    if not Path("config.example.json").exists():
        print("❌ config.example.json not found!")
        return
    
    # Copy example config
    with open("config.example.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Get channel ID
    channel_id = input("\nTelegram Channel ID (e.g., @mychannel or -100123456789): ").strip()
    if channel_id:
        config["telegram"]["channel_id"] = channel_id
    
    # Save config
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ config.json created successfully!")


def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("   Please run manually: pip install -r requirements.txt")


def print_next_steps():
    """Print next steps for user"""
    print("\n" + "=" * 60)
    print(" 🎉 Setup Complete!")
    print("=" * 60)
    print("\n📚 Next Steps:\n")
    print("1. Make sure your bot is admin in your Telegram channel")
    print("2. Review config.json and adjust settings if needed")
    print("3. Start the bot:")
    print("   python bot.py")
    print("\n4. (Optional) Start the admin panel:")
    print("   python admin_bot.py")
    print("\n5. Send /admin to your bot to access admin features")
    print("\n📖 For more information, read README.md")
    print("\n🔗 Useful links:")
    print("   - Get bot token: https://t.me/botfather")
    print("   - Get your user ID: https://t.me/userinfobot")
    print("   - Get Groq API key: https://console.groq.com/")
    print("\n")


def main():
    """Main setup function"""
    print_header()
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Check Python version
    check_python_version()
    
    # Create configuration files
    create_env_file()
    create_config_file()
    
    # Install dependencies
    install = input("\nInstall dependencies now? (Y/n): ").strip().lower()
    if install != 'n':
        install_dependencies()
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
