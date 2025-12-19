#!/usr/bin/env python3
"""Post-installation script for comux."""

import os
import sys
from pathlib import Path


def setup_update_alias():
    """Setup comux-update alias in .bashrc."""
    bashrc = Path.home() / ".bashrc"

    # Find comux installation directory
    comux_path = Path(__file__).parent.resolve()
    quick_update_path = comux_path / "quick_update.py"

    if not quick_update_path.exists():
        print("⚠️  quick_update.py not found, skipping alias setup")
        return

    # Read current bashrc
    bashrc_content = ""
    if bashrc.exists():
        bashrc_content = bashrc.read_text()

    # Remove existing alias
    lines = bashrc_content.split('\n')
    filtered_lines = [line for line in lines if 'alias comux-update=' not in line]

    # Add new alias
    filtered_lines.extend([
        "",
        "# Comux update alias",
        f"alias comux-update=\"python {quick_update_path}\""
    ])

    # Write back to bashrc
    bashrc.write_text('\n'.join(filtered_lines))
    print(f"✅ Added comux-update alias to {bashrc}")

    # Try to source bashrc
    try:
        os.system(f"source {bashrc}")
    except:
        print("⚠️  Please run 'source ~/.bashrc' to activate the alias")


def main():
    """Main post-install function."""
    print("🔧 Running comux post-install setup...")

    # Setup update alias
    setup_update_alias()

    print("✅ Post-install setup complete!")
    print("Run 'comux' to start")
    print("Run 'comux-update' to update from GitHub")


if __name__ == "__main__":
    main()