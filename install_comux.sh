#!/bin/bash
# Simple installation script for Comux (no pip installation)

echo "📦 Installing Comux..."

# Create user bin directory if it doesn't exist
mkdir -p ~/../usr/bin

# Create symlink in user bin directory (no sudo needed)
ln -sf "$(pwd)/comux.py" ~/../usr/bin/comux

# Make sure it's executable
chmod +x comux.py
chmod +x ~/../usr/bin/comux

# Create update alias in bashrc
BASHRC="$HOME/.bashrc"
if [ -f "$BASHRC" ]; then
    # Remove existing alias if any
    sed -i '/alias comux-update=/d' "$BASHRC"

    # Add new alias
    echo "" >> "$BASHRC"
    echo "# Comux update alias" >> "$BASHRC"
    echo "alias comux-update=\"python $(pwd)/quick_update.py\"" >> "$BASHRC"

    echo "✅ Update alias added to .bashrc"
fi

# Source bashrc to make alias available immediately
source "$BASHRC" 2>/dev/null || true

# Verify installation
if command -v comux &> /dev/null; then
    echo ""
    echo "✅ Comux installed successfully!"
    echo ""
    echo "📌 Next steps:"
    echo "   1. Install dependencies: pip install -r requirements.txt"
    echo "   2. Set API key: export ZAI_API_KEY=your_api_key"
    echo "   3. Run Comux: comux"
    echo ""
    echo "💡 For full setup with dependencies, run:"
    echo "   ./setup_termux.sh"
else
    echo "❌ Installation failed"
    echo "Make sure ~/../usr/bin is in your PATH"
fi