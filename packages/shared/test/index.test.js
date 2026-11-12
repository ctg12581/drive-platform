// packages/shared/test/index.test.js
// 运行：node --test packages/shared/test
import test from 'node:test'
import assert from 'node:assert/strict'

import { formatLocalTime, isUrl, isImageUrl, isTokenExpired } from '../src/index.js'

function makeToken(payload) {
  const body = Buffer.from(JSON.stringify(payload)).toString('base64')
  return `header.${body}.signature`
}

test('formatLocalTime: 空值返回空串，非法值原样返回', () => {
  assert.equal(formatLocalTime(''), '')
  assert.equal(formatLocalTime(null), '')
  assert.equal(formatLocalTime('not-a-date'), 'not-a-date')
})

test('formatLocalTime: 支持占位符替换', () => {
  const out = formatLocalTime('2020-01-02T03:04:05Z', 'YYYY-MM-DD')
  assert.equal(out, '2020-01-02')
})

test('isTokenExpired: 未来有效、过去过期、异常按过期', () => {
  const future = Math.floor(Date.now() / 1000) + 3600
  const past = Math.floor(Date.now() / 1000) - 3600
  assert.equal(isTokenExpired(makeToken({ exp: future })), false)
  assert.equal(isTokenExpired(makeToken({ exp: past })), true)
  assert.equal(isTokenExpired('garbage'), true)
  assert.equal(isTokenExpired(''), true)
})

test('isUrl: 识别 http(s) 与站内绝对路径', () => {
  assert.equal(isUrl('https://example.com/a.png'), true)
  assert.equal(isUrl('/assets/a.png'), true)
  assert.equal(isUrl('🚀'), false)
  assert.equal(isUrl(''), false)
})

test('isImageUrl: 识别 data:image 与常见图片后缀', () => {
  assert.equal(isImageUrl('data:image/png;base64,AAAA'), true)
  assert.equal(isImageUrl('https://x/a.JPG'), true)
  assert.equal(isImageUrl('https://x/a.png?w=1'), true)
  assert.equal(isImageUrl('https://x/a.txt'), false)
})
