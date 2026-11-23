import { fetchEventSource } from '@microsoft/fetch-event-source'
import { API_BASE } from './http'

/**
 * 调用后端的 SSE 聊天接口。
 *
 * @param {Object} options
 * @param {string} options.question 用户问题
 * @param {string} options.token JWT
 * @param {AbortSignal} options.signal 用于“停止生成”
 * @param {(text: string) => void} options.onDelta 收到一段文本
 * @param {(items: Array) => void} options.onProducts 收到结构化商品列表
 * @param {(error: Error) => void} options.onError 业务错误
 * @param {() => void} options.onDone 流结束
 */
export async function streamChat({
  question,
  token,
  signal,
  onDelta,
  onProducts,
  onError,
  onDone,
}) {
  let finished = false

  await fetchEventSource(
    `${API_BASE}/assistant/chat?question=${encodeURIComponent(question)}`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'text/event-stream',
      },
      signal,
      // 页面切到后台时保持流式连接
      openWhenHidden: true,

      async onopen(response) {
        const contentType = response.headers.get('content-type') || ''

        if (response.ok && contentType.includes('text/event-stream')) {
          return
        }

        let message = `请求失败 (${response.status})`
        try {
          const body = await response.json()
          message = body.detail || body.msg || message
        } catch {
          // 非 JSON 响应，保留默认错误
        }

        const error = new Error(message)
        error.status = response.status
        throw error
      },

      onmessage(event) {
        if (!event.data) return

        let payload
        try {
          payload = JSON.parse(event.data)
        } catch {
          return
        }

        if (payload.error) {
          onError?.(new Error(payload.error))
          return
        }

        // 后端可以发送：
        // {"type":"products","items":[{ id, name, image, price, variant_id }]}
        if (payload.type === 'products' && Array.isArray(payload.items)) {
          onProducts?.(payload.items)
          return
        }

        // 兼容直接返回 products 数组的情况
        if (Array.isArray(payload.products)) {
          onProducts?.(payload.products)
          return
        }

        if (payload.content === '[DONE]') {
          finished = true
          onDone?.()
          return
        }

        if (payload.content) {
          onDelta(payload.content)
        }
      },

      onclose() {
        if (!finished) {
          finished = true
          onDone?.()
        }
      },

      onerror(error) {
        // 抛出后停止 fetch-event-source 的自动重试，
        // 避免重复提交同一个问题。
        throw error
      },
    }
  )
}