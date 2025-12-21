# Quick Start Guide - Tool Recommend Landing Pages

## ✅ Setup Complete!

Your tool recommend landing pages are now organized and ready to use. Here's what's been set up:

### 📁 What You Have

- **`_tool-recommends/product-1/`** - First tool recommend landing page (fully built)
- **`_tool-recommends/product-2/`** - Second tool recommend landing page (fully built)
- **`_tool-recommends/shared/`** - Reference source for components
- **`_tool-recommends/build/`** - Built output folders in each product

### 🚀 Using Your Tool Recommend Pages

#### View Product Pages Locally

```bash
# Product 1
cd _tool-recommends/product-1
npm run dev

# Opens at http://localhost:5173
```

#### Build for Deployment

```bash
# Product 1
cd _tool-recommends/product-1
npm run build
# Output in: _tool-recommends/product-1/build/

# Product 2
cd _tool-recommends/product-2
npm run build
# Output in: _tool-recommends/product-2/build/
```

### 📝 Customizing Products

Each product has a `src/config.ts` file that controls all content:

**`_tool-recommends/product-1/src/config.ts`**
```typescript
export const productConfig = {
  headline: "Your headline",
  highlights: [{ text: "Highlighted text", style: "gradient" }],
  subheadline: "Your subheadline",
  benefits: ["Benefit 1", "Benefit 2", ...],
  socialProof: [{ value: "100+", label: "Users" }, ...],
  ctaText: "Button text",
  ctaLink: "your-affiliate-link",
  productImageUrl: "image-url"
};
```

Just edit the config to change everything about your landing page!

### ➕ Creating New Products

1. **Copy an existing product:**
   ```bash
   cp -r _tool-recommends/product-1 _affiliates/product-3
   ```

2. **Update the config:**
   ```bash
   cd _tool-recommends/product-3
   nano src/config.ts
   ```

3. **Install dependencies:**
   ```bash
   npm install
   ```

4. **Start developing:**
   ```bash
   npm run dev
   ```

### 🌐 Deployment Options

Each `build/` folder can be deployed to:

- **Netlify** - Easiest option, auto-deploys on git push
- **Vercel** - Great for React projects
- **GitHub Pages** - Use separate repo for each product
- **Your server** - Upload the `build/` folder via FTP/SSH

#### Deploy to Netlify (Recommended)

1. Create new site in Netlify
2. Connect your GitHub repo
3. Set build command: `cd _tool-recommends/product-1 && npm run build`
4. Set publish directory: `_affiliates/product-1/build`
5. Deploy!

### 📚 Available Styles

In your config, use these highlight styles:

```typescript
highlights: [
  { text: "Gradient text", style: "gradient" },      // Colorful gradient
  { text: "Background", style: "background" },       // Solid background
  { text: "Underline", style: "underline" }          // Underline
]
```

### 💡 Pro Tips

1. **Share affiliate links** - Put your unique link in `ctaLink`
2. **Update images** - Change `productImageUrl` to your product photo
3. **Track results** - Use UTM parameters in affiliate links for analytics
4. **A/B test** - Create multiple products with different headlines/benefits
5. **Embed anywhere** - Get the deployment URL and embed via iframe or direct link

### 🔗 Project Structure

```
product-1/
├── src/
│   ├── config.ts          ← Edit this for content
│   ├── App.tsx            ← Uses config
│   ├── components/        ← Reusable UI components
│   ├── index.css          ← Styles
│   └── main.tsx
├── build/                 ← Generated on npm run build
├── vite.config.ts
├── package.json
└── index.html
```

### ❓ Common Tasks

**Change headline:**
```typescript
// src/config.ts
headline: "Your new headline here"
```

**Add more benefits:**
```typescript
benefits: [
  "Existing benefit",
  "New benefit 1",
  "New benefit 2",
  "New benefit 3"
]
```

**Update social proof:**
```typescript
socialProof: [
  { value: "10,000+", label: "Customers" },
  { value: "4.9/5", label: "Rating" },
  { value: "$5M+", label: "Saved" }
]
```

**Change button text and link:**
```typescript
ctaText: "Get Access Now",
ctaLink: "https://your-affiliate-link.com"
```

### 🎨 Available UI Components

All products include:
- Buttons, cards, badges
- Forms and inputs
- Modals and dialogs
- Tabs and accordions
- Sliders and progress bars
- And 50+ more UI components from Radix UI

### 📖 Next Steps

1. ✅ Customize `product-1` config with your first tool recommend product
2. ✅ Test locally with `npm run dev`
3. ✅ Build with `npm run build`
4. ✅ Deploy the `build/` folder to Netlify/Vercel
5. ✅ Share your tool recommend landing page URL!

### 📞 Need Help?

- Check the full README: `_tool-recommends/README.md`
- Review the template: `_tool-recommends/shared/components/ToolRecommendLandingPage.tsx`
- Check Radix UI docs: https://www.radix-ui.com/

Enjoy! 🚀
