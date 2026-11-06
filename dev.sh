#!/bin/bash

# Development server script for tool-recommend landing pages with Jekyll
# Run this to start the full local development environment

set -e

echo "🚀 Starting development environment..."
echo ""

# Build tool-recommends first
echo "Step 1: Building tool-recommend landing pages..."
bash build-tool-recommends.sh
echo ""

echo "Step 2: Starting Jekyll server..."
echo "   Watching for changes..."
echo ""

# Start Jekyll in watch mode
# Use a watch script to rebuild tool-recommends when Jekyll detects changes
cd /Users/yvette/projects/blog

# Function to keep tool-recommend files in sync
keep_tool_recommends_synced() {
    while true; do
        sleep 2
        # Rebuild tool-recommends every 2 seconds if _tool-recommends changed
        bash build-tool-recommends.sh > /dev/null 2>&1 || true
    done
}

# Start Jekyll in background
bundle exec jekyll serve --baseurl '/blog' &
JEKYLL_PID=$!

# Start tool-recommend sync in background
keep_tool_recommends_synced &
SYNC_PID=$!

echo ""
echo "✅ Development environment running!"
echo ""
echo "📍 Access:"
echo "   Blog: http://127.0.0.1:4000/blog/"
echo "   Products: http://127.0.0.1:4000/blog/tool-recommend/<product-name>/"
echo ""
echo "📝 Edit:"
echo "   Blog posts: _posts/*.md"
echo "   Product content: _tool-recommends/<product-name>/src/config.ts"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Wait for both processes
wait
