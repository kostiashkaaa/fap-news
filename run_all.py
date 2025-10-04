#!/usr/bin/env python3
"""
Convenience script to run both the main bot and admin bot
"""

import asyncio
import subprocess
import sys
import signal
import os
from pathlib import Path


def print_header():
    """Print startup header"""
    print("\n" + "=" * 60)
    print(" 🗞️  FAP News - Starting All Services")
    print("=" * 60 + "\n")


async def run_process(name: str, command: list):
    """Run a process and stream its output"""
    print(f"🚀 Starting {name}...")
    
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    return process


async def stream_output(process, name: str):
    """Stream process output with prefix"""
    async for line in process.stdout:
        print(f"[{name}] {line.decode().rstrip()}")


async def main():
    """Main function to run both bots"""
    print_header()
    
    # Check if config exists
    if not Path("config.json").exists():
        print("❌ config.json not found!")
        print("   Please run: python setup.py")
        sys.exit(1)
    
    processes = []
    
    try:
        # Start main bot
        bot_process = await run_process(
            "Main Bot",
            [sys.executable, "bot.py"]
        )
        processes.append(("Main Bot", bot_process))
        
        # Wait a bit before starting admin bot
        await asyncio.sleep(2)
        
        # Start admin bot
        admin_process = await run_process(
            "Admin Bot",
            [sys.executable, "admin_bot.py"]
        )
        processes.append(("Admin Bot", admin_process))
        
        print("\n✅ All services started!")
        print("📊 Press Ctrl+C to stop all services\n")
        
        # Stream outputs
        await asyncio.gather(
            stream_output(bot_process, "Bot"),
            stream_output(admin_process, "Admin"),
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Shutting down all services...")
        for name, process in processes:
            print(f"   Stopping {name}...")
            process.terminate()
            await process.wait()
        print("✅ All services stopped")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        for name, process in processes:
            process.terminate()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)