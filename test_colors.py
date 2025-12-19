#!/usr/bin/env python3
"""Test color support in Termux."""

import os

# Test basic colors
print("Testing colors...")
print(f"RED: \033[31mThis should be red\033[0m")
print(f"GREEN: \033[32mThis should be green\033[0m")
print(f"YELLOW: \033[33mThis should be yellow\033[0m")
print(f"BLUE: \033[34mThis should be blue\033[0m")
print(f"MAGENTA: \033[35mThis should be magenta\033[0m")
print(f"CYAN: \033[36mThis should be cyan\033[0m")

# Test bright colors
print("\nTesting bright colors...")
print(f"BRIGHT_RED: \033[91mThis should be bright red\033[0m")
print(f"BRIGHT_GREEN: \033[92mThis should be bright green\033[0m")
print(f"BRIGHT_YELLOW: \033[93mThis should be bright yellow\033[0m")
print(f"BRIGHT_BLUE: \033[94mThis should be bright blue\033[0m")

# Check environment
print(f"\nTERM: {os.getenv('TERM', 'Not set')}")
print(f"COLORTERM: {os.getenv('COLORTERM', 'Not set')}")
print(f"Is terminal (tty): {os.isatty(1)}")

# Try curses
try:
    import curses
    curses.setupterm()
    colors = curses.tigetnum('colors')
    print(f"Colors supported: {colors}")
except Exception as e:
    print(f"Could not detect colors: {e}")