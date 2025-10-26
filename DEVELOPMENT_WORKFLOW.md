# Quick Start Guide - Development Workflow

## The Problem & Solution

Jekyll regenerates `_site/` when it starts, which overwrites your affiliate pages. The solution is to rebuild them **after** Jekyll has initialized.

## Quick Start (Recommended)

Use the integrated development workflow script:

```bash
./dev-workflow.sh
```

This script:
1. ✅ Builds your affiliate pages
2. ✅ Starts Jekyll in the background
3. ✅ Waits for Jekyll to initialize
4. ✅ Rebuilds affiliate pages (so they aren't overwritten)
5. ✅ Shows you the URLs to visit

Then visit:
- **Blog:** http://127.0.0.1:4000/blog/
- **Affiliate 1:** http://127.0.0.1:4000/blog/affiliate/product-1/
- **Affiliate 2:** http://127.0.0.1:4000/blog/affiliate/product-2/

Press `Ctrl+C` to stop.

## Editing Workflow During Development

When you edit affiliate content in `_affiliates/product-1/` or `_affiliates/product-2/`:

1. **Edit your files** in the IDE
2. **Rebuild affiliates:**
   ```bash
   ./rebuild-affiliates.sh
   ```
3. **Refresh your browser** to see changes

That's it! No need to restart Jekyll.

## Manual Process (If You Prefer)

If you want full control:

```bash
# Terminal 1: Start Jekyll in background
bundle exec jekyll serve --baseurl '/blog' &

# Wait 3 seconds for Jekyll to initialize, then in Terminal 2:
./build-affiliates.sh

# Visit http://127.0.0.1:4000/blog/affiliate/product-1/
```

When you edit affiliate content:
```bash
# Terminal 2: Just rebuild (Jekyll keeps running)
./rebuild-affiliates.sh
# Refresh browser
```

## Troubleshooting

### "Address already in use" Error

If you get a port 4000 error:

```bash
# Kill any existing process on port 4000
lsof -i :4000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Then try again
./dev-workflow.sh
```

### Affiliate pages show 404

This usually means:
1. **The pages haven't been built yet** → Run `./build-affiliates.sh`
2. **Jekyll just started** → Wait a moment, then refresh
3. **You edited affiliate code** → Run `./rebuild-affiliates.sh` and refresh

### Changes not showing up

1. Run `./rebuild-affiliates.sh` (even if you edited Jekyll files)
2. Hard-refresh browser (Cmd+Shift+R on Mac)
3. Check that the build completed successfully

## File Structure

```
blog/
├── dev-workflow.sh           ← Use this to start development
├── build-affiliates.sh       ← Builds affiliates initially
├── rebuild-affiliates.sh     ← Use this when editing affiliates
├── _config.yml               ← Jekyll config
├── _affiliates/
│   ├── product-1/            ← Edit these
│   │   ├── src/
│   │   │   ├── config.ts      ← Content config
│   │   │   ├── App.tsx
│   │   │   └── components/
│   │   ├── vite.config.ts
│   │   └── package.json
│   ├── product-2/            ← Edit these
│   │   └── ... (same as product-1)
│   └── shared/               ← Shared UI components
└── _site/
    └── affiliate/            ← Built output (don't edit)
        ├── product-1/
        └── product-2/
```

## Next Steps

- **To add a new product:** Copy `_affiliates/product-1/` to `_affiliates/product-3/`, update `config.ts`
- **To customize styling:** Edit `src/components/AffiliateLandingPage.tsx` or Tailwind classes
- **To deploy:** Push to GitHub and enable GitHub Pages (all builds are committed to `_site/`)

## Commands Reference

| Task | Command |
|------|---------|
| Start development | `./dev-workflow.sh` |
| Rebuild affiliates | `./rebuild-affiliates.sh` |
| Build initial setup | `./build-affiliates.sh` |
| Start Jekyll only | `bundle exec jekyll serve --baseurl '/blog'` |

Questions? Check `AFFILIATE_SETUP_COMPLETE.md` for more details.
