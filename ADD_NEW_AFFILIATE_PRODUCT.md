# Adding New Affiliate Products - Quick Guide

This guide walks you through adding a new affiliate product to your GitHub Pages blog.

## Quick Summary

```bash
# 1. Copy template
cp -r _affiliates/product-1 _affiliates/product-3

# 2. Edit content
nano _affiliates/product-3/src/config.ts

# 3. Test locally
./rebuild-affiliates.sh
# Visit: http://127.0.0.1:4000/blog/affiliate/product-3/

# 4. Deploy (auto-builds on GitHub Actions)
git add .
git commit -m "Add product-3 affiliate page"
git push origin main
```

That's it! Your new page will be live at `https://yourdomain.github.io/blog/affiliate/product-3/`

---

## Detailed Steps

### Step 1: Copy the Template

```bash
cp -r _affiliates/product-1 _affiliates/product-3
```

This creates a complete copy with:
- ✅ All dependencies configured
- ✅ Vite build setup
- ✅ React components
- ✅ Ready to customize

### Step 2: Update the Configuration

Edit the config file:

```bash
nano _affiliates/product-3/src/config.ts
```

Update with your product details:

```typescript
export const productConfig = {
  headline: "Product 3 - Amazing Solution",
  subheadline: "The best product for your needs",
  
  highlights: [
    { text: "Feature 1", style: "gradient" },
    { text: "Feature 2", style: "default" },
    { text: "Feature 3", style: "gradient" }
  ],
  
  benefits: [
    "Benefit 1 - Save time",
    "Benefit 2 - Increase productivity", 
    "Benefit 3 - Reduce costs"
  ],
  
  socialProof: [
    { value: "250,000+", label: "Active Users" },
    { value: "4.9★", label: "Average Rating" },
    { value: "98%", label: "Satisfaction" }
  ],
  
  ctaText: "Start Your Free Trial",
  ctaLink: "https://your-affiliate-link-product-3.com",
  productImageUrl: "https://your-domain.com/images/product-3.png"
};
```

**Config Fields Explained:**

| Field | Purpose | Example |
|-------|---------|---------|
| `headline` | Main page headline | "Affiliate Product Name" |
| `subheadline` | Smaller subtitle | "Transform your workflow" |
| `highlights` | Feature boxes (max 3) | `{ text: "Fast", style: "gradient" }` |
| `benefits` | List of benefits (3-5) | "Save 10 hours per week" |
| `socialProof` | Social proof stats | `{ value: "50K+", label: "Users" }` |
| `ctaText` | Button text | "Get Started" |
| `ctaLink` | Affiliate/button link | Your affiliate URL |
| `productImageUrl` | Product image URL | Full URL to image |

### Step 3: Customize the Design (Optional)

If you want to customize colors or layout:

```bash
nano _affiliates/product-3/src/components/AffiliateLandingPage.tsx
```

Common customizations:
- Change Tailwind color classes
- Modify text alignment
- Adjust component spacing
- Add additional sections

See the existing product-1 or product-2 for examples.

### Step 4: Test Locally

Build and test before deploying:

```bash
./rebuild-affiliates.sh
```

Then visit in your browser:
```
http://127.0.0.1:4000/blog/affiliate/product-3/
```

**Tips for testing:**
- Hard refresh (Cmd+Shift+R) to clear cache
- Check that all images load
- Test the CTA button (should go to your affiliate link)
- Verify mobile responsiveness (inspect in browser dev tools)

### Step 5: Deploy to GitHub Pages

When you're ready to go live:

```bash
# Stage all changes
git add .

# Commit with descriptive message
git commit -m "Add product-3 affiliate landing page"

# Push to GitHub (triggers automatic build)
git push origin main
```

**What happens next:**
1. GitHub Actions automatically builds your new page
2. React app compiles with optimized assets
3. Jekyll processes your blog content
4. Everything deploys to `gh-pages` branch
5. Site goes live (1-2 minutes)

**Monitor the build:**
- Go to your GitHub repo
- Click **Actions** tab
- Watch the "Build Affiliates & Deploy" workflow
- When it shows ✅, your site is live!

