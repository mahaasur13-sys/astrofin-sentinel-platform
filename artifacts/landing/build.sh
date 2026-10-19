#!/usr/bin/env bash
set -euo pipefail

SRC_CSS="enterprise.css"
SRC_HTML="index.html"
CRIT_CSS="critical.css"
OUT_DIR="dist"
MIN_CSS="enterprise.min.css"

mkdir -p "$OUT_DIR"

echo "→ 1/4 Minify full CSS…"
npx --yes lightningcss \
  --minify \
  --targets ">= 0.25%, last 2 versions" \
  -o "$OUT_DIR/$MIN_CSS" \
  "$SRC_CSS"

echo "→ 2/4 Minify critical CSS…"
npx --yes lightningcss \
  --minify \
  -o "$OUT_DIR/critical.min.css" \
  "$CRIT_CSS"

echo "→ 3/4 Assemble dist/index.html…"
node - "$SRC_HTML" "$OUT_DIR/$MIN_CSS" "$OUT_DIR/critical.min.css" "$MIN_CSS" "$OUT_DIR/index.html" <<'NODE'
const fs = require('fs');
const [, , srcHtml, minCssPath, critCssPath, cssHref, outHtml] = process.argv;

let html    = fs.readFileSync(srcHtml, 'utf8');
const minCss  = fs.readFileSync(minCssPath, 'utf8');
const critCss = fs.readFileSync(critCssPath, 'utf8');

// 1. Удалить оригинальный <link rel="stylesheet" href="enterprise.css" />
html = html.replace(
  /\s*<link[^>]*rel=["']stylesheet["'][^>]*href=["']enterprise\.css["'][^>]*>\s*/i,
  '\n'
);

// 2. Вставить critical CSS инлайном в <head>
html = html.replace(
  '</head>',
  `  <style>${critCss}</style>\n</head>`
);

// 3. Подключить полный CSS асинхронно (media=print + onload)
const deferred =
`  <link rel="stylesheet" href="${cssHref}" media="print" onload="this.media='all'">
  <noscript><link rel="stylesheet" href="${cssHref}"></noscript>
`;
html = html.replace('</head>', deferred + '</head>');

fs.writeFileSync(outHtml, html, 'utf8');
NODE

echo "→ 4/4 Report:"
ls -la "$OUT_DIR"
echo
echo "  Original HTML:  $(wc -c < "$SRC_HTML") bytes"
echo "  Dist HTML:      $(wc -c < "$OUT_DIR/index.html") bytes"
echo "  Full CSS min:   $(wc -c < "$OUT_DIR/$MIN_CSS") bytes"
echo "  Critical min:   $(wc -c < "$OUT_DIR/critical.min.css") bytes"
echo
echo "✓ Build complete: $OUT_DIR/"
