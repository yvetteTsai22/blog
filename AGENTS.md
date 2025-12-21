# AGENTS instructions

## Project overview
This is a hybrid blog system combining:
- **Jekyll** (Ruby-based static site generator) for the main blog
- **React + Vite** apps for tool recommend landing pages under `_tool-recommends/`
- Theme: Jekflix (Netflix-inspired) with custom modifications

## Dev environment setup
- Install Ruby dependencies: `bundle install`
- Install Node dependencies: `npm install`
- For tool-recommend pages, use `npm install --legacy-peer-deps` to handle dependency conflicts.
- Run `bash ./dev.sh` to start local development with Jekyll + tool-recommend sync.
- Run `gulp` for the default build with watching and BrowserSync hot reload.

## Build commands
- `gulp build` – Production build for the main Jekyll blog.
- `./build-tool-recommends.sh` – Build all React tool recommend landing pages.
- `bundle exec jekyll build --baseurl '/blog'` – Build Jekyll with the production base URL.
- Tool recommend builds output to `_site/tool-recommend/<product-name>/`.

## Working with tool-recommend pages
- Each tool-recommend lives in `_tool-recommends/<product-name>/` with its own `package.json` and Vite config.
- From a tool-recommend directory: `npm run dev` to start Vite dev server, `npm run build` to build.
- Shared configuration is in `_tool-recommends/shared/`.

## Creating new content
- Use `./initpost.sh` to scaffold a new blog post.
- Posts live in `_posts/` as Markdown files with YAML front matter.
- Authors are defined in `_authors/`.

## CI/CD
- GitHub Actions workflow: `.github/workflows/build-tool-recommends.yml`
- Triggers on push or PR to `main` or `master`.
- Builds tool-recommend React apps, then Jekyll, then deploys to GitHub Pages.
- The site is served at the `/blog` subpath.

## PR instructions
- Run `gulp build` and `./build-tool-recommends.sh` locally before pushing.
- Ensure Jekyll builds without errors: `bundle exec jekyll build`.
- Keep tool-recommend `node_modules/` and build artifacts out of commits (already in `.gitignore`).