---

## Adding Multiple Products

Just repeat the process for each product:

```bash
# Product 4
cp -r _affiliates/product-1 _affiliates/product-4
nano _affiliates/product-4/src/config.ts
./rebuild-affiliates.sh
git push origin main

# Product 5
cp -r _affiliates/product-1 _affiliates/product-5
nano _affiliates/product-5/src/config.ts
./rebuild-affiliates.sh
git push origin main

# ... and so on
```

Each product will have its own URL:
- `/blog/affiliate/product-3/`
- `/blog/affiliate/product-4/`
- `/blog/affiliate/product-5/`
- etc.

---

## Editing Existing Products

To update an existing product (e.g., product-1):

```bash
# Edit config
nano _affiliates/product-1/src/config.ts

# Test locally
./rebuild-affiliates.sh
# Refresh browser

# Deploy
git add .
git commit -m "Update product-1 content"
git push origin main
```

GitHub Actions will automatically rebuild and deploy.

---

## Troubleshooting

### Build fails locally
```bash
# Rebuild everything
./build-affiliates.sh

# Or build a specific product
cd _affiliates/product-3
npm install
npm run build
cd ../..
```

### Assets not loading
- Hard refresh browser (Cmd+Shift+R)
- Check that images URLs are correct and accessible
- Verify `vite.config.ts` has correct `base:` path

### New page returns 404 after pushing
- Check GitHub Actions logs (Actions tab)
- Verify the build succeeded (✅)
- Wait 5 minutes for GitHub Pages cache to clear
- Hard refresh browser

### Old content showing
- Hard refresh browser (Cmd+Shift+R)
- Clear browser cache completely
- Wait 5-10 minutes for CDN cache

---

## File Locations

New product files are automatically created here:

```
_affiliates/product-3/
├── src/
│   ├── config.ts           ← Edit this
│   ├── App.tsx             (leave as-is)
│   ├── components/         (optional customization)
│   │   └── AffiliateLandingPage.tsx
│   └── main.tsx
├── build/                  (generated, don't edit)
├── index.html
├── package.json
├── vite.config.ts
└── node_modules/           (auto-installed)
```

Deployed files go to:
```
_site/affiliate/product-3/
├── index.html
├── assets/
│   ├── index-xxx.js
│   └── index-xxx.css
└── ...
```

---

## GitHub Actions Automation

When you push, GitHub Actions:

1. ✅ Detects changes in `_affiliates/`
2. ✅ Installs npm dependencies for **all** products
3. ✅ Builds **all** products (product-1, product-2, product-3, etc.)
4. ✅ Builds Jekyll blog
5. ✅ Deploys to GitHub Pages

So you don't need to do anything special - just push and GitHub handles the build! 🚀

---

## Command Reference

| Task | Command |
|------|---------|
| Copy template for new product | `cp -r _affiliates/product-1 _affiliates/product-X` |
| Edit product content | `nano _affiliates/product-X/src/config.ts` |
| Build locally | `./rebuild-affiliates.sh` |
| Deploy to GitHub | `git push origin main` |
| Monitor build | GitHub repo → Actions tab |
| Check live site | `https://yourdomain.github.io/blog/affiliate/product-X/` |

---

## Next Steps

1. **Choose a product number** (3, 4, 5, etc.)
2. **Copy the template:** `cp -r _affiliates/product-1 _affiliates/product-X`
3. **Edit the config:** `nano _affiliates/product-X/src/config.ts`
4. **Test locally:** `./rebuild-affiliates.sh`
5. **Deploy:** `git push origin main`

You can add unlimited products! Each gets its own page and independent configuration.

---

## Need Help?

- **Local development issues:** See `DEVELOPMENT_WORKFLOW.md`
- **GitHub Pages deployment:** See `GITHUB_PAGES_DEPLOYMENT.md`
- **Component customization:** See `_affiliates/README.md`
- **Configuration details:** See `_affiliates/QUICK_START.md`

Happy creating! 🚀
