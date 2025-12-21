#!/bin/bash

# Build script for tool-recommend landing pages
# This builds all tool-recommend products and prepares them for Jekyll serving

set -e  # Exit on error

echo "🚀 Building tool-recommend landing pages..."
echo ""

# Make sure _site directory exists
mkdir -p _site

# Build product-1
echo "📦 Building product-1..."
cd _tool-recommends/product-1
npm run build > /dev/null 2>&1
cd ../..

# Create tool-recommend directory in _site (will be preserved by Jekyll)
mkdir -p _site/tool-recommend/product-1

# Copy product-1 to _site (preserve after Jekyll runs)
echo "📋 Copying product-1 to _site/tool-recommend/product-1..."
cp -r _tool-recommends/product-1/build/* _site/tool-recommend/product-1/

# Build product-2
echo "📦 Building product-2..."
cd _tool-recommends/product-2
npm run build > /dev/null 2>&1
cd ../..

# Create tool-recommend directory in _site
mkdir -p _site/tool-recommend/product-2

# Copy product-2 to _site
echo "📋 Copying product-2 to _site/tool-recommend/product-2..."
cp -r _tool-recommends/product-2/build/* _site/tool-recommend/product-2/

echo ""
echo "✅ Done! Tool recommend pages built:"
echo "   - _site/tool-recommend/product-1/"
echo "   - _site/tool-recommend/product-2/"
echo ""
echo "📌 Note: Jekyll will regenerate _site on each change."
echo "   Your tool-recommend pages need to be rebuilt after Jekyll runs:"
echo "   ./build-tool-recommends.sh"
echo ""
echo "To develop:"
echo "  1. bundle exec jekyll serve --baseurl '/blog' &"
echo "  2. ./build-tool-recommends.sh"
echo "  3. Visit: http://127.0.0.1:4000/blog/tool-recommend/product-1/"
echo ""
echo "After editing tool-recommend content:"
echo "  1. ./build-tool-recommends.sh"
echo "  2. Refresh browser"
