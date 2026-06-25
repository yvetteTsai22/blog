# Design Spec: /my-affiliate/ Hidden Tools Listing Page

**Date:** 2026-06-25  
**Status:** Approved

---

## Overview

A hidden page at `/my-affiliate/` that lists all recommended affiliate tools in full detail. Accessible only via direct URL — not linked from navigation, excluded from sitemap, and marked noindex for search engines.

---

## Goals

- Provide a single page to view all recommended tools at a glance
- Not discoverable except by direct URL share
- Show full product details for each tool (name, price, rating, benefits, social proof, affiliate link)
- Easy to update as new tools are added

---

## Files

| File | Purpose |
|------|---------|
| `_data/tools.yml` | Central data source — one entry per tool |
| `my-affiliate.html` | Jekyll page rendered at `/my-affiliate/` |

No new layouts, no new CSS frameworks. Reuses the existing `page` layout.

---

## Data Schema (`_data/tools.yml`)

Each tool entry:

```yaml
- name: string               # Product display name
  description: string        # Short subheadline / pitch
  price: string              # e.g. "$37"
  price_note: string         # e.g. "one-time payment — no monthly fees"
  rating: string             # e.g. "4.9"
  user_count: string         # e.g. "90,000+"
  guarantee: string          # e.g. "60" (days)
  benefits:
    - string
    - string
  social_proof:
    - value: string          # e.g. "50,000+"
      label: string          # e.g. "Active Users"
  affiliate_url: string      # Direct affiliate link
  landing_url: string        # Local landing page path e.g. /blog/tool-recommend/instadoodle/
  image_url: string          # Product image URL
  cta_text: string           # e.g. "Get InstaDoodle Now"
```

Initial entries populated from existing TypeScript configs:
- `instadoodle` — real data (price $37, rating 4.9, affiliateUrl, etc.)
- `product-1` — placeholder data from `productConfig`
- `product-2` — placeholder data from `productConfig`

---

## Page (`my-affiliate.html`)

### Front matter

```yaml
---
layout: page
title: My Recommended Tools
permalink: /my-affiliate/
sitemap: false
robots: noindex
---
```

### Discoverability controls

- `sitemap: false` — excluded from Jekyll sitemap plugin
- `<meta name="robots" content="noindex, nofollow">` — requires a one-line addition to `_includes/head.html`:
  ```liquid
  {% if page.robots %}<meta name="robots" content="{{ page.robots }}">{% endif %}
  ```
  Then `robots: noindex, nofollow` in the page front matter triggers it. No other pages are affected.
- Not added to any navigation config

### Card structure (per tool)

Each tool in `site.data.tools` renders as:

```
┌─────────────────────────────────────────────┐
│  [Product Image]                            │
│  Tool Name                  ★ rating  price │
│  Description                                │
│  ✓ Benefit 1                                │
│  ✓ Benefit 2                                │
│  ✓ Benefit 3                                │
│  ─────────────────────────────────          │
│  user_count users · guarantee-day guarantee │
│  [  → cta_text  ] (affiliate_url)           │
│  [ View landing page ]                      │
└─────────────────────────────────────────────┘
```

Cards stack vertically. Styled with minimal inline styles (no external CSS dependency).

### Liquid template sketch

```liquid
{% for tool in site.data.tools %}
<div class="tool-card">
  <img src="{{ tool.image_url }}" alt="{{ tool.name }}">
  <div class="tool-info">
    <h2>{{ tool.name }} <span>★ {{ tool.rating }}</span> <span>{{ tool.price }}</span></h2>
    <p>{{ tool.description }}</p>
    <ul>
      {% for benefit in tool.benefits %}
        <li>✓ {{ benefit }}</li>
      {% endfor %}
    </ul>
    <div class="tool-stats">
      {% for stat in tool.social_proof %}
        <span>{{ stat.value }} {{ stat.label }}</span>
      {% endfor %}
      {% if tool.guarantee %}
        <span>{{ tool.guarantee }}-day guarantee</span>
      {% endif %}
    </div>
    <a href="{{ tool.affiliate_url }}" target="_blank" rel="noopener noreferrer">
      → {{ tool.cta_text }}
    </a>
    {% if tool.landing_url %}
      <a href="{{ site.baseurl }}{{ tool.landing_url }}">View landing page</a>
    {% endif %}
  </div>
</div>
{% endfor %}
```

---

## What Does NOT Change

- No edits to `_config.yml`
- No edits to any navigation include
- No edits to existing product React apps
- No new layout files
- No new CSS framework

## What Changes Beyond the Two New Files

- `_includes/head.html` — one line added: `{% if page.robots %}<meta name="robots" content="{{ page.robots }}">{% endif %}`

---

## Adding Future Tools

1. Add entry to `_data/tools.yml`
2. Deploy — the page auto-updates

No code changes required.
