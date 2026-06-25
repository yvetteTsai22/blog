#!/bin/bash

# Build script for tool-recommend landing pages.
# Auto-discovers any subdirectory of _tool-recommends/ that has a package.json.
# Adding a new product requires no changes here — just create the directory.

set -e

echo "🚀 Building tool-recommend landing pages..."
echo ""

mkdir -p _site

# Auto-build all products in _tool-recommends/ that have a package.json
for pkg in _tool-recommends/*/package.json; do
  dir=$(dirname "$pkg")
  name=$(basename "$dir")

  echo "📦 Building $name..."
  cd "$dir"
  npm run build > /dev/null 2>&1
  cd ../..

  # Support both Vite (dist/) and CRA-style (build/) output dirs
  if [ -d "$dir/dist" ]; then
    out_dir="$dir/dist"
  else
    out_dir="$dir/build"
  fi

  mkdir -p "_site/tool-recommend/$name"
  cp -r "$out_dir/." "_site/tool-recommend/$name/"
  echo "   ✓ copied to _site/tool-recommend/$name/"
done

# Build fire-calculator (lives outside _tool-recommends/)
echo "📦 Building fire-calculator..."
cd fire-calculator
npm run build > /dev/null 2>&1
cd ..
mkdir -p _site/fire-calculator
cp -r fire-calculator/dist/. _site/fire-calculator/
echo "   ✓ copied to _site/fire-calculator/"

echo ""
echo "✅ Done!"
echo ""
echo "📌 Note: Jekyll will regenerate _site on each change."
echo "   Rebuild tool-recommend pages after Jekyll runs: ./build-tool-recommends.sh"
echo ""
echo "To develop:"
echo "  1. bundle exec jekyll serve --baseurl '/blog' &"
echo "  2. ./build-tool-recommends.sh"
echo "  3. Visit: http://127.0.0.1:4000/blog/tool-recommend/<product-name>/"
