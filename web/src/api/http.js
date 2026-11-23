export const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
).replace(/\/+$/, '')

/**
 * 统一处理 JSON 接口和错误。
 * 后端错误通常返回 { detail: "..." } 或 { msg: "..." }。
 */
export async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  let body = {}

  try {
    body = await response.json()
  } catch {
    // 非 JSON 响应，保留空对象
  }

  if (!response.ok) {
    const error = new Error(
      body.detail || body.msg || `请求失败 (${response.status})`
    )
    error.status = response.status
    error.body = body
    throw error
  }

  return body
}