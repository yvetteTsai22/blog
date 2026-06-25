# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hybrid blog system: **Jekyll** (main blog) + **React/Vite** apps (affiliate landing pages under `_tool-recommends/`). Theme is Jekflix (Netflix-inspired). Deployed to GitHub Pages at `https://yvettetsai22.github.io/blog/`.

## Build & Dev Commands

### Jekyll Blog
- `gulp` — Dev server with BrowserSync, file watching, and live reload
- `gulp build` — Production build (theme + SASS + JS + images + Jekyll)
- `bundle exec jekyll build --baseurl '/blog'` — Jekyll-only build with production base URL
- `bundle exec jekyll serve --baseurl '/blog'` — Jekyll-only local server

### Tool-Recommend Landing Pages
- `./build-tool-recommends.sh` — Build all affiliate products and copy to `_site/tool-recommend/`
- `cd _tool-recommends/product-N && npm run dev` — Vite dev server for individual product
- `cd _tool-recommends/product-N && npm run build` — Production build for individual product
- Use `npm install --legacy-peer-deps` to handle dependency conflicts in tool-recommend apps

### Full Dev Environment
- `bash ./dev.sh` — Starts Jekyll server + tool-recommend auto-sync together

### Scaffolding
- `./initpost.sh -c My New Post Title` — Create a new blog post in `_posts/`

## Architecture

### Build Pipeline (Gulp)
The Jekyll config is **generated**, not hand-edited. Gulp assembles `_config.yml` from partials in `src/yml/` (site.yml, theme.yml, social.yml, posts.yml, advanced.yml). Theme colors in `src/yml/theme.yml` are converted through a YAML → JSON → SCSS pipeline to produce `_sass/_theme.scss`. JavaScript in `src/js/main/` is concatenated and minified to `assets/js/scripts.min.js`.

**Do not edit `_config.yml` directly** — edit the source files in `src/yml/` instead.

### Two Independent Build Systems
1. **Jekyll** (Ruby/Gulp): Blog posts, layouts, SASS → `_site/`
2. **Vite+React** (Node/TypeScript): Each product in `_tool-recommends/product-N/` is a standalone React app with its own `package.json` and `vite.config.ts`

The affiliate pages are built *after* Jekyll (since Jekyll clears `_site/`) and copied into `_site/tool-recommend/`. Jekyll's `keep_files` config preserves the `tool-recommend/` directory across rebuilds.

### Tool-Recommend Pattern
- All product content lives in `src/config.ts` — no component editing needed for content changes
- Shared UI components live in `_tool-recommends/shared/components/` as a reference; they are **copied** into each product's `src/components/` for build isolation
- Each product's `vite.config.ts` sets a unique base path: `/blog/tool-recommend/<product-name>/`

### Adding a New Product Landing Page

The build system auto-discovers any subdirectory of `_tool-recommends/` that has a `package.json`. No changes to `build-tool-recommends.sh` or the GitHub Actions workflow are needed.

**Steps:**

1. **Create the product directory** by copying an existing one as a template:
   ```bash
   cp -r _tool-recommends/instadoodle _tool-recommends/<product-name>
   cd _tool-recommends/<product-name>
   npm install --legacy-peer-deps
   ```

2. **Update `vite.config.ts`** — change the `base` path:
   ```ts
   base: '/blog/tool-recommend/<product-name>/',
   ```

3. **Edit `src/config.ts`** — all product content (title, description, affiliate URL, features, FAQ, etc.) lives here. No component editing needed.

4. **Test locally:**
   ```bash
   npm run dev
   # visit http://localhost:3002/blog/tool-recommend/<product-name>/
   ```

5. **Commit and push** — CI will auto-build and deploy to:
   ```
   https://yvettetsai22.github.io/blog/tool-recommend/<product-name>/
   ```

### Content Structure
- Blog posts: `_posts/YYYY-MM-DD-title.md` with YAML front matter
- Authors: `_authors/` (Jekyll collection)
- Categories: `category/` (NLP, blog, code, css, diet, life, music, tips, tool, travel, tutorial, work)
- Layouts: `_layouts/` (Liquid templates: home, post, page, contact)
- Theme SCSS: `_sass/`

## CI/CD

GitHub Actions (`.github/workflows/build-tool-recommends.yml`):
1. Builds Jekyll with `--baseurl '/blog'`
2. Builds each tool-recommend product (`npm install --legacy-peer-deps && npm run build`)
3. Copies built products into `_site/tool-recommend/`
4. Deploys `_site/` to GitHub Pages via `peaceiris/actions-gh-pages@v3`

## Key Conventions

- Base URL is `/blog` (all production paths are prefixed)
- Post permalinks: `/:title/`
- Post pagination separator: `--page-break--`
- Ruby 3.2, Node 18 (as used in CI)

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **blog** (1705 symbols, 3172 relationships, 12 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/blog/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/blog/context` | Codebase overview, check index freshness |
| `gitnexus://repo/blog/clusters` | All functional areas |
| `gitnexus://repo/blog/processes` | All execution flows |
| `gitnexus://repo/blog/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
