# 🚀 Ready to Deploy Checklist

Complete these steps to deploy your Jekyll blog + React affiliates to GitHub Pages.

## Pre-Deployment Checklist

- [ ] **Affiliate pages built locally**
  ```bash
  ./build-affiliates.sh
  ```
  ✅ Files exist at: `_site/affiliate/product-1/` and `_site/affiliate/product-2/`

- [ ] **Updated GitHub Pages configuration**
  - [ ] Updated `cname: yourdomain.github.io` in `.github/workflows/build-affiliates.yml`
  - [ ] Or removed `cname:` line if using `username.github.io`

- [ ] **GitHub repo has Pages enabled**
  - [ ] Settings → Pages → Deploy from branch: `gh-pages`

## Deployment Steps

### Step 1: Add & Commit Files
```bash
git add .
git commit -m "Add affiliate landing pages with GitHub Actions deployment"
```

### Step 2: Push to GitHub
```bash
git push origin main
# (or: git push origin master)
```

### Step 3: Monitor Build
1. Go to your GitHub repo
2. Click **Actions** tab
3. Watch the "Build Affiliates & Deploy" workflow
4. Should complete in 1-2 minutes

### Step 4: Verify Deployment
Once workflow shows ✅ (green), visit:

- **Blog:** `https://yourdomain.github.io/blog/`
- **Affiliate 1:** `https://yourdomain.github.io/blog/affiliate/product-1/`
- **Affiliate 2:** `https://yourdomain.github.io/blog/affiliate/product-2/`

---

## If Deployment Fails

### Check the Error Logs
1. Go to **Actions** → **Build Affiliates & Deploy**
2. Click the failed run
3. Look at the error message

### Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `cname: yourdomain.github.io` doesn't match | Update to your actual domain or remove line |
| Node.js build failed | Check `_affiliates/product-*/package.json` for syntax errors |
| Jekyll build failed | Check `_config.yml` for syntax errors (especially `keep_files:`) |
| Assets return 404 | Verify `vite.config.ts` has correct `base:` paths with `/blog/` |
| Nothing deployed | Make sure you're on the right branch (main or master) |

### Emergency: Manual Fix
If automated workflow fails repeatedly:

```bash
# Build locally
./build-affiliates.sh
bundle exec jekyll build --baseurl '/blog'

# Deploy manually to gh-pages branch
git checkout --orphan gh-pages
git rm -rf .
cp -r _site/* .
git add .
git commit -m "Deploy to GitHub Pages"
git push origin gh-pages -f

# Switch back to main
git checkout main
```

---

## After First Deployment

### Edit & Update Content
```bash
# Edit affiliate content
nano _affiliates/product-1/src/config.ts

# Test locally
./rebuild-affiliates.sh
# (refresh browser)

# Push to GitHub (GitHub Actions handles the rest)
git push origin main
```

### Add New Products
```bash
cp -r _affiliates/product-1 _affiliates/product-3
nano _affiliates/product-3/src/config.ts

# Build & commit
./build-affiliates.sh
git add .
git commit -m "Add product-3 affiliate page"
git push origin main
```

---

## Useful Commands

```bash
# Check if affiliate files are tracked by Git
git ls-files | grep "affiliate"

# See what will be committed
git status

# View GitHub Actions workflow file
cat .github/workflows/build-affiliates.yml

# Check local _site/ structure
tree _site/affiliate/
# (or: find _site/affiliate/ -type f | head -20)
```

---

## Need Help?

1. **Check:** `GITHUB_PAGES_DEPLOYMENT.md` for detailed guide
2. **Check:** `.github/workflows/build-affiliates.yml` for automation config
3. **Check:** `DEVELOPMENT_WORKFLOW.md` for local development
4. **Monitor:** GitHub Actions tab for real-time build logs

---

## ✅ You're Ready!

Everything is configured. Just run:

```bash
git add .
git commit -m "Deploy affiliate pages to GitHub Pages"
git push origin main
```

Then check the **Actions** tab and wait for the ✅!

Questions? See `GITHUB_PAGES_DEPLOYMENT.md` for the complete guide.
