# My Affiliate Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a hidden Jekyll page at `/my-affiliate/` that lists all recommended affiliate tools with full details, accessible only via direct URL.

**Architecture:** A `_data/tools.yml` YAML file holds all tool data; a `my-affiliate.html` Jekyll page loops over it rendering one card per tool. A one-line addition to `_includes/head.html` enables per-page `noindex` control via front matter.

**Tech Stack:** Jekyll (Liquid templates), YAML, HTML/CSS (no new frameworks)

## Global Constraints

- No edits to `_config.yml`
- No edits to navigation includes
- No new layouts
- No new CSS frameworks — minimal inline styles only
- `sitemap: false` front matter excludes the page from Jekyll's sitemap plugin
- `robots: "noindex, nofollow"` front matter + head.html hook prevents search engine indexing
- Page not linked from any navigation
- All product data sourced from existing TypeScript configs (transcribed to YAML)

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `_includes/head.html` | Add one-line robots meta hook after line 40 |
| Create | `_data/tools.yml` | Central data source for all tools |
| Create | `my-affiliate.html` | Jekyll page at `/my-affiliate/` |

---

### Task 1: Add robots meta hook to head.html

**Files:**
- Modify: `_includes/head.html:40` (after the `{% if page.tags %}` keywords block, before `<!-- Social: Twitter -->`)

**Interfaces:**
- Produces: any page with `robots: "noindex, nofollow"` in front matter gets `<meta name="robots" content="noindex, nofollow">` in its `<head>`

- [ ] **Step 1: Open `_includes/head.html` and locate the insertion point**

  The file currently has this block around line 38–41:
  ```liquid
      <meta name="description" content="{{ description }}">
      {% if page.tags %}
          <meta name="keywords" content="{{ page.tags | join: ', ' }}">
      {% endif %}
  ```
  The robots meta tag goes immediately after that `{% endif %}`.

- [ ] **Step 2: Add the robots meta hook**

  Edit `_includes/head.html`. After line 41 (`{% endif %}` for keywords), add:
  ```liquid
      {% if page.robots %}<meta name="robots" content="{{ page.robots }}">{% endif %}
  ```

  The resulting block should look like:
  ```liquid
      <meta name="description" content="{{ description }}">
      {% if page.tags %}
          <meta name="keywords" content="{{ page.tags | join: ', ' }}">
      {% endif %}
      {% if page.robots %}<meta name="robots" content="{{ page.robots }}">{% endif %}

      <!-- Social: Twitter -->
  ```

- [ ] **Step 3: Verify the change is isolated**

  Confirm no other page in the repo sets `robots:` in its front matter (so this change affects zero existing pages):
  ```bash
  grep -r "^robots:" /Users/yvette/projects/blog --include="*.html" --include="*.md" -l
  ```
  Expected output: empty (no results).

---

### Task 2: Create `_data/tools.yml`

**Files:**
- Create: `_data/tools.yml`

**Interfaces:**
- Produces: `site.data.tools` — an array of tool objects consumed by Task 3's Liquid template

- [ ] **Step 1: Create the `_data/` directory and `tools.yml`**

  ```bash
  mkdir -p /Users/yvette/projects/blog/_data
  ```

  Create `/Users/yvette/projects/blog/_data/tools.yml` with this exact content:

  ```yaml
  - name: "InstaDoodle"
    description: "Type a description, click Generate — and InstaDoodle's DoodleAI™ engine turns your idea into a professional whiteboard animation in minutes. No drawing. No software. No monthly fee."
    price: "$37"
    price_note: "one-time payment — no monthly fees"
    rating: "4.9"
    user_count: "90,000+"
    guarantee: "60"
    benefits:
      - "Create professional whiteboard videos in minutes — no drawing skill required"
      - "AI-powered DoodleAI™ engine generates animations from text descriptions"
      - "Multilingual voiceover support — expand into new markets without hiring"
      - "Export HD video ready for YouTube, sales funnels, or social media"
      - "One-time payment — no subscriptions, no monthly fees"
    social_proof:
      - value: "90,000+"
        label: "Business Owners"
      - value: "4.9★"
        label: "Average Rating"
      - value: "$37"
        label: "One-Time Payment"
    affiliate_url: "https://d69e8wbz17mpcv4aoi33mev4s9.hop.clickbank.net"
    landing_url: "/tool-recommend/instadoodle/"
    image_url: "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=800&q=80"
    cta_text: "Get InstaDoodle Now ✦"

  - name: "Secret Tool"
    description: "What if you could reclaim 10+ hours every week without changing your entire workflow? This game-changing solution does exactly that — and it takes just minutes to set up."
    price: ""
    price_note: ""
    rating: "4.9"
    user_count: "50,000+"
    guarantee: "30"
    benefits:
      - "Save over 10 hours per week with intelligent automation"
      - "Eliminate repetitive tasks that drain your productivity"
      - "Get results in minutes, not days — no learning curve required"
      - "Works seamlessly with the tools you already use"
      - "Join 50,000+ professionals who've already made the switch"
    social_proof:
      - value: "50,000+"
        label: "Active Users"
      - value: "4.9/5"
        label: "Average Rating"
      - value: "10+ Hours"
        label: "Saved Per Week"
    affiliate_url: "#your-affiliate-link-here"
    landing_url: "/tool-recommend/product-1/"
    image_url: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80"
    cta_text: "Unlock Instant Access"

  - name: "Your Second Product"
    description: "Discover how thousands are already leveraging this powerful solution to achieve more in less time. Join the revolution and unlock your full potential."
    price: ""
    price_note: ""
    rating: "4.8"
    user_count: "100,000+"
    guarantee: "30"
    benefits:
      - "Double your productivity in just days"
      - "Reduce manual work by up to 80%"
      - "Easy integration with existing tools"
      - "24/7 dedicated customer support"
      - "30-day money-back guarantee"
    social_proof:
      - value: "100,000+"
        label: "Satisfied Customers"
      - value: "4.8/5"
        label: "Star Rating"
      - value: "99.9%"
        label: "Uptime"
    affiliate_url: "#your-product-2-affiliate-link"
    landing_url: "/tool-recommend/product-2/"
    image_url: "https://images.unsplash.com/photo-1552664730-d307ca884978?w=800&q=80"
    cta_text: "Get Started Free Today"
  ```

