#!/bin/bash
# Enhanced Scholarly MCP Server - Deployment Script

set -e  # Exit on any error

echo "🚀 Enhanced Scholarly MCP Server - Deployment Script"
echo "=" * 60

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Add all files
echo "📝 Adding files to Git..."
git add .

# Check for changes
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Enhanced Scholarly MCP Server with full-text retrieval

Features:
- Multi-source open access detection (Unpaywall, Semantic Scholar, arXiv)
- Full PDF text extraction using PyMuPDF
- Comprehensive error handling and rate limiting
- Production-ready configuration
- Complete example usage and testing suite

🤖 Generated with Claude Code
https://claude.ai/code"
    echo "✅ Changes committed"
fi

# Check if remote exists
if git remote get-url origin 2>/dev/null; then
    echo "✅ Remote origin exists"

    # Ask if user wants to push
    echo ""
    echo "🌐 Ready to push to GitHub?"
    echo "Current remote: $(git remote get-url origin)"
    echo ""
    read -p "Push changes? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📤 Pushing to GitHub..."

        # Get current branch
        BRANCH=$(git branch --show-current)

        # Push to remote
        git push -u origin $BRANCH
        echo "✅ Pushed to GitHub successfully"

        echo ""
        echo "🎉 Deployment ready!"
        echo ""
        echo "📋 Next steps:"
        echo "1. Visit https://fastmcp.cloud"
        echo "2. Sign in with your GitHub account"
        echo "3. Create new project from your repository"
        echo "4. Set entrypoint: scholarly_enhanced_server.py:mcp"
        echo "5. Configure environment variables (optional):"
        echo "   - UNPAYWALL_EMAIL=your_email@example.com"
        echo "   - SEMANTIC_SCHOLAR_API_KEY=your_key (optional)"
        echo "   - CORE_API_KEY=your_key (optional)"
        echo "6. Deploy and test!"
        echo ""
        echo "📚 Documentation: https://github.com/$(git remote get-url origin | sed 's/.*github.com[/:]//' | sed 's/.git$//')"

    else
        echo "⏸️  Skipped push to GitHub"
        echo "💡 To push manually later: git push -u origin $(git branch --show-current)"
    fi

else
    echo "⚠️  No remote origin configured"
    echo ""
    echo "📋 To add GitHub remote:"
    echo "1. Create repository on GitHub"
    echo "2. Run: git remote add origin https://github.com/username/repo-name.git"
    echo "3. Run: git push -u origin main"
    echo ""
    echo "💡 Or run this script again after setting up remote"
fi

echo ""
echo "📊 Repository status:"
echo "Files: $(find . -name '*.py' -o -name '*.md' -o -name '*.txt' -o -name '*.yaml' | wc -l) total"
echo "Main server: scholarly_enhanced_server.py ($(wc -l < scholarly_enhanced_server.py) lines)"
echo "Configuration: enhanced_config.py ($(wc -l < enhanced_config.py) lines)"
echo "Examples: $(find examples -name '*.py' | wc -l) example files"
echo ""
echo "🎯 Ready for deployment to FastMCP Cloud!"