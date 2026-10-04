#!/usr/bin/env node
/**
 * 由 skills/<技能名>/ 生成 skills/<技能名>.skill 打包件（ZIP）。
 *
 * 用法：
 *   node scripts/build-skills.mjs          # 生成 / 更新全部打包件
 *   node scripts/build-skills.mjs --check  # 仅校验打包件是否与目录一致，不一致则退出码 1
 *
 * 设计要点：
 * - 无第三方依赖（只用 Node 内置模块），仓库无需 package.json。
 * - 输出**确定性**：固定时间戳、固定条目顺序、固定压缩级别，
 *   因此 `--check` 可以精确判断"打包件是否为最新"。
 * - 只打包真实存在的文件（不生成幽灵空目录）。
 */

import { readdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs'
import { join, dirname, relative, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { deflateRawSync } from 'node:zlib'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const SKILLS_DIR = join(ROOT, 'skills')

// 固定时间戳 -> DOS 时间 0，DOS 日期 0x21 (1980-01-01)
const DOS_TIME = 0
const DOS_DATE = 0x21

/* ---------------------------------------------------------------- CRC32 */

const CRC_TABLE = (() => {
  const t = new Uint32Array(256)
  for (let i = 0; i < 256; i++) {
    let c = i
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    t[i] = c >>> 0
  }
  return t
})()

function crc32(buf) {
  let c = 0xffffffff
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}

/* ----------------------------------------------------------- 文件收集 */

/** 递归收集目录下所有文件，返回相对路径（用 / 分隔），已排序。 */
function collectFiles(dir) {
  const out = []
  const walk = (cur) => {
    for (const entry of readdirSync(cur, { withFileTypes: true }).sort((a, b) =>
      a.name < b.name ? -1 : a.name > b.name ? 1 : 0,
    )) {
      const abs = join(cur, entry.name)
      if (entry.isDirectory()) walk(abs)
      else if (entry.isFile()) out.push(relative(dir, abs).split(sep).join('/'))
    }
  }
  walk(dir)
  return out.sort()
}

/* -------------------------------------------------------------- ZIP 构建 */

function buildZip(entries) {
  const local = []
  const central = []
  let offset = 0

  for (const { name, data } of entries) {
    const nameBuf = Buffer.from(name, 'utf8')
    const crc = crc32(data)
    const deflated = deflateRawSync(data, { level: 9 })
    const useDeflate = deflated.length < data.length
    const payload = useDeflate ? deflated : data
    const method = useDeflate ? 8 : 0

    const lh = Buffer.alloc(30)
    lh.writeUInt32LE(0x04034b50, 0)
    lh.writeUInt16LE(20, 4) // version needed
    lh.writeUInt16LE(0, 6) // flags
    lh.writeUInt16LE(method, 8)
    lh.writeUInt16LE(DOS_TIME, 10)
    lh.writeUInt16LE(DOS_DATE, 12)
    lh.writeUInt32LE(crc, 14)
    lh.writeUInt32LE(payload.length, 18)
    lh.writeUInt32LE(data.length, 22)
    lh.writeUInt16LE(nameBuf.length, 26)
    lh.writeUInt16LE(0, 28)
    local.push(lh, nameBuf, payload)

    const ch = Buffer.alloc(46)
    ch.writeUInt32LE(0x02014b50, 0)
    ch.writeUInt16LE(0x031e, 4) // version made by: UNIX, 3.0
    ch.writeUInt16LE(20, 6) // version needed
    ch.writeUInt16LE(0, 8) // flags
    ch.writeUInt16LE(method, 10)
    ch.writeUInt16LE(DOS_TIME, 12)
    ch.writeUInt16LE(DOS_DATE, 14)
    ch.writeUInt32LE(crc, 16)
    ch.writeUInt32LE(payload.length, 20)
    ch.writeUInt32LE(data.length, 24)
    ch.writeUInt16LE(nameBuf.length, 28)
    ch.writeUInt16LE(0, 30) // extra len
    ch.writeUInt16LE(0, 32) // comment len
    ch.writeUInt16LE(0, 34) // disk number
    ch.writeUInt16LE(0, 36) // internal attrs
    ch.writeUInt32LE((0o100644 << 16) >>> 0, 38) // external attrs: -rw-r--r--
    ch.writeUInt32LE(offset, 42)
    central.push(ch, nameBuf)

    offset += lh.length + nameBuf.length + payload.length
  }

  const cd = Buffer.concat(central)
  const eocd = Buffer.alloc(22)
  eocd.writeUInt32LE(0x06054b50, 0)
  eocd.writeUInt16LE(0, 4)
  eocd.writeUInt16LE(0, 6)
  eocd.writeUInt16LE(entries.length, 8)
  eocd.writeUInt16LE(entries.length, 10)
  eocd.writeUInt32LE(cd.length, 12)
  eocd.writeUInt32LE(offset, 16)
  eocd.writeUInt16LE(0, 20)

  return Buffer.concat([...local, cd, eocd])
}

/* ------------------------------------------------------------------ main */

const checkOnly = process.argv.includes('--check')

const skillNames = readdirSync(SKILLS_DIR, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name)
  .sort()

const packed = new Set()
let stale = 0
let written = 0
let failed = 0

for (const name of skillNames) {
  const dir = join(SKILLS_DIR, name)
  const relFiles = collectFiles(dir)
  if (relFiles.length === 0) {
    console.warn(`skip  ${name}（目录为空）`)
    continue
  }

  const entries = relFiles.map((rel) => ({ name: rel, data: readFileSync(join(dir, rel)) }))
  const zip = buildZip(entries)
  const target = join(SKILLS_DIR, `${name}.skill`)
  packed.add(`${name}.skill`)

  if (checkOnly) {
    const current = existsSync(target) ? readFileSync(target) : null
    if (current && current.equals(zip)) {
      console.log(`ok      ${name}.skill  (${relFiles.length} files)`)
    } else {
      console.error(`STALE   ${name}.skill  — 与 ${name}/ 不一致，请运行 node scripts/build-skills.mjs`)
      stale++
    }
  } else {
    const current = existsSync(target) ? readFileSync(target) : null
    const changed = !current || !current.equals(zip)
    writeFileSync(target, zip)
    console.log(`${changed ? 'write' : 'keep '}  ${name}.skill  (${relFiles.length} files, ${zip.length} bytes)`)
    written++
  }
}

// 检查孤儿打包件：源目录已不存在的 .skill
for (const f of readdirSync(SKILLS_DIR)) {
  if (!f.endsWith('.skill') || packed.has(f)) continue
  console.error(`ORPHAN  skills/${f} — 没有对应的技能目录，请删除`)
  failed++
}

if (checkOnly) {
  if (stale || failed) {
    console.error(`\n✗ 打包件校验失败：${stale} 个过期，${failed} 个孤儿。`)
    process.exit(1)
  }
  console.log(`\n✓ 全部打包件均为最新（共 ${packed.size} 个）。`)
} else {
  console.log(`\n✓ 已处理 ${written} 个打包件${failed ? `，${failed} 个孤儿待清理` : ''}。`)
  if (failed) process.exit(1)
}
