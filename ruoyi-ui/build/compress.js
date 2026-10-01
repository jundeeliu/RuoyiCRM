'use strict'

// Produce the same optional precompressed assets without Webpack 4's MD4
// hashing path, which is unavailable in current Node/OpenSSL versions.
const fs = require('fs')
const path = require('path')
const zlib = require('zlib')

const root = path.resolve(__dirname, '../dist')
const minRatio = 0.8
let compressed = 0

function visit(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const filename = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      visit(filename)
    } else if (entry.isFile() && /\.(?:js|css|html)$/i.test(entry.name)) {
      const source = fs.readFileSync(filename)
      const gzip = zlib.gzipSync(source, { level: 9 })
      if (gzip.length / source.length < minRatio) {
        fs.writeFileSync(`${filename}.gz`, gzip)
        compressed++
      }
    }
  }
}

visit(root)
process.stdout.write(`Created ${compressed} precompressed assets in ${root}\n`)
