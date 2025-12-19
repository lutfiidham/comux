#!/bin/bash
# Setup script for Comux on Termux with autocomplete support

echo "🚀 Setting up Comux for Termux..."

# Update packages
echo "📦 Updating Termux packages..."
pkg update -y

# Install Python and required packages
echo "🐍 Installing Python and dependencies..."
pkg install -y python clang make libffi

# Don't install pip separately - it comes with python package in Termux

# Install Python dependencies
echo "📚 Installing Python packages..."
# Use --user flag to avoid system package conflicts
if [ -f "requirements.txt" ]; then
    pip install --user -r requirements.txt
else
    pip install --user requests>=2.31.0
fi

# Check readline availability
echo "🔍 Checking readline support..."
python -c "
try:
    import readline
    print('✅ readline is available - autocomplete will work!')
except ImportError:
    print('⚠️  readline not available - installing gnureadline...')
    import subprocess
    subprocess.check_call(['pip', 'install', '--user', 'gnureadline'])
    print('✅ gnureadline installed - autocomplete should work now!')
"

# Install Comux in development mode
echo "💾 Installing Comux..."
pip install --user -e .

# Create symlink in user bin for easier access
mkdir -p ~/../usr/bin
ln -sf "$(pwd)/comux.py" ~/../usr/bin/comux
chmod +x ~/../usr/bin/comux

# Setup command alias in bashrc
echo "🔗 Setting up command alias..."
BASHRC="$HOME/.bashrc"
if ! grep -q 'alias comux=' "$BASHRC"; then
    echo "" >> "$BASHRC"
    echo "# Comux command alias" >> "$BASHRC"
    echo 'alias comux="python -m comux"' >> "$BASHRC"
    echo "✅ Command alias added to .bashrc"
fi

# Add environment variables for better experience
echo "⚙️ Setting up environment variables..."
if ! grep -q 'export ZAI_API_KEY=' "$BASHRC"; then
    echo "" >> "$BASHRC"
    echo "# Comux environment variables" >> "$BASHRC"
    echo "# export ZAI_API_KEY=your_api_key_here" >> "$BASHRC"
    echo "export COMUX_STREAM=true" >> "$BASHRC"
    echo "✅ Environment variables added to .bashrc (uncomment and set your API key)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📌 Next steps:"
echo "   1. Set your API key: export ZAI_API_KEY=your_api_key_here"
echo "   2. Or add it permanently in ~/.bashrc"
echo "   3. Run Comux: comux"
echo ""
echo "💡 Features enabled:"
echo "   • Tab autocomplete for @filename"
echo "   • Response streaming (real-time output)"
echo "   • 20+ AI tools for coding"
echo ""
echo "🔄 To apply all changes, run:"
echo "   source ~/.bashrc"
echo ""
echo "Or restart Termux to reload shell configuration."