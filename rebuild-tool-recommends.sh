#!/bin/bash

# Quick rebuild script for tool-recommend changes during development
# Run this whenever you edit tool-recommend content

set -e

echo "🔄 Rebuilding tool-recommend landing pages..."
echo ""

# Build product-1
echo "📦 Building product-1..."
cd _tool-recommends/product-1
npm run build > /dev/null 2>&1
cd ../..

# Copy product-1 to _site
mkdir -p _site/tool-recommend/product-1
echo "📋 Copying product-1..."
cp -r _tool-recommends/product-1/build/* _site/tool-recommend/product-1/

# Build product-2
echo "📦 Building product-2..."
cd _tool-recommends/product-2
npm run build > /dev/null 2>&1
cd ../..

# Copy product-2 to _site
mkdir -p _site/tool-recommend/product-2
echo "📋 Copying product-2..."
cp -r _tool-recommends/product-2/build/* _site/tool-recommend/product-2/

echo ""
echo -e "✅ \033[0;32mTool recommend pages rebuilt!\033[0m"
echo "   📚 Refresh your browser to see changes"
echo ""
echo "   🔗 http://127.0.0.1:4000/blog/tool-recommend/product-1/"
echo "   🔗 http://127.0.0.1:4000/blog/tool-recommend/product-2/"
