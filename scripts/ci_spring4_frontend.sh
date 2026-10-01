#!/usr/bin/env bash
set -euo pipefail

mode="${1:-build}"
if [[ "$mode" != build && "$mode" != lint && "$mode" != audit && "$mode" != sbom ]]; then
  echo "Usage: $0 build|lint|audit|sbom" >&2
  exit 2
fi

node_major="$(node -p 'process.versions.node.split(".")[0]')"
npm_major="$(npm --version | cut -d. -f1)"
if [[ "$node_major" != 24 || "$npm_major" != 11 ]]; then
  echo "Frontend CI requires Node 24 and npm 11; found Node $(node --version), npm $(npm --version)" >&2
  exit 2
fi

cd "$(dirname "$0")/../ruoyi-ui"
export CI=1
npm ci --registry=https://registry.npmjs.org --no-audit --no-fund
npm run test:dependency-contract

if [[ "$mode" == sbom ]]; then
  mkdir -p ../target
  # The inherited Vue CLI tree has eslint-loader 2's old peer range;
  # report the locked graph without changing the installed resolution.
  npm sbom --package-lock-only --legacy-peer-deps --sbom-format cyclonedx \
    --sbom-type application > ../target/ui-bom.json
  python3 -c 'import json; d=json.load(open("../target/ui-bom.json")); assert d["bomFormat"] == "CycloneDX" and len(d["components"]) > 0'
elif [[ "$mode" == audit ]]; then
  npm audit --omit=dev --registry=https://registry.npmjs.org
elif [[ "$mode" == lint ]]; then
  npm run lint
else
  npm run build:prod
  npm run test:compression
  npm run build:stage
  npm run test:compression
fi
