// Prerender a tool-recommend product after `vite build` + `vite build --ssr`.
// Run from the product directory: node ../shared/prerender.mjs
// Expects build/index.html (client) and build-ssr/entry-server.{mjs,js} exporting
// render() -> { html, seo: { title, description, url, image } }.
import { existsSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const clientDir = resolve("build");
const ssrEntry = ["entry-server.mjs", "entry-server.js"]
  .map((file) => resolve("build-ssr", file))
  .find((file) => existsSync(file));
if (!ssrEntry) {
  throw new Error("build-ssr/entry-server.{mjs,js} not found; run vite build --ssr first");
}

const escapeAttr = (value) =>
  String(value)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

function headTags(seo) {
  const required = ["title", "description", "url"];
  const missing = required.filter((key) => !seo?.[key]);
  if (missing.length) {
    throw new Error(`seo config missing: ${missing.join(", ")}`);
  }
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: seo.title,
    description: seo.description,
    url: seo.url,
  };
  const tags = [
    `<meta name="description" content="${escapeAttr(seo.description)}" />`,
    `<link rel="canonical" href="${escapeAttr(seo.url)}" />`,
    `<meta property="og:type" content="website" />`,
    `<meta property="og:title" content="${escapeAttr(seo.title)}" />`,
    `<meta property="og:description" content="${escapeAttr(seo.description)}" />`,
    `<meta property="og:url" content="${escapeAttr(seo.url)}" />`,
    `<meta name="twitter:card" content="summary_large_image" />`,
  ];
  if (seo.image) {
    tags.push(
      `<meta property="og:image" content="${escapeAttr(seo.image)}" />`,
      `<meta name="twitter:image" content="${escapeAttr(seo.image)}" />`,
    );
  }
  const safeJson = JSON.stringify(jsonLd).replace(/</g, "\\u003c");
  tags.push(`<script type="application/ld+json">${safeJson}</script>`);
  return tags.join("\n    ");
}

const { render } = await import(pathToFileURL(ssrEntry).href);
const { html, seo } = render();

const indexPath = resolve(clientDir, "index.html");
const template = readFileSync(indexPath, "utf8");
const emptyRoot = '<div id="root"></div>';
if (!template.includes(emptyRoot) || !template.includes("</head>")) {
  throw new Error(`${indexPath}: expected an empty #root and a </head>`);
}

const output = template
  .replace("</head>", `    ${headTags(seo)}\n  </head>`)
  .replace(emptyRoot, `<div id="root">${html}</div>`);

writeFileSync(indexPath, output);
rmSync(resolve("build-ssr"), { recursive: true, force: true });
console.log(`prerendered ${indexPath} (${html.length} chars)`);
