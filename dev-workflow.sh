#!/bin/bash

# Integrated development workflow for Jekyll + Affiliate Landing Pages
# This script handles the timing issues between Jekyll and affiliate builds

set -e

echo "🚀 Starting integrated development environment..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Initial build of affiliates
echo -e "${BLUE}Step 1: Building affiliate landing pages...${NC}"
./build-affiliates.sh
echo ""

# Step 2: Start Jekyll in background
echo -e "${BLUE}Step 2: Starting Jekyll server...${NC}"
bundle exec jekyll serve --baseurl '/blog' &
JEKYLL_PID=$!
echo -e "${GREEN}Jekyll started (PID: $JEKYLL_PID)${NC}"
echo ""

# Wait for Jekyll to start (give it 3 seconds)
echo -e "${YELLOW}Waiting for Jekyll to initialize...${NC}"
sleep 3

# Step 3: Rebuild affiliates after Jekyll starts
echo -e "${BLUE}Step 3: Rebuilding affiliates after Jekyll initialization...${NC}"
./build-affiliates.sh
echo ""

# Step 4: Instructions
echo -e "${GREEN}✅ Development environment ready!${NC}"
echo ""
echo -e "${BLUE}Access your sites at:${NC}"
echo "  📚 Blog:           http://127.0.0.1:4000/blog/"
echo "  🔗 Affiliate 1:    http://127.0.0.1:4000/blog/affiliate/product-1/"
echo "  🔗 Affiliate 2:    http://127.0.0.1:4000/blog/affiliate/product-2/"
echo ""
echo -e "${YELLOW}Important workflow:${NC}"
echo "  1. Edit affiliate content in _affiliates/product-1/ or product-2/"
echo "  2. Run: ./build-affiliates.sh"
echo "  3. Refresh your browser"
echo ""
echo -e "${YELLOW}To stop the server:${NC}"
echo "  Press Ctrl+C"
echo ""

# Handle cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping Jekyll server (PID: $JEKYLL_PID)...${NC}"
    kill $JEKYLL_PID 2>/dev/null || true
    echo -e "${GREEN}Done!${NC}"
}

trap cleanup EXIT

# Keep script running while Jekyll is active
wait $JEKYLL_PID
