# 📖 Documentation Index

Complete reference guide for your affiliate landing pages setup.

---

## 🚀 Getting Started

**Start with these:**

1. **`00_START_HERE.md`** ⭐ 
   - Quick start guide
   - Build and deploy in 5 minutes
   - Basic troubleshooting

2. **`SETUP_COMPLETE.md`**
   - Complete setup overview
   - What you have and how it works
   - File structure and reference

---

## 📋 How-To Guides

**Choose a task:**

### Local Development
- **`DEVELOPMENT_WORKFLOW.md`**
  - Local development setup
  - How to edit and test
  - Using `./dev-workflow.sh`

### GitHub Pages Deployment
- **`GITHUB_PAGES_DEPLOYMENT.md`** 
  - Complete GitHub Pages setup
  - GitHub Actions automation
  - Detailed troubleshooting

- **`DEPLOYMENT_READY.md`**
  - Pre-deployment checklist
  - Step-by-step deployment
  - What to do after first deploy

### Adding New Products
- **`ADD_NEW_AFFILIATE_PRODUCT.md`** ⭐
  - How to create product-3, product-4, etc.
  - Configuration options
  - All customization details

---

## 🛠️ Technical Reference

**For technical details:**

### GitHub Actions
- **`.github/workflows/build-affiliates.yml`**
  - The automation workflow (read-only)
  - Updates on your machine

- **`.github/workflows/README.md`**
  - How GitHub Actions works
  - Monitoring builds
  - Troubleshooting automation

### Affiliate Configuration
- **`_affiliates/README.md`**
  - Full technical documentation
  - Architecture and design
  - Component details

- **`_affiliates/QUICK_START.md`**
  - Quick reference for affiliates
  - Configuration fields
  - Build process

### Build Scripts
- **`build-affiliates.sh`**
  - Initial full build
  - Use before first deployment

- **`rebuild-affiliates.sh`**
  - Quick rebuild after edits
  - Faster than full build

- **`dev-workflow.sh`**
  - Automated dev environment
  - Handles Jekyll + React timing

---

## 📊 Quick Decision Tree

**"I want to..."**

### ...start developing locally
→ Read: `00_START_HERE.md` then `DEVELOPMENT_WORKFLOW.md`

### ...deploy to GitHub Pages
→ Read: `GITHUB_PAGES_DEPLOYMENT.md` then `DEPLOYMENT_READY.md`

### ...add product-3, product-4, etc.
→ Read: `ADD_NEW_AFFILIATE_PRODUCT.md` ⭐

### ...understand how everything works
→ Read: `SETUP_COMPLETE.md` and `_affiliates/README.md`

### ...debug a problem
→ Check the "Troubleshooting" section in each guide

### ...customize design or components
→ Read: `_affiliates/README.md` then `DEVELOPMENT_WORKFLOW.md`

---

## 📁 File Structure Reference

```
/blog/
├── 📄 00_START_HERE.md                    ← Start here
├── 📄 SETUP_COMPLETE.md                  ← Overview
├── 📄 ADD_NEW_AFFILIATE_PRODUCT.md       ← Add products ⭐
├── 📄 DEVELOPMENT_WORKFLOW.md            ← Local dev
├── 📄 GITHUB_PAGES_DEPLOYMENT.md         ← GitHub Pages
├── �� DEPLOYMENT_READY.md                ← Pre-deploy checklist
├── 📄 DOCUMENTATION_INDEX.md             ← This file
│
├── 🔧 build-affiliates.sh                ← Build script
├── 🔧 rebuild-affiliates.sh              ← Quick rebuild
├── 🔧 dev-workflow.sh                    ← Dev environment
│
├── 📋 _config.yml                        ← Jekyll config
├── 📋 .gitignore                         ← Git rules
│
├── .github/
│   └── workflows/
│       ├── build-affiliates.yml          ← GitHub Actions
│       └── README.md                     ← Actions reference
│
├── _affiliates/
│   ├── 📄 README.md                      ← Affiliate docs
│   ├── 📄 QUICK_START.md                 ← Affiliate quick ref
│   ├── product-1/                        ← Example affiliate 1
│   ├── product-2/                        ← Example affiliate 2
│   └── shared/                           ← Shared components
│
└── _site/
    └── affiliate/                        ← Built output
        ├── product-1/                    ← Built affiliate 1
        └── product-2/                    ← Built affiliate 2
```

