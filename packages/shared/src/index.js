// @drive/shared —— DRIVE 平台前端共享工具库
// 统一维护用户端（apps/web）与管理后台（apps/admin）中重复的时间格式化、
// 请求封装、头像/图片判断与本地缓存读写逻辑，避免两份实现各自漂移。

/**
 * 将 UTC / ISO 时间字符串转换为设备本地时区，并按 pattern 输出。
 * 支持占位符：YYYY / MM / DD / HH / mm / ss。
 * @param {string} isoString 后端返回的时间字符串
 * @param {string} pattern 输出格式，默认 "MM-DD HH:mm"
 * @returns {string}
 */
export function formatLocalTime(isoString, pattern = 'MM-DD HH:mm') {
  if (!isoString) return ''
  try {
    const date = new Date(isoString)
    if (Number.isNaN(date.getTime())) return isoString

    const tokens = {
      YYYY: String(date.getFullYear()),
      MM: String(date.getMonth() + 1).padStart(2, '0'),
      DD: String(date.getDate()).padStart(2, '0'),
      HH: String(date.getHours()).padStart(2, '0'),
      mm: String(date.getMinutes()).padStart(2, '0'),
      ss: String(date.getSeconds()).padStart(2, '0'),
    }
    return pattern.replace(/YYYY|MM|DD|HH|mm|ss/g, (token) => tokens[token])
  } catch (err) {
    console.error('时间转换出错:', err)
    return isoString
  }
}

/**
 * 判断 JWT Token 是否已过期（解析失败按已过期处理）。
 * @param {string} token
 * @returns {boolean}
 */
export function isTokenExpired(token) {
  if (!token) return true
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(
      decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join(''),
      ),
    )
    return payload.exp < Math.floor(Date.now() / 1000)
  } catch {
    return true
  }
}

/**
 * 判断一个头像/资源字段是否为 URL（http(s) 或站内绝对路径），
 * 否则视为 Emoji 文本。
 * @param {unknown} value
 * @returns {boolean}
 */
export function isUrl(value) {
  if (typeof value !== 'string' || !value) return false
  return /^(https?:\/\/|\/)/i.test(value)
}

/**
 * 判断消息文本/链接是否为图片（data:image 内联图或常见图片后缀，含查询串）。
 * @param {unknown} value
 * @returns {boolean}
 */
export function isImageUrl(value) {
  if (typeof value !== 'string' || !value) return false
  return value.startsWith('data:image/') || /\.(jpe?g|png|gif|webp)(\?.*)?$/i.test(value)
}

/**
 * 创建 fetch 封装：自动补全 baseURL、附带 Bearer Token、
 * FormData 自动处理 Content-Type、401 时触发 onUnauthorized。
 *
 * @param {object} [opts]
 * @param {string} [opts.baseURL] 后端地址
 * @param {() => string} [opts.getToken] 读取当前 token
 * @param {(res: Response) => void} [opts.onUnauthorized] 401 回调（如登出 + 跳转）
 * @returns {(endpoint: string, options?: RequestInit) => Promise<Response>}
 */
export function createApiFetch({ baseURL = '', getToken, onUnauthorized } = {}) {
  return async function apiFetch(endpoint, options = {}) {
    const headers = { ...options.headers }
    const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
    if (options.body != null && !isFormData && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json'
    }

    const token = typeof getToken === 'function' ? getToken() : ''
    if (token) headers.Authorization = `Bearer ${token}`

    const response = await fetch(`${baseURL}${endpoint}`, { ...options, headers })
    if (response.status === 401 && typeof onUnauthorized === 'function') {
      onUnauthorized(response)
    }
    return response
  }
}

/**
 * 安全地读取并反序列化 localStorage 中的 JSON。
 * @template T
 * @param {string} key
 * @param {T} [fallback]
 * @returns {T}
 */
export function readJSON(key, fallback = null) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch (err) {
    console.warn(`读取本地缓存 ${key} 失败:`, err)
    return fallback
  }
}

/**
 * 安全地将值序列化为 JSON 写入 localStorage。
 * @param {string} key
 * @param {unknown} value
 */
export function writeJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (err) {
    console.warn(`写入本地缓存 ${key} 失败:`, err)
  }
}
