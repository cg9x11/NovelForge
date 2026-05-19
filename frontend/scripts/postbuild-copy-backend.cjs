const fs = require('fs')
const path = require('path')

const root = path.resolve(__dirname, '..')
const distWeb = path.resolve(root, 'dist-web')
const backendSrc = path.resolve(root, '..', 'backend')
const backendDst = path.join(distWeb, 'backend')

if (!fs.existsSync(distWeb)) {
  console.warn('[postbuild:web] dist-web missing, skip copy backend')
  process.exit(0)
}

if (!fs.existsSync(backendSrc)) {
  console.warn('[postbuild:web] backend source missing, skip copy backend')
  process.exit(0)
}

fs.rmSync(backendDst, { recursive: true, force: true })
fs.mkdirSync(backendDst, { recursive: true })

for (const name of fs.readdirSync(backendSrc)) {
  const src = path.join(backendSrc, name)
  const dst = path.join(backendDst, name)
  fs.cpSync(src, dst, { recursive: true })
}

console.log('[postbuild:web] backend copied to dist-web/backend')

