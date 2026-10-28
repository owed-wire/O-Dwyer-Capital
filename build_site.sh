#!/usr/bin/env bash
# Cloudflare Pages build step: copy the public website into dist/, leaving out the
# publishing scripts, docs, page templates and repo config so they aren't served.
# Cloudflare Pages settings: build command "bash build_site.sh", output directory "dist".
set -euo pipefail
cd "$(dirname "$0")"

rm -rf dist
mkdir dist

tar -cf - \
  --exclude=./dist \
  --exclude=./.git \
  --exclude=./.github \
  --exclude=./templates \
  --exclude='__pycache__' \
  --exclude='*.py' \
  --exclude='*.md' \
  --exclude=./requirements.txt \
  --exclude=./analyzer_output.txt \
  --exclude=./pyproject.toml \
  --exclude=./vercel.json \
  --exclude=./.vercelignore \
  --exclude=./.gitignore \
  --exclude=./.gitattributes \
  --exclude=./build_site.sh \
  . | tar -xf - -C dist

echo "Copied $(find dist -type f | wc -l) files to dist/"
