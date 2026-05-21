import fs from 'node:fs'
import path from 'node:path'

const root = process.cwd()
const target = path.resolve(root, 'out-dev')
const allowed = path.resolve(root)

if (!target.startsWith(allowed + path.sep)) {
  throw new Error(`Refuse to clean path outside frontend workspace: ${target}`)
}

if (!fs.existsSync(target)) process.exit(0)

const stale = path.resolve(root, `.out-dev-stale-${Date.now()}`)

try {
  fs.renameSync(target, stale)
} catch (error) {
  if (error?.code === 'EPERM' || error?.code === 'EBUSY') {
    console.warn(`[clean:dev] out-dev locked by running process; reuse directory: ${target}`)
    process.exit(0)
  }
  throw error
}

for (let attempt = 1; attempt <= 5; attempt += 1) {
  try {
    fs.rmSync(stale, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 })
    process.exit(0)
  } catch (error) {
    if (!['EPERM', 'EBUSY', 'ENOTEMPTY'].includes(error?.code)) throw error
    if (attempt === 5) {
      console.warn(`[clean:dev] stale out-dev still locked; left for later cleanup: ${stale}`)
      process.exit(0)
    }
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, attempt * 200)
  }
}
