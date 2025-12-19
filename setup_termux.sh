#!/bin/bash
# Setup script for Comux on Termux with autocomplete support

echo "🚀 Setting up Comux for Termux..."

# Update packages
echo "📦 Updating Termux packages..."
pkg update -y
pkg upgrade -y

# Install Python and required packages
echo "🐍 Installing Python and dependencies..."
pkg install -y python clang make libffi

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install requests>=2.31.0
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
    subprocess.check_call(['pip', 'install', 'gnureadline'])
    print('✅ gnureadline installed - autocomplete should work now!')
"

# Install Comux
echo "💾 Installing Comux..."
pip install -e .

# Setup command alias
echo "🔗 Setting up command alias..."
if ! grep -q 'alias comux' ~/.bashrc; then
    echo 'alias comux="python -m comux"' >> ~/.bashrc
fi

# Setup completion
echo "⚡ Enabling tab completion..."
cat << 'EOF' > ~/.comux_completion
# Comux tab completion helper
_comux_complete() {
    local cur prev
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # If completing after @, show files
    if [[ $cur == @* ]]; then
        local files=$(find . -type f -not -path '*/.*' -not -path '*/__pycache__/*' -not -path '*/node_modules/*' | sed 's|^\./||' | sort)
        COMPREPLY=( $(compgen -W "$files" -- ${cur#@}) )
    fi
}

complete -F _comux_complete comux
EOF

if ! grep -q '~/.comux_completion' ~/.bashrc; then
    echo 'source ~/.comux_completion' >> ~/.bashrc
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📌 Usage:"
echo "   comux                    # Start Comux"
echo "   comux @file[TAB]         # Autocomplete file names"
echo ""
echo "🔄 To apply changes, run:"
echo "   source ~/.bashrc"
echo ""
echo "Or restart Termux to reload shell configuration."