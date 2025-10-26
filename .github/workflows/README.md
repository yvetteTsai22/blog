# GitHub Actions Workflow Reference

This file explains what happens automatically when you push to GitHub.

## Workflow File Location
`.github/workflows/build-affiliates.yml`

## What Happens on `git push`

### Automatically Triggered On:
- Push to `main` branch
- Push to `master` branch
- Pull requests to these branches

### Steps That Run (In Order):

1. **Checkout code** - GitHub Actions pulls your repository
2. **Setup Node.js** - Installs Node.js 18
3. **Setup Ruby** - Installs Ruby 3.2 (for Jekyll)
4. **Install dependencies** - `bundle install`
5. **Build affiliates** - Runs for both product-1 and product-2:
   - Installs npm dependencies
   - Runs `npm run build`
   - Copies to `_site/affiliate/`
6. **Build Jekyll** - Runs `jekyll build --baseurl '/blog'`
7. **Deploy to GitHub Pages** - Pushes `_site/` to `gh-pages` branch

### Total Time
- **First run:** 2-3 minutes
- **Subsequent runs:** ~1 minute

---

## Monitoring the Workflow

### In GitHub
1. Go to your repository
2. Click **Actions** tab
3. See all workflow runs
4. Click on a run to see detailed logs

### Status Indicators
- 🟡 **Yellow (In progress)** - Workflow is running
- 🟢 **Green (Success)** - Everything worked, site is live
- 🔴 **Red (Failed)** - Something broke, check logs

### View Logs
1. Click a workflow run
2. Click "Build and Deploy" job
3. Expand any step to see what happened
4. Look for error messages

---

## When It's Done

### Your Site Goes Live At:
- `https://yourdomain.github.io/blog/`
- `https://yourdomain.github.io/blog/affiliate/product-1/`
- `https://yourdomain.github.io/blog/affiliate/product-2/`

(Or your custom domain if configured)

### GitHub Pages Branch
- A new branch `gh-pages` is automatically created
- Contains the built `_site/` directory
- This is what the internet sees

---

## Customization

### Edit the Workflow File

To make changes, edit `.github/workflows/build-affiliates.yml`:

```yaml
# Change Node version
node-version: '18'  # ← Change if needed

# Change Ruby version
ruby-version: '3.2'  # ← Change if needed

# Change deployment domain
cname: yourdomain.github.io  # ← Your domain here
```

### Add New Build Steps

Example: Add a custom build script:

```yaml
- name: Run custom build script
  run: |
    bash ./my-custom-script.sh
```

---

## Troubleshooting Failures

### Read the Error Log
1. Click failed workflow
2. Click failed job
3. Look at error message
4. Common issues below:

### Common Errors

#### `npm ERR! code ERESOLVE`
**Cause:** npm dependency conflict
**Fix:** Already handled with `--legacy-peer-deps` flag

#### `jekyll: command not found`
**Cause:** Ruby/Jekyll not installed correctly
**Fix:** Workflow handles this, check Ruby version

#### `Could not find a JavaScript runtime`
**Cause:** Node.js issue
**Fix:** Workflow handles this, may need to clear cache

#### Build succeeds but site shows 404
**Cause:** `keep_files: [affiliate]` missing or assets not in `_site/`
**Fix:** Verify `_config.yml` has the `keep_files:` section

### Clear GitHub Actions Cache
If builds fail mysteriously:

1. Go to **Settings** → **Actions** → **Runners**
2. Click **Clear all caches**
3. Try deploying again

---

## Manual Deployment (Backup Plan)

If GitHub Actions fails repeatedly, deploy manually:

```bash
# Build locally
./build-affiliates.sh
bundle exec jekyll build --baseurl '/blog'

# Deploy manually
git checkout --orphan gh-pages
git rm -rf .
cp -r _site/* .
git add .
git commit -m "Manual deployment"
git push origin gh-pages -f

# Return to main
git checkout main
```

---

## Best Practices

✅ **DO:**
- Build affiliates locally before pushing
- Check Actions log after every push
- Keep `_config.yml` syntax correct
- Commit built files in `_site/affiliate/`

❌ **DON'T:**
- Edit `_site/` files directly
- Push without building first
- Change the workflow without testing
- Commit `node_modules/` folders

---

## Security Notes

- GitHub Actions uses `${{ secrets.GITHUB_TOKEN }}` - This is secure
- Token is automatically rotated by GitHub
- Workflow has read/write access to your repo only
- No sensitive data is logged

---

## For More Info

- **GitHub Actions Docs:** https://docs.github.com/en/actions
- **GitHub Pages Docs:** https://docs.github.com/en/pages
- **Local Development:** See `DEVELOPMENT_WORKFLOW.md`
- **Deployment Guide:** See `GITHUB_PAGES_DEPLOYMENT.md`

---

## Quick Checklist

Before first push:
- [ ] Updated `cname:` with your domain
- [ ] Ran `./build-affiliates.sh` locally
- [ ] Verified `_site/affiliate/` has files
- [ ] Set GitHub Pages source to `gh-pages` branch
- [ ] Committed and pushed

After first push:
- [ ] Checked **Actions** tab
- [ ] Verified build succeeded (✅)
- [ ] Visited live site
- [ ] Affiliate pages load correctly
- [ ] No 404 errors

You're ready! 🚀
