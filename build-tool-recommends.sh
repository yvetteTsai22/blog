#!/bin/bash

# Build script for tool-recommend landing pages.
# Auto-discovers any subdirectory of _tool-recommends/ that has a package.json.
# Adding a new product requires no changes here — just create the directory.

set -e

echo "🚀 Building tool-recommend landing pages..."
echo ""

mkdir -p _site

SITE_URL="https://yvettetsai22.github.io/blog"
sitemap_urls=()

# Auto-build all products in _tool-recommends/ that have a package.json.
# A product containing a .no-deploy file (e.g. an unfinished template) is skipped.
for pkg in _tool-recommends/*/package.json; do
  dir=$(dirname "$pkg")
  name=$(basename "$dir")
  # Directories starting with _ (e.g. _templates/) are not deployed.
  case "$name" in _*) continue ;; esac

  if [ -f "$dir/.no-deploy" ]; then
    echo "⏭️  Skipping $name (.no-deploy)"
    continue
  fi

  echo "📦 Building $name..."
  cd "$dir"
  npm install --legacy-peer-deps --no-audit --no-fund > /dev/null 2>&1
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
  sitemap_urls+=("$SITE_URL/tool-recommend/$name/")
done

# Build fire-calculator (lives outside _tool-recommends/)
echo "📦 Building fire-calculator..."
cd fire-calculator
npm install --no-audit --no-fund > /dev/null 2>&1
npm run build > /dev/null 2>&1
cd ..
mkdir -p _site/fire-calculator
cp -r fire-calculator/dist/. _site/fire-calculator/
echo "   ✓ copied to _site/fire-calculator/"

# Jekyll's sitemap can't see these pages (they're built after Jekyll), so add them here.
if [ -f _site/sitemap.xml ] && [ ${#sitemap_urls[@]} -gt 0 ]; then
  node -e '
    const fs = require("fs");
    const [file, ...urls] = process.argv.slice(1);
    const xml = fs.readFileSync(file, "utf8");
    if (!xml.includes("</urlset>")) throw new Error(file + ": no </urlset>");
    const entries = urls
      .filter((url) => !xml.includes("<loc>" + url + "</loc>"))
      .map((url) => "    <url>\n        <loc>" + url + "</loc>\n    </url>\n")
      .join("");
    fs.writeFileSync(file, xml.replace("</urlset>", entries + "</urlset>"));
  ' _site/sitemap.xml "${sitemap_urls[@]}"
  echo "   ✓ added ${#sitemap_urls[@]} tool-recommend URL(s) to _site/sitemap.xml"
fi

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
