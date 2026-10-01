# RuoyiCRM frontend

This is the existing Vue 2 / Vue CLI 4 application. The verified local build toolchain is Node 24.21.0 and npm 11.19.0; `.nvmrc` pins the Node version. Use the committed `package-lock.json` and the official npm registry for repeatable installs.

```bash
cd ruoyi-ui
nvm use
npm ci --registry=https://registry.npmjs.org
npm run test:dependency-contract
npm run build:prod
npm run test:compression
npm run build:stage
npm run test:compression
```

`build:prod` and `build:stage` create `dist/` and precompressed `.gz` files for compressible JS, CSS, and HTML assets. The deployment server must send those files only with the correct `Content-Encoding: gzip` header. `npm run dev` starts the development server on port 80 and proxies API requests to port 8080.

Run `npm run lint` separately. The existing source has a large lint backlog; the command now checks actual source files and currently exits nonzero. Keep that result visible in CI until the violations are fixed without disabling rules or bulk formatting unrelated code.

The production dependency audit is `npm audit --omit=dev --registry=https://registry.npmjs.org`. At the checked lockfile revision it reports 0 critical, 0 high, 4 moderate, and 4 low findings, so the separate CI audit gate exits nonzero. Vue 2 has reached end of life; the build evidence does not establish frontend production readiness.
