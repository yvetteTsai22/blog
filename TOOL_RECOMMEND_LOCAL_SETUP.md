# 🚀 Local Development Setup - Affiliate Landing Pages (Solution 2)

## ✅ Setup Complete! Everything is configured and working.

### Quick Access URLs (Local)

While `bundle exec jekyll serve --baseurl '/blog'` is running:

- **Blog:** http://127.0.0.1:4000/blog/
- **Product 1:** http://127.0.0.1:4000/blog/affiliate/product-1/
- **Product 2:** http://127.0.0.1:4000/blog/affiliate/product-2/

---

## 🎯 The Workflow (Solution 2: Built Files in Git)

### How It Works

1. You **build affiliate pages** → generates files in `_site/affiliate/`
2. Jekyll runs and regenerates `_site/` → but preserves `_site/affiliate/` (it's a directory Jekyll doesn't control)
3. Built affiliate files are **committed to Git** 
4. When deployed to GitHub Pages, both blog AND affiliates are served

### Step-by-Step Usage

#### Step 1: Start Jekyll (Background)

```bash
bundle exec jekyll serve --baseurl '/blog' &
```

This watches for changes and regenerates the blog. The process runs in the background.

#### Step 2: Build Affiliate Pages

```bash
./build-affiliates.sh
```

This:
- Builds each affiliate project
- Copies them to `_site/affiliate/product-1/` and `_site/affiliate/product-2/`

#### Step 3: Access Locally

Visit in browser:
- http://127.0.0.1:4000/blog/affiliate/product-1/
- http://127.0.0.1:4000/blog/affiliate/product-2/

---

## 📝 Development Workflow

### Editing Blog Content

```bash
# Edit your posts in _posts/
nano _posts/my-post.md

# Jekyll automatically rebuilds and detects changes
# Refresh browser to see updates
```

### Editing Affiliate Content

```bash
# Edit product config
nano _affiliates/product-1/src/config.ts

# Rebuild affiliates
./build-affiliates.sh

# Refresh browser to see updates
```

### Quick Development Loop

```bash
# Terminal 1: Start Jekyll
bundle exec jekyll serve --baseurl '/blog'

# Terminal 2: Watch and rebuild affiliates
while true; do
  ./build-affiliates.sh
  sleep 5
done
```

---

## 🔄 Deployment to GitHub Pages

### Before Pushing

Affiliate files must be built and committed:

```bash
# Build affiliates
./build-affiliates.sh

# Commit changes
git add _site/affiliate/
git commit -m "Update affiliate landing pages"

# Push to GitHub
git push origin main
```

GitHub Pages will automatically serve:
- `yourdomain.github.io/blog/` → Jekyll blog
- `yourdomain.github.io/blog/affiliate/product-1/` → Affiliate product 1
- `yourdomain.github.io/blog/affiliate/product-2/` → Affiliate product 2

### CI/CD (Optional - GitHub Actions)

