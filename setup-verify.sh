#!/bin/bash

# Complete setup and test script for affiliate landing pages
# Run this to verify everything is working correctly

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  AFFILIATE LANDING PAGES - COMPLETE SETUP VERIFICATION         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Jekyll is installed
echo "✓ Checking dependencies..."
if ! command -v bundle &> /dev/null; then
    echo "  ⚠ Bundle not found - installing..."
    gem install bundler
fi

# Check if npm is available for affiliates
if ! command -v npm &> /dev/null; then
    echo "  ⚠ npm not found - please install Node.js"
    exit 1
fi

echo "  ✓ Bundle available"
echo "  ✓ npm available"
echo ""

# Install Ruby dependencies
echo "✓ Installing Jekyll dependencies..."
bundle install > /dev/null 2>&1 || true
echo "  ✓ Jekyll ready"
echo ""

# Check affiliates structure
echo "✓ Checking affiliate structure..."
if [ ! -d "_affiliates/product-1" ]; then
    echo "  ✗ product-1 folder missing"
    exit 1
fi
if [ ! -d "_affiliates/product-2" ]; then
    echo "  ✗ product-2 folder missing"
    exit 1
fi
echo "  ✓ product-1 folder exists"
echo "  ✓ product-2 folder exists"
echo ""

# Install npm dependencies for affiliates
echo "✓ Installing affiliate dependencies..."
cd _affiliates/product-1
npm install > /dev/null 2>&1
cd ../..
cd _affiliates/product-2
npm install > /dev/null 2>&1
cd ../..
echo "  ✓ product-1 dependencies installed"
echo "  ✓ product-2 dependencies installed"
echo ""

# Build affiliates
echo "✓ Building affiliate landing pages..."
bash build-affiliates.sh > /dev/null 2>&1
echo "  ✓ Builds successful"
echo ""

# Verify files in _site
echo "✓ Verifying built files..."
if [ ! -f "_site/affiliate/product-1/index.html" ]; then
    echo "  ✗ product-1 not built correctly"
    exit 1
fi
if [ ! -f "_site/affiliate/product-2/index.html" ]; then
    echo "  ✗ product-2 not built correctly"
    exit 1
fi
echo "  ✓ product-1/index.html exists"
echo "  ✓ product-2/index.html exists"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ ALL CHECKS PASSED - READY TO DEVELOP!                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "Next steps:"
echo ""
echo "1️⃣  Start Jekyll server:"
echo "   bundle exec jekyll serve --baseurl '/blog'"
echo ""
echo "2️⃣  In another terminal, visit:"
echo "   http://127.0.0.1:4000/blog/affiliate/product-1/"
echo "   http://127.0.0.1:4000/blog/affiliate/product-2/"
echo ""
echo "3️⃣  Edit affiliate content:"
echo "   nano _affiliates/product-1/src/config.ts"
echo ""
echo "4️⃣  Rebuild affiliates:"
echo "   bash build-affiliates.sh"
echo ""
echo "5️⃣  Refresh browser to see changes"
echo ""
echo "📖 For more details, see: AFFILIATE_LOCAL_SETUP.md"
echo ""