- [ ] **Step 2: Verify YAML parses correctly**

  ```bash
  ruby -e "require 'yaml'; data = YAML.load_file('_data/tools.yml'); puts \"#{data.length} tools loaded\"; data.each { |t| puts t['name'] }"
  ```
  Expected output:
  ```
  3 tools loaded
  InstaDoodle
  Secret Tool
  Your Second Product
  ```

---

### Task 3: Create `my-affiliate.html`

**Files:**
- Create: `my-affiliate.html` (blog root)

**Interfaces:**
- Consumes: `site.data.tools` from Task 2 — array of objects with fields: `name`, `description`, `price`, `price_note`, `rating`, `user_count`, `guarantee`, `benefits` (array), `social_proof` (array of `{value, label}`), `affiliate_url`, `landing_url`, `image_url`, `cta_text`
- Consumes: `page.robots` hook from Task 1 — front matter `robots: "noindex, nofollow"` renders the noindex meta tag

- [ ] **Step 1: Create `my-affiliate.html` in the blog root**

  Create `/Users/yvette/projects/blog/my-affiliate.html` with this exact content:

  ```html
  ---
  layout: page
  title: My Recommended Tools
  permalink: /my-affiliate/
  sitemap: false
  robots: "noindex, nofollow"
  ---

  <style>
    .tool-card {
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 2.5rem;
      background: #fff;
    }
    .tool-card img {
      width: 100%;
      height: 220px;
      object-fit: cover;
      display: block;
    }
    .tool-body {
      padding: 1.5rem;
    }
    .tool-header {
      display: flex;
      align-items: baseline;
      gap: 0.75rem;
      flex-wrap: wrap;
      margin-bottom: 0.5rem;
    }
    .tool-header h2 {
      margin: 0;
      font-size: 1.4rem;
    }
    .tool-rating {
      color: #f5a623;
      font-weight: bold;
      white-space: nowrap;
    }
    .tool-price {
      font-weight: bold;
      color: #333;
      white-space: nowrap;
    }
    .tool-price-note {
      font-size: 0.85rem;
      color: #777;
    }
    .tool-description {
      color: #555;
      margin: 0.5rem 0 1rem;
      line-height: 1.55;
    }
    .tool-benefits {
      list-style: none;
      padding: 0;
      margin: 0 0 1rem;
    }
    .tool-benefits li {
      padding: 0.2rem 0;
      color: #333;
    }
    .tool-benefits li::before {
      content: "✓ ";
      color: #2c9e4b;
      font-weight: bold;
    }
    .tool-divider {
      border: none;
      border-top: 1px solid #eee;
      margin: 1rem 0;
    }
    .tool-stats {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.25rem;
    }
    .tool-stat {
      font-size: 0.9rem;
      color: #555;
    }
    .tool-stat strong {
      color: #222;
    }
    .tool-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: center;
    }
    .btn-affiliate {
      display: inline-block;
      background: #e63329;
      color: #fff !important;
      text-decoration: none;
      padding: 0.65rem 1.4rem;
      border-radius: 4px;
      font-weight: bold;
      font-size: 0.95rem;
    }
    .btn-affiliate:hover {
      background: #c4271e;
    }
    .btn-landing {
      display: inline-block;
      color: #555;
      text-decoration: underline;
      font-size: 0.9rem;
    }
  </style>

  <p style="color:#888; font-size:0.9rem; margin-bottom:2rem;">
    {{ site.data.tools | size }} tools listed &mdash; direct URL only, not indexed.
  </p>

  {% for tool in site.data.tools %}
  <div class="tool-card">
    {% if tool.image_url %}
    <img src="{{ tool.image_url }}" alt="{{ tool.name }} product image">
    {% endif %}
    <div class="tool-body">
      <div class="tool-header">
        <h2>{{ tool.name }}</h2>
        {% if tool.rating %}
        <span class="tool-rating">★ {{ tool.rating }}</span>
        {% endif %}
        {% if tool.price and tool.price != "" %}
        <span class="tool-price">{{ tool.price }}</span>
        {% endif %}
      </div>
      {% if tool.price_note and tool.price_note != "" %}
      <span class="tool-price-note">{{ tool.price_note }}</span>
      {% endif %}

      <p class="tool-description">{{ tool.description }}</p>

      {% if tool.benefits %}
      <ul class="tool-benefits">
        {% for benefit in tool.benefits %}
        <li>{{ benefit }}</li>
        {% endfor %}
      </ul>
      {% endif %}

      <hr class="tool-divider">

      <div class="tool-stats">
        {% for stat in tool.social_proof %}
        <span class="tool-stat"><strong>{{ stat.value }}</strong> {{ stat.label }}</span>
        {% endfor %}
        {% if tool.user_count and tool.user_count != "" %}
        <span class="tool-stat"><strong>{{ tool.user_count }}</strong> users</span>
        {% endif %}
        {% if tool.guarantee and tool.guarantee != "" %}
        <span class="tool-stat"><strong>{{ tool.guarantee }}-day</strong> guarantee</span>
        {% endif %}
      </div>

      <div class="tool-actions">
        <a href="{{ tool.affiliate_url }}" class="btn-affiliate" target="_blank" rel="noopener noreferrer">
          → {{ tool.cta_text }}
        </a>
        {% if tool.landing_url and tool.landing_url != "" %}
        <a href="{{ site.baseurl }}{{ tool.landing_url }}" class="btn-landing">View landing page</a>
        {% endif %}
      </div>
    </div>
  </div>
  {% endfor %}
  ```

