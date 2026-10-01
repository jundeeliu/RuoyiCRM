'use strict'

const assert = require('assert')
const fs = require('fs')
const path = require('path')
const zlib = require('zlib')

const root = path.resolve(__dirname, '../dist')
let verified = 0

function visit(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const filename = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      visit(filename)
    } else if (entry.isFile() && filename.endsWith('.gz')) {
      const gzip = fs.readFileSync(filename)
      const original = fs.readFileSync(filename.slice(0, -3))
      assert.deepStrictEqual(zlib.gunzipSync(gzip), original, filename)
      assert.ok(gzip.length / original.length < 0.8, filename)
      verified++
    }
  }
}

visit(root)
assert.ok(verified > 0, 'No precompressed assets found')
process.stdout.write(`Verified ${verified} precompressed assets\n`)
