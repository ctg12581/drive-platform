// src/utils/userProfile.js
// 用户主页数据（资料 + TA 的动态）属于读多写少，统一走 60s 缓存，避免重复点开反复请求。
import { apiFetch } from './api'
import { cachedFetch } from './cache'

/**
 * @param {string} targetUsername
 * @param {{ force?: boolean }} [options]
 * @returns {Promise<{ user: object, posts: any[] }>}
 */
export function fetchUserProfile(targetUsername, { force = false } = {}) {
  return cachedFetch(
    `profile:${targetUsername}`,
    async () => {
      const [profileRes, postsRes] = await Promise.all([
        apiFetch(`/auth/profile/${targetUsername}`),
        apiFetch(`/moments/user/${targetUsername}`),
      ])
      if (!profileRes.ok || !postsRes.ok) {
        throw new Error('加载用户数据失败')
      }
      const [user, userPosts] = await Promise.all([profileRes.json(), postsRes.json()])
      return { user, posts: userPosts.moments || [] }
    },
    { ttl: 60000, force },
  )
}
