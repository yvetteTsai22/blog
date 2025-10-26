#!/bin/bash

# Development server script for affiliate landing pages with Jekyll
# Run this to start the full local development environment

set -e

echo "🚀 Starting development environment..."
echo ""

# Build affiliates first
echo "Step 1: Building affiliate landing pages..."
bash build-affiliates.sh
echo ""

echo "Step 2: Starting Jekyll server..."
echo "   Watching for changes..."
echo ""

# Start Jekyll in watch mode
# Use a watch script to rebuild affiliates when Jekyll detects changes
cd /Users/yvette/projects/blog

# Function to keep affiliate files in sync
keep_affiliates_synced() {
    while true; do
        sleep 2
        # Rebuild affiliates every 2 seconds if _affiliates changed
        bash build-affiliates.sh > /dev/null 2>&1 || true
    done
}

# Start Jekyll in background
bundle exec jekyll serve --baseurl '/blog' &
JEKYLL_PID=$!

# Start affiliate sync in background
keep_affiliates_synced &
SYNC_PID=$!

echo ""
echo "✅ Development environment running!"
echo ""
echo "📍 Access:"
echo "   Blog: http://127.0.0.1:4000/blog/"
echo "   Product 1: http://127.0.0.1:4000/blog/affiliate/product-1/"
echo "   Product 2: http://127.0.0.1:4000/blog/affiliate/product-2/"
echo ""
echo "📝 Edit:"
echo "   Blog posts: _posts/*.md"
echo "   Product 1 content: _affiliates/product-1/src/config.ts"
echo "   Product 2 content: _affiliates/product-2/src/config.ts"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Wait for both processes
wait
