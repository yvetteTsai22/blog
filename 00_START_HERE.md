# 🎉 AFFILIATE LANDING PAGES - START HERE

Your affiliate landing pages are fully set up and working!

## ⚡ Quick Start (Copy & Paste)

### Terminal 1: Build Affiliates
```bash
cd /Users/yvette/projects/blog
./build-affiliates.sh
```

### Terminal 2: Start Jekyll
```bash
cd /Users/yvette/projects/blog
bundle exec jekyll serve --baseurl '/blog'
```

### Then Open Browser
- http://127.0.0.1:4000/blog/affiliate/product-1/
- http://127.0.0.1:4000/blog/affiliate/product-2/

---

## 📝 Edit Your Products

### Change Content
```bash
nano _affiliates/product-1/src/config.ts
```

Edit:
- `headline` - Your main message
- `highlights` - Key phrases to highlight
- `benefits` - List of features
- `socialProof` - Stats like "50,000+ users"
- `ctaText` - Button text (e.g., "Get Access")
- `ctaLink` - Your affiliate link
- `productImageUrl` - Product image URL

### Save Changes
```bash
./build-affiliates.sh
```

Refresh browser to see updates!

---

## 🚀 Deploy to GitHub Pages

```bash
./build-affiliates.sh
git add _site/affiliate/
git commit -m "Update affiliate pages"
git push origin main
```

Pages will be live at:
- `yourdomain.github.io/blog/affiliate/product-1/`
- `yourdomain.github.io/blog/affiliate/product-2/`

---

## 📁 Files Created

✅ **`build-affiliates.sh`** - Builds all affiliate pages (run this!)
✅ **`AFFILIATE_SETUP_COMPLETE.md`** - Setup summary
✅ **`AFFILIATE_LOCAL_SETUP.md`** - Detailed local dev guide
✅ **`_affiliates/README.md`** - Full documentation
✅ **`_affiliates/QUICK_START.md`** - Quick reference
✅ **`.gitignore`** - Updated to track built files

---

## 📊 What's Inside

- **product-1** - Example affiliate landing page
- **product-2** - Another example (different content)
- **shared/** - Reference UI components
- React + Vite for fast builds
- 50+ beautiful UI components
- Fully responsive design

---

## 🎯 Next Steps

1. ✅ Run the Quick Start commands above
2. ✅ Visit the URLs in your browser
3. ✅ Edit `_affiliates/product-1/src/config.ts`
4. ✅ Run `./build-affiliates.sh`
5. ✅ Refresh and see changes
6. ✅ Create new products by copying product-1
7. ✅ Deploy to GitHub Pages

---

## 📚 Full Documentation

- **This file:** Quick start
- **AFFILIATE_SETUP_COMPLETE.md** - Setup summary
- **AFFILIATE_LOCAL_SETUP.md** - Detailed guide
- **_affiliates/QUICK_START.md** - Affiliate quick ref
- **_affiliates/README.md** - Complete docs

---

## 🆘 Troubleshooting

**Affiliate pages show 404?**
```bash
./build-affiliates.sh
```

**npm install fails?**
```bash
cd _affiliates/product-1
rm -rf node_modules package-lock.json
npm install
```

**Port 4000 in use?**
```bash
pkill -f "bundle exec jekyll serve"
sleep 1
bundle exec jekyll serve --baseurl '/blog'
```

---

## 🎁 Summary

You have:
- ✅ 2 example affiliate landing pages (fully working)
- ✅ Build script that compiles everything
- ✅ Local dev environment that works
- ✅ Deployment ready for GitHub Pages
- ✅ Complete documentation

**Your affiliate business is ready to launch!** 🚀

---

**Run this now:**
```bash
./build-affiliates.sh && bundle exec jekyll serve --baseurl '/blog'
```

Then visit: http://127.0.0.1:4000/blog/affiliate/product-1/
