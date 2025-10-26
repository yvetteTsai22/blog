# Affiliate Landing Pages

This folder contains multiple affiliate landing pages built with React, TypeScript, and Vite. Each product is independently built and deployable.

## 🏗️ Architecture

### Design Philosophy

- **Independent Products** - Each product has its own build and deployment
- **Shared Components** - UI components are referenced in shared folder but copied to each product (for build isolation)
- **Config-Driven** - All content changes happen in `src/config.ts` - no component modifications needed
- **Fast & Simple** - Pure React + Vite, no complex setup

### Directory Structure

```
_affiliates/
├── shared/                    # Reference source (don't edit for deployment)
│   └── components/
│       ├── AffiliateLandingPage.tsx    # Main landing page component
│       ├── ui/                         # 50+ Radix UI components
│       └── figma/                      # Utility components
│
├── product-1/                 # Independent affiliate landing page
│   ├── src/
│   │   ├── components/        # Copied from shared
│   │   │   ├── AffiliateLandingPage.tsx
│   │   │   ├── ui/
│   │   │   └── figma/
│   │   ├── App.tsx            # Main app (uses config)
│   │   ├── config.ts          # ⭐ Edit this for content
│   │   ├── main.tsx
│   │   └── index.css
│   ├── build/                 # Generated on npm run build
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── node_modules/
│
├── product-2/                 # Same structure as product-1
│   ├── src/
│   ├── build/
│   └── ...
│
└── README.md & QUICK_START.md
```

## Getting Started

### Build Individual Products

```bash
# Product 1
cd _affiliates/product-1
npm install
npm run build

# Product 2
cd _affiliates/product-2
npm install
npm run build
```

### Development

Each product can be developed independently:

```bash
cd _affiliates/product-1
npm run dev
```

## Creating a New Product

1. Copy an existing product folder (e.g., `cp -r product-1 product-3`)
2. Update `src/config.ts` with new product details
3. Keep `App.tsx` as-is (it imports from shared)
4. Run `npm install` in the new folder
5. Start developing with `npm run dev`

## Configuration

Each product's content is controlled via `src/config.ts`:

```typescript
export const productConfig = {
  headline: "Your headline here",
  highlights: [{ text: "Highlighted text", style: "gradient" }],
  subheadline: "Your subheadline",
  benefits: ["Benefit 1", "Benefit 2"],
  socialProof: [{ value: "100+", label: "Users" }],
  ctaText: "Call to action",
  ctaLink: "your-affiliate-link",
  productImageUrl: "image-url"
};
```

## Deployment

Each `dist/` folder can be deployed independently to:
- Netlify
- Vercel
- GitHub Pages (separate repo)
- Your own server

## Styling

Global styles are in the shared components. Product-specific styling can be added to individual `index.css` files if needed.

## 🚀 Quick Start

### Build a Product

```bash
cd _affiliates/product-1
npm install      # Only needed first time
npm run build    # Creates build/ folder
```

### View Product Locally

```bash
cd _affiliates/product-1
npm run dev      # Starts at http://localhost:5173
```

### Edit Content

**All content lives in `src/config.ts`** - no need to touch components:

```typescript
// _affiliates/product-1/src/config.ts
export const productConfig = {
  headline: "Your Product Headline",
  highlights: [
    { text: "Key phrase 1", style: "gradient" },
    { text: "Key phrase 2", style: "background" }
  ],
  subheadline: "Supporting text",
  benefits: [
    "Benefit 1",
    "Benefit 2",
    "Benefit 3"
  ],
  socialProof: [
    { value: "50,000+", label: "Users" },
    { value: "4.9/5", label: "Rating" }
  ],
  ctaText: "Click here!",
  ctaLink: "https://your-affiliate-link.com",
  productImageUrl: "https://example.com/image.jpg"
};
```

## ➕ Creating New Products

### Option 1: Quick Copy

```bash
# Copy product-1 to create product-3
cp -r _affiliates/product-1 _affiliates/product-3

# Update config
cd _affiliates/product-3
nano src/config.ts

# Install and test
npm install
npm run dev
```

### Option 2: Manual Setup

1. Copy product-1 folder → product-3
2. Update `package.json` name field if desired
3. Edit `src/config.ts` with new content
4. Run `npm install && npm run dev`

## 📤 Deployment

### To Netlify (Easiest)

1. Push your repo to GitHub
2. Go to netlify.com → New site from Git
3. Select your repository
4. Build settings:
   - **Build command:** `cd _affiliates/product-1 && npm run build`
   - **Publish directory:** `_affiliates/product-1/build`