If you want to automate the build process, create `.github/workflows/build.yml`:

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - name: Build affiliates
        run: |
          cd _affiliates/product-1 && npm install && npm run build && cd ../..
          cd _affiliates/product-2 && npm install && npm run build && cd ../..
          mkdir -p _site/affiliate/product-1
          mkdir -p _site/affiliate/product-2
          cp -r _affiliates/product-1/build/* _site/affiliate/product-1/
          cp -r _affiliates/product-2/build/* _site/affiliate/product-2/
      - name: Upload to Pages
        uses: actions/upload-pages-artifact@v2
        with:
          path: '_site'
      - name: Deploy to Pages
        uses: actions/deploy-pages@v2
```

---

## 📁 .gitignore Configuration

The `.gitignore` is configured to:
- ❌ Ignore `node_modules/` in `_affiliates/`
- ❌ Ignore `build/` folders in `_affiliates/`
- ✅ **ALLOW** `_site/affiliate/` files to be committed

This ensures:
- Source code stays small (no node_modules)
- Built files are version controlled
- Deployments are consistent

---

## 🎨 Customizing Products

### Change Product 1 Content

```bash
nano _affiliates/product-1/src/config.ts
```

Edit these fields:
- `headline` - Main title
- `highlights` - Highlighted phrases
- `subheadline` - Supporting text
- `benefits` - Feature list
- `socialProof` - Statistics
- `ctaText` - Button text
- `ctaLink` - Affiliate link
- `productImageUrl` - Product image

### Create Product 3

```bash
# Copy product-1
cp -r _affiliates/product-1 _affiliates/product-3

# Edit config
nano _affiliates/product-3/src/config.ts

# Install dependencies
cd _affiliates/product-3
npm install
cd ../..

# Build all affiliates
./build-affiliates.sh

# Access at: http://127.0.0.1:4000/blog/affiliate/product-3/
```

---

## ❓ Troubleshooting

### Affiliates show 404

**Solution:**
```bash
./build-affiliates.sh
```

After rebuilding, refresh browser. If still 404, restart Jekyll.

### Port 4000 already in use

**Solution:**
```bash
pkill -f "bundle exec jekyll serve"
sleep 1
bundle exec jekyll serve --baseurl '/blog'
```

### npm install fails in _affiliates/product-X

**Solution:**
```bash
cd _affiliates/product-1
rm -rf node_modules package-lock.json
npm install
```

### Changes not appearing

**Check:**
1. Did you rebuild? → `./build-affiliates.sh`
2. Is Jekyll running? → `ps aux | grep jekyll`
3. Did you refresh browser? → `Cmd+Shift+R` (hard refresh)

---

## 📊 File Structure Overview

```
blog/
├── build-affiliates.sh          ← Run this to build affiliates
├── _config.yml                  ← Jekyll config (excludes _affiliates)
├── _site/                       ← Generated by Jekyll
│   ├── affiliate/               ← **COMMITTED TO GIT**
│   │   ├── product-1/           ← Built React app
│   │   │   ├── index.html
│   │   │   └── assets/
│   │   └── product-2/
│   │       ├── index.html
│   │       └── assets/
│   ├── index.html               ← Blog homepage
│   └── ... (other Jekyll output)
├── _affiliates/                 ← **NOT COMMITTED** (except affiliate folders)
│   ├── product-1/
│   │   ├── src/
│   │   │   ├── config.ts        ← Edit for content
│   │   │   └── App.tsx
│   │   ├── package.json
│   │   └── node_modules/        ← Excluded from Git
│   └── product-2/
│       └── ...
├── .gitignore                   ← Configured for this setup
└── _posts/                      ← Blog posts
```

---

## 🚀 One-Command Development Start

To start everything at once:

```bash
bash build-affiliates.sh && bundle exec jekyll serve --baseurl '/blog'
```

Then visit: http://127.0.0.1:4000/blog/

---

## 📋 Checklist for First Run

- [ ] Run `./build-affiliates.sh`
- [ ] Run `bundle exec jekyll serve --baseurl '/blog'`
- [ ] Visit http://127.0.0.1:4000/blog/affiliate/product-1/
- [ ] Verify page loads with "Discover the Secret Tool..." heading
- [ ] Edit `_affiliates/product-1/src/config.ts`
- [ ] Run `./build-affiliates.sh` again
- [ ] Refresh browser and see changes
- [ ] Create a new product (`cp -r product-1 product-3`)
- [ ] Test the new product works

---

## ✨ Next Steps

1. **Customize your products** → Edit `src/config.ts` files
2. **Test locally** → Build and visit pages
3. **Commit changes** → `git add .` and `git commit`
4. **Push to GitHub** → Built files deploy automatically
5. **Share affiliate links** → Your pages are live!

---

## 💡 Key Points to Remember

- ✅ **Built files ARE committed** - That's intentional (Solution 2)
- ✅ **Source files are NOT** - Keep repo small
- ✅ **Run `./build-affiliates.sh` before pushing** - Ensures up-to-date deployment
- ✅ **Jekyll doesn't interfere** - It preserves the `_site/affiliate/` directory
- ✅ **Everything works locally** - GitHub Pages is just the hosted version
