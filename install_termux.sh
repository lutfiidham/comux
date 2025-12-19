#!/bin/bash
# Installation script for Termux

echo "Installing comux for Termux..."

# Install dependencies
pip install -r requirements.txt

# Create user bin directory if it doesn't exist
mkdir -p ~/../usr/bin

# Create symlink in user bin directory (no sudo needed)
ln -sf "$(pwd)/comux.py" ~/../usr/bin/comux

# Make sure it's executable
chmod +x comux.py
chmod +x ~/../usr/bin/comux

# Verify installation
if command -v comux &> /dev/null; then
    echo "✅ comux installed successfully!"
    echo "Run 'comux' to start"
else
    echo "❌ Installation failed"
    echo "Make sure ~/../usr/bin is in your PATH"
fi