---

## �� Common Tasks Quick Reference

| Task | Guide | Command |
|------|-------|---------|
| Start local dev | `DEVELOPMENT_WORKFLOW.md` | `./dev-workflow.sh` |
| Edit product content | `ADD_NEW_AFFILIATE_PRODUCT.md` | `nano _affiliates/product-1/src/config.ts` |
| Rebuild after edit | `DEVELOPMENT_WORKFLOW.md` | `./rebuild-affiliates.sh` |
| Add new product | `ADD_NEW_AFFILIATE_PRODUCT.md` | `cp -r _affiliates/product-1 _affiliates/product-3` |
| Deploy to GitHub | `GITHUB_PAGES_DEPLOYMENT.md` | `git push origin main` |
| Monitor build | `.github/workflows/README.md` | GitHub Actions tab |
| Troubleshoot | Various guides | Search "Troubleshooting" |

---

## 🔑 Key Concepts

### Affiliate Pages
- **What:** React-based landing pages for affiliate products
- **Where:** `_affiliates/product-1/`, `_affiliates/product-2/`, etc.
- **Configuration:** Edit `src/config.ts` for content
- **Building:** Run `./rebuild-affiliates.sh` after edits

### Jekyll Blog
- **What:** Your blog content and main site
- **Where:** Root directory (posts in `_posts/`)
- **Configuration:** `_config.yml`
- **Important:** `keep_files: [affiliate]` preserves affiliate pages

### GitHub Actions
- **What:** Automated build and deploy
- **When:** Triggers on `git push`
- **Workflow:** `.github/workflows/build-affiliates.yml`
- **Output:** Deploys to `gh-pages` branch

### GitHub Pages
- **What:** Free hosting for your site
- **Where:** `https://yourdomain.github.io/blog/`
- **Source:** `gh-pages` branch
- **Setup:** Settings → Pages → Deploy from branch

---

## 🚨 Important Notes

⚠️ **Before pushing to GitHub:**
1. Update `cname:` in `.github/workflows/build-affiliates.yml`
2. Enable GitHub Pages in repo settings
3. Run `./build-affiliates.sh` locally first

✅ **Always rebuild locally before pushing:**
```bash
./rebuild-affiliates.sh
git add .
git push origin main
```

✅ **GitHub Actions handles everything after push:**
- Builds React apps
- Builds Jekyll site
- Deploys to GitHub Pages

---

## 📞 Getting Help

1. **Check the relevant guide** - Each has a "Troubleshooting" section
2. **Search documentation** - Look for keywords
3. **Check GitHub Actions logs** - For deployment issues
4. **Read error messages carefully** - Usually tell you the problem

---

## ✅ Checklist for Success

- [ ] Read `00_START_HERE.md`
- [ ] Run `./build-affiliates.sh` locally
- [ ] Test affiliate pages locally
- [ ] Edit `_affiliates/product-1/src/config.ts`
- [ ] Deploy to GitHub Pages (see `GITHUB_PAGES_DEPLOYMENT.md`)
- [ ] Monitor GitHub Actions build
- [ ] Visit live site to verify
- [ ] Add new products as needed (see `ADD_NEW_AFFILIATE_PRODUCT.md`)

---

## 🎉 You're Ready!

Your affiliate landing pages are fully set up and documented.

**Next step:** Read `00_START_HERE.md` or `ADD_NEW_AFFILIATE_PRODUCT.md`

Happy building! 🚀