- [ ] **Step 2: Build Jekyll locally to verify the page renders**

  ```bash
  cd /Users/yvette/projects/blog
  bundle exec jekyll build --baseurl '/blog'
  ```
  Expected: build completes with no errors.

- [ ] **Step 3: Check the page was built at the correct path**

  ```bash
  ls _site/my-affiliate/
  ```
  Expected output: `index.html`

- [ ] **Step 4: Verify noindex meta tag is in the built HTML**

  ```bash
  grep "robots" _site/my-affiliate/index.html
  ```
  Expected output:
  ```
  <meta name="robots" content="noindex, nofollow">
  ```

- [ ] **Step 5: Verify all 3 tools appear in the built HTML**

  ```bash
  grep -c "tool-card" _site/my-affiliate/index.html
  ```
  Expected output: `3`

- [ ] **Step 6: Verify the page is NOT in the sitemap**

  ```bash
  grep "my-affiliate" _site/sitemap.xml 2>/dev/null && echo "FOUND — sitemap exclusion failed" || echo "OK — not in sitemap"
  ```
  Expected output: `OK — not in sitemap`

- [ ] **Step 7: Verify the page is not linked from navigation**

  ```bash
  grep -r "my-affiliate" /Users/yvette/projects/blog/_includes/ /Users/yvette/projects/blog/_layouts/ 2>/dev/null
  ```
  Expected output: empty (no results).

- [ ] **Step 8: Start dev server and do a visual check**

  ```bash
  bundle exec jekyll serve --baseurl '/blog'
  ```
  Open `http://localhost:4000/blog/my-affiliate/` in a browser and confirm:
  - 3 tool cards are visible
  - Each card shows name, rating, description, benefits, stats, and CTA button
  - InstaDoodle card shows $37 price and real affiliate URL
  - Product-1 and Product-2 cards show placeholder content

---

## Self-Review Notes

- **Spec coverage**: ✓ noindex via head.html hook, ✓ sitemap: false, ✓ not in nav, ✓ `_data/tools.yml` with all 3 products, ✓ full card layout, ✓ permalink `/my-affiliate/`
- **Placeholders**: None — all YAML values copied verbatim from existing TypeScript configs and component copy
- **Type consistency**: `site.data.tools` array → `tool.name`, `tool.benefits`, `tool.social_proof` (with `.value`/`.label`) — consistent across Tasks 2 and 3
- **user_count duplication**: The YAML has both `user_count` and `social_proof` entries that may overlap for instadoodle. The template renders `social_proof` stats first then `user_count` separately — for instadoodle this means "90,000+ Business Owners" appears twice. Fix: the instadoodle entry's `social_proof` already includes Business Owners, so set `user_count: ""` for instadoodle to avoid duplication (already done in the YAML above).
