#!/bin/bash

# MPLADS AI Platform - Cleanup & Organization Script
# Removes temporary files and organizes project structure

echo "🧹 Starting cleanup and organization..."
echo ""

# Create necessary directories if they don't exist
mkdir -p logs
mkdir -p docs

# Remove temporary log and PID files
echo "🗑️  Removing temporary files..."
rm -f backend.log frontend.log backend.pid frontend.pid 2>/dev/null
rm -f backend/backend.log 2>/dev/null
echo "   ✅ Removed log files"

# Remove OS-specific files
echo "🗑️  Removing OS-specific files..."
find . -name ".DS_Store" -delete 2>/dev/null
find . -name "Thumbs.db" -delete 2>/dev/null
echo "   ✅ Removed .DS_Store and Thumbs.db"

# Remove Python cache
echo "🗑️  Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null
echo "   ✅ Cleaned Python cache"

# Check if documentation is organized
if [ -f "START.md" ] || [ -f "SUMMARY.md" ] || [ -f "VERIFICATION.md" ]; then
    echo "📚 Moving documentation to docs/..."
    mv START.md docs/ 2>/dev/null
    mv SUMMARY.md docs/ 2>/dev/null
    mv VERIFICATION.md docs/ 2>/dev/null
    echo "   ✅ Documentation organized"
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Project Statistics:"
echo "   - Backend files: $(find backend/app -name "*.py" | wc -l | xargs) Python files"
echo "   - Frontend files: $(find frontend/src -name "*.jsx" -o -name "*.js" | wc -l | xargs) JS/JSX files"
echo "   - Documentation: $(ls -1 docs/ 2>/dev/null | wc -l | xargs) files"
echo ""
echo "🎉 Your project is now organized in industry-grade structure!"
echo ""
echo "Next steps:"
echo "  1. Run: ./start.sh"
echo "  2. Open: http://localhost:5173"
echo "  3. Read: README.md for full documentation"
