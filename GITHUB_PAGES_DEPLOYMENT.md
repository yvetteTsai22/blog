# GitHub Pages Deployment Guide

## Overview

Your Jekyll blog + React affiliate pages are now set up to deploy to GitHub Pages with **automatic building** via GitHub Actions.

## How It Works

1. **You push to GitHub** (`git push`)
2. **GitHub Actions automatically:**
   - Installs Node.js dependencies
   - Builds React affiliate pages
   - Builds Jekyll blog
   - Deploys everything to GitHub Pages
3. **Site is live** at `yourdomain.github.io/blog/`

## Setup Steps

### 1. **Update GitHub Repository Name**

The workflow currently assumes you're deploying to `yourdomain.github.io`. Update this in `.github/workflows/build-affiliates.yml`:

```yaml
cname: yourdomain.github.io  # ← Change this to your actual domain
```

If you **don't have a custom domain**, remove that line:
```yaml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./_site
    # (remove the cname line)
```

### 2. **Enable GitHub Pages in Your Repo**

Go to your GitHub repository:
1. **Settings** → **Pages**
2. Under "Source", select **Deploy from a branch**
3. Select branch: **gh-pages**
4. Select folder: **/ (root)**
5. Click **Save**

GitHub Actions will automatically create the `gh-pages` branch on first deploy.

### 3. **Build Affiliate Pages Locally (First Time)**

Before pushing, build locally to ensure everything works:

```bash
./build-affiliates.sh
```

This creates `_site/affiliate/product-1/` and `_site/affiliate/product-2/`.

### 4. **Commit & Push**

```bash
git add .
git commit -m "Initial affiliate pages setup"
git push origin main
```

(or `master` if that's your default branch)

### 5. **Monitor the Build**

Go to your repo on GitHub:
- **Actions** tab → Watch the workflow run
- It should complete in 1-2 minutes
- Amber (🟡) = Running
- Green (🟢) = Success
- Red (🔴) = Failed

### 6. **Access Your Site**

Your site will be live at:
- **Blog:** `https://yourdomain.github.io/blog/`
- **Affiliate 1:** `https://yourdomain.github.io/blog/affiliate/product-1/`
- **Affiliate 2:** `https://yourdomain.github.io/blog/affiliate/product-2/`

(or `username.github.io` if you haven't set a custom domain)

---

## Development Workflow

### Local Development

```bash
# Terminal 1: Start Jekyll
./dev-workflow.sh

# Terminal 2: Edit affiliate files and rebuild when needed
./rebuild-affiliates.sh
```

### Before Pushing to GitHub

```bash
# Build affiliates locally
./build-affiliates.sh

# Check that _site/affiliate/ has your files
ls _site/affiliate/

# Commit everything
git add .
git commit -m "Update affiliate pages"
git push origin main
```

### Editing Content

**To edit affiliate content:**
1. Edit `_affiliates/product-1/src/config.ts` or `_affiliates/product-2/src/config.ts`
2. Edit `_affiliates/product-1/src/components/` or `_affiliates/product-2/src/components/`
3. Run locally: `./rebuild-affiliates.sh`
4. Test: Refresh browser
5. When ready: `git push` (GitHub Actions handles the rest)

**To edit Jekyll/blog content:**
1. Create/edit posts in `_posts/`
2. Run locally: `./rebuild-affiliates.sh` (if you also edited affiliates) then restart Jekyll
3. Test: Refresh browser
4. When ready: `git push`

---

## Adding New Affiliate Products

To add product-3:

```bash
# Copy product-1 template
cp -r _affiliates/product-1 _affiliates/product-3

# Edit config
nano _affiliates/product-3/src/config.ts

# Build locally to test
./rebuild-affiliates.sh

# Then push
git push origin main
```

The GitHub Actions workflow will automatically build it.

---

## Troubleshooting

### Actions Workflow Failed

Check the workflow logs:
1. Go to **Actions** tab on GitHub
2. Click the failed workflow
3. Click the failing job
4. Look for error messages

Common issues:
- **Node.js build failed:** Check `_affiliates/product-*/package.json` syntax
- **Jekyll failed:** Check `_config.yml` syntax
- **Permissions:** Make sure your GitHub token has repo access (usually automatic)

### Site Shows Old Content

```bash
# Clear browser cache (Hard refresh)
Mac: Cmd + Shift + R
Windows: Ctrl + Shift + F5

# Or wait 5 minutes for GitHub Pages cache to clear
```

### Affiliate Pages Return 404 on GitHub Pages

This usually means the GitHub Actions build failed. Check:
1. **Actions** tab for build errors
2. Make sure `keep_files: [affiliate]` is in `_config.yml`
3. Ensure `_site/affiliate/` files are in Git (run `git ls-files | grep affiliate`)

---

## Important Notes

✅ **Always build affiliates before pushing:**
```bash
./build-affiliates.sh
git add .
```

⚠️ **Never commit `_affiliates/*/node_modules/`** - Git ignores them automatically

✅ **GitHub Actions has read-only access** - It builds automatically, you don't need to do anything special

📌 **First deploy takes 2-3 minutes** - Subsequent deploys are faster (~1 minute)

---

## Quick Reference

| Action | Command |
|--------|---------|
| Local dev | `./dev-workflow.sh` |
| Rebuild affiliates | `./rebuild-affiliates.sh` |
| Build affiliates (first time) | `./build-affiliates.sh` |
| Push to GitHub | `git push origin main` |
| Monitor GitHub Actions | GitHub repo → Actions tab |
| View live site | `https://yourdomain.github.io/blog/` |

Questions? Check the error logs in the **Actions** tab on GitHub.
