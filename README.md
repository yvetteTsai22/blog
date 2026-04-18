# Yvette's Blog

My personal blog — built on the [Jekflix](https://github.com/thiagorossener/jekflix-template) theme (Netflix-inspired Jekyll theme) with affiliate landing pages powered by React/Vite.

**Live site:** [yvettetsai22.github.io/blog](https://yvettetsai22.github.io/blog/)

## Topics

NLP · Code · CSS · Tools · Tips · Tutorials · Travel · Life · Music · Diet · Work

## Tech Stack

- **Jekyll** — blog posts, layouts, SASS, Liquid templates
- **Gulp** — dev server, build pipeline, config assembly
- **React + Vite** — standalone affiliate landing pages under `_tool-recommends/`
- **GitHub Pages** — deployment via GitHub Actions

## Local Development

```bash
# Full dev environment (Jekyll + tool-recommend auto-sync)
bash ./dev.sh

# Jekyll only
bundle exec jekyll serve --baseurl '/blog'

# Gulp dev server (with BrowserSync + live reload)
gulp
```

## Build

```bash
# Production build
gulp build

# Build affiliate landing pages
./build-tool-recommends.sh
```

## New Post

```bash
./initpost.sh -c "My Post Title"
```

## Project Structure

```
_posts/          # Blog posts (YYYY-MM-DD-title.md)
_authors/        # Author collection
category/        # Category pages
_layouts/        # Liquid templates
_sass/           # Theme styles
src/yml/         # Config partials (assembled into _config.yml by Gulp)
_tool-recommends/ # React/Vite affiliate landing pages
```

> Do not edit `_config.yml` directly — edit files in `src/yml/` instead.

## Credits

Theme forked from [Jekflix Template](https://github.com/thiagorossener/jekflix-template) by [Thiago Rossener](https://rossener.com/), available under the [MIT License](https://github.com/thiagorossener/jekflix-template/blob/master/LICENSE).
