#!/usr/bin/env python3
"""
Quick update script for comux from GitHub.
Run this script from anywhere to update comux.
"""

import os
import subprocess
import sys
from pathlib import Path


def find_comux_dir():
    """Find the comux directory."""
    # Check common locations
    possible_paths = [
        Path.home() / "comux",
        Path.home() / "github" / "comux",
        Path.home() / "projects" / "comux",
        Path.cwd() / "comux",
    ]

    # Check if any of these exist
    for path in possible_paths:
        if path.exists() and (path / ".git").exists():
            return str(path)

    # Ask user for the path
    print("Comux directory not found. Please enter the path to comux:")
    user_path = input("> ").strip()

    if Path(user_path).exists() and (Path(user_path) / ".git").exists():
        return user_path

    print(f"❌ Invalid path: {user_path}")
    return None


def update_comux(comux_dir):
    """Update comux from GitHub."""
    print(f"🔄 Updating comux at {comux_dir}...")

    try:
        # Change to comux directory
        os.chdir(comux_dir)

        # Stash changes
        print("📦 Stashing local changes...")
        subprocess.run(["git", "stash", "push", "-m", "Auto-stash before update"],
                      check=True, capture_output=True)

        # Pull updates
        print("⬇️ Pulling latest changes...")
        subprocess.run(["git", "pull", "origin", "main"], check=True)

        # Reinstall
        print("🔧 Reinstalling comux...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)

        # Restore stashed if exists
        result = subprocess.run(["git", "stash", "list"], capture_output=True, text=True)
        if "Auto-stash before update" in result.stdout:
            print("📦 Restoring local changes...")
            subprocess.run(["git", "stash", "pop"], check=True)

        print("✅ Update complete!")
        print("\nRun 'comux' to start using the updated version")

    except subprocess.CalledProcessError as e:
        print(f"❌ Update failed: {e}")
        return False

    return True


def main():
    """Main function."""
    print("🚀 Comux Quick Update")
    print("=" * 30)

    # Find comux directory
    comux_dir = find_comux_dir()
    if not comux_dir:
        print("\nPlease clone comux first:")
        print("git clone https://github.com/yourusername/comux.git ~/comux")
        sys.exit(1)

    # Update comux
    success = update_comux(comux_dir)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()