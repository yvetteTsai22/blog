#!/bin/bash

# Build script for affiliate landing pages
# This builds all affiliate products and prepares them for Jekyll serving

set -e  # Exit on error

echo "🚀 Building affiliate landing pages..."
echo ""

# Make sure _site directory exists
mkdir -p _site

# Build product-1
echo "📦 Building product-1..."
cd _affiliates/product-1
npm run build > /dev/null 2>&1
cd ../..

# Create affiliate directory in _site (will be preserved by Jekyll)
mkdir -p _site/affiliate/product-1

# Copy product-1 to _site (preserve after Jekyll runs)
echo "📋 Copying product-1 to _site/affiliate/product-1..."
cp -r _affiliates/product-1/build/* _site/affiliate/product-1/

# Build product-2
echo "📦 Building product-2..."
cd _affiliates/product-2
npm run build > /dev/null 2>&1
cd ../..

# Create affiliate directory in _site
mkdir -p _site/affiliate/product-2

# Copy product-2 to _site
echo "📋 Copying product-2 to _site/affiliate/product-2..."
cp -r _affiliates/product-2/build/* _site/affiliate/product-2/

echo ""
echo "✅ Done! Affiliate pages built:"
echo "   - _site/affiliate/product-1/"
echo "   - _site/affiliate/product-2/"
echo ""
echo "📌 Note: Jekyll will regenerate _site on each change."
echo "   Your affiliate pages need to be rebuilt after Jekyll runs:"
echo "   ./build-affiliates.sh"
echo ""
echo "To develop:"
echo "  1. bundle exec jekyll serve --baseurl '/blog' &"
echo "  2. ./build-affiliates.sh"
echo "  3. Visit: http://127.0.0.1:4000/blog/affiliate/product-1/"
echo ""
echo "After editing affiliate content:"
echo "  1. ./build-affiliates.sh"
echo "  2. Refresh browser"