5. Click Deploy!

Your site will be live at `your-site.netlify.app`

### To Vercel

```bash
npm install -g vercel
cd _affiliates/product-1
vercel
```

### To GitHub Pages

1. Create new repo: `affiliate-product-1`
2. Copy `build/` contents to repo root
3. Enable GitHub Pages in settings
4. Access at `username.github.io/affiliate-product-1`

### To Your Own Server

```bash
cd _affiliates/product-1
npm run build

# Upload build/ folder via FTP/SSH
# Or use rsync:
rsync -avz build/ user@host:/var/www/affiliate/
```

## 🎨 Customization

### Highlight Styles

Three highlight style options:

```typescript
// Gradient effect
{ text: "Amazing", style: "gradient" }

// Background highlight
{ text: "Feature", style: "background" }

// Underline
{ text: "Important", style: "underline" }
```

### Component Features

The `AffiliateLandingPage` component includes:

- ✅ Hero section with headline
- ✅ Highlighted text styling
- ✅ Features/benefits section
- ✅ Social proof section
- ✅ Product image with fallback
- ✅ CTA button
- ✅ Responsive design
- ✅ Dark mode support
- ✅ Smooth animations

### Styling

Global styles are in:
- `src/index.css` - Global CSS
- `src/components/ui/*.tsx` - Component styles (Tailwind CSS)

Modify `index.css` to change colors, fonts, spacing globally for a product.

## 📊 Content Tips

### Headlines

- Keep under 80 characters
- Use power words: Secret, Discover, Transform, Unlock
- Lead with benefit, not features

### Benefits

- Start with action verb
- Include specific numbers when possible
- 5-7 benefits work best
- Order by importance

### Social Proof

- Use real numbers
- Include different types (users, rating, results)
- 3-5 items optimal

### CTA

- Action-oriented text: "Get Access", "Start Free", "Learn More"
- Make link your actual affiliate URL
- Test different CTA text with A/B testing

## 🔧 Technical Details

### Dependencies

All products use:
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Lightning-fast builds
- **Tailwind CSS** - Styling
- **Radix UI** - Accessible components
- **Lucide React** - Icons

### Build Output

Running `npm run build` creates:
- `build/index.html` - Main page
- `build/assets/` - CSS and JS bundles
- Optimized for production
- ~180KB total size (gzipped: ~60KB)

### Performance

- Fast initial load
- Optimized images
- Code splitting
- Asset compression
- SEO-friendly HTML

## 🐛 Troubleshooting

### npm install fails

```bash
rm -rf node_modules package-lock.json
npm install
```

### Build error: "Cannot find module"

Make sure you're in the right directory:
```bash
cd _affiliates/product-1
npm run build
```

### Port 5173 already in use

```bash
npm run dev -- --port 5174
```

### Images not loading

Check that `productImageUrl` in config is:
- Valid HTTPS URL (not HTTP)
- Image exists and is accessible
- URL is complete with file extension

## 📚 File Reference

### Main Files to Edit

| File | Purpose |
|------|---------|
| `src/config.ts` | All content (headlines, benefits, links) |
| `src/index.css` | Global styles |
| `vite.config.ts` | Build configuration |

### Component Files (Don't edit for deployment)

| File | Purpose |
|------|---------|
| `src/App.tsx` | Entry point, uses config |
| `src/components/AffiliateLandingPage.tsx` | Main component |
| `src/components/ui/*` | UI components |
| `src/main.tsx` | React setup |

## 🎯 Workflow Example

### Creating & Deploying Your First Product

```bash
# 1. Create new product
cp -r _affiliates/product-1 _affiliates/my-tool

# 2. Edit content
cd _affiliates/my-tool
nano src/config.ts
# Update: headline, benefits, CTA, image URL, affiliate link

# 3. Test locally
npm install
npm run dev
# Visit http://localhost:5173 and check it looks good

# 4. Build for production
npm run build

# 5. Deploy
# Option A: Push to GitHub and deploy via Netlify
# Option B: Upload build/ folder to your server
# Option C: Use Vercel CLI: vercel
```

## 💡 Next Steps

1. Read `QUICK_START.md` for step-by-step guide
2. Customize `product-1` or create a new product
3. Test locally with `npm run dev`
4. Build with `npm run build`
5. Deploy the `build/` folder
6. Share your affiliate link!

## 📖 Resources

- [Radix UI Components](https://www.radix-ui.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)

---

**Last Updated:** October 2025
**Status:** ✅ Ready to use
