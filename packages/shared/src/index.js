// @drive/shared —— DRIVE 平台前端共享工具库（骨架）
// 目标：把 web / admin 两个 Vue 应用中重复的请求封装、时间格式化、鉴权逻辑收敛到这里。
// 当前为可用的初始版本，后续可按需继续抽取 UI 组件。

/**
 * 将 UTC 字符串转换为设备本地时区的时间，并支持自定义格式。
 * @param {string} isoString 后端返回的 UTC 字符串，如 "2026-06-27T06:10:00Z"
 * @param {string} pattern 输出格式，默认 "MM-DD HH:mm"
 */
export function formatLocalTime(isoString, pattern = 'MM-DD HH:mm') {
  if (!isoString) return ''
  try {
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return isoString
    const yyyy = date.getFullYear()
    const mm = String(date.getMonth() + 1).padStart(2, '0')
    const dd = String(date.getDate()).padStart(2, '0')
    const hh = String(date.getHours()).padStart(2, '0')
    const min = String(date.getMinutes()).padStart(2, '0')
    const ss = String(date.getSeconds()).padStart(2, '0')
    return pattern
      .replace('YYYY', yyyy)
      .replace('MM', mm)
      .replace('DD', dd)
      .replace('HH', hh)
      .replace('mm', min)
      .replace('ss', ss)
  } catch (err) {
    console.error('时间转换出错:', err)
    return isoString
  }
}

/**
 * 创建一个 fetch 封装：自动补全 baseURL、附带 Bearer Token、FormData 自动处理 Content-Type、
 * 401 时触发 onUnauthorized。
 *
 * @param {object} opts
 * @param {string} opts.baseURL 后端地址
 * @param {() => string} [opts.getToken] 读取当前 token
 * @param {(res: Response) => void} [opts.onUnauthorized] 401 回调（如登出+跳转）
 * @returns {(endpoint: string, options?: RequestInit) => Promise<Response>}
 */
export function createApiFetch({ baseURL, getToken, onUnauthorized }) {
  return async function apiFetch(endpoint, options = {}) {
    const headers = { ...options.headers }
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
    }
    const token = getToken ? getToken() : ''
    if (token) headers['Authorization'] = `Bearer ${token}`

    const response = await fetch(`${baseURL}${endpoint}`, { ...options, headers })
    if (response.status === 401 && onUnauthorized) {
      onUnauthorized(response)
    }
    return response
  }
}
