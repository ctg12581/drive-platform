// src/utils/cache.js
// 极简 TTL 内存缓存：用于「读多写少」的 GET 数据，避免每次进入页面都重复请求。
// - 缓存的是 Promise：并发调用会复用同一个请求（去重）。
// - 命中且未过期直接返回；过期或 force 时重新请求。
const store = new Map()

/**
 * 带缓存的请求。
 * @template T
 * @param {string} key 缓存键
 * @param {() => Promise<T>} fetcher 真正发起请求的函数
 * @param {{ ttl?: number, force?: boolean }} [options] ttl 毫秒（默认 60s），force 强制刷新
 * @returns {Promise<T>}
 */
export function cachedFetch(key, fetcher, { ttl = 60000, force = false } = {}) {
  const now = Date.now()
  const hit = store.get(key)
  if (!force && hit && now - hit.ts < ttl) {
    return hit.promise
  }
  const promise = Promise.resolve().then(fetcher)
  store.set(key, { ts: now, promise })
  // 请求失败则清除缓存，避免把错误结果缓存下来
  promise.catch(() => {
    const cur = store.get(key)
    if (cur && cur.promise === promise) store.delete(key)
  })
  return promise
}

/** 按前缀失效缓存（不传则清空全部）。写操作后调用，保证数据新鲜。 */
export function invalidateCache(prefix = '') {
  if (!prefix) {
    store.clear()
    return
  }
  for (const key of Array.from(store.keys())) {
    if (key.startsWith(prefix)) store.delete(key)
  }
}
