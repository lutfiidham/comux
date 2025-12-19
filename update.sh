#!/bin/bash
# Update script for comux from GitHub

echo "🔄 Updating comux..."

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Not in a git repository. Please run from the comux directory."
    exit 1
fi

# Stash any local changes
echo "📦 Stashing local changes..."
git stash push -m "Auto-stash before update"

# Pull latest changes
echo "⬇️ Pulling latest changes..."
git pull origin main

# Restore stashed changes if any
if git stash list | grep -q "Auto-stash before update"; then
    echo "📦 Restoring local changes..."
    git stash pop
fi

# Reinstall dependencies if needed
if [ -f requirements.txt ]; then
    echo "📚 Updating dependencies..."
    pip install -r requirements.txt
fi

# Reinstall comux
echo "🔧 Reinstalling comux..."
pip install -e .

echo "✅ Update complete!"
echo ""
echo "Run 'comux' to start using the updated version"