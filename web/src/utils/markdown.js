import DOMPurify from 'dompurify'
import { marked } from 'marked'

marked.setOptions({
  gfm: true,
  breaks: true,
})

DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A') {
    node.setAttribute('target', '_blank')
    node.setAttribute('rel', 'noopener noreferrer')
  }

  if (node.tagName === 'IMG') {
    node.setAttribute('loading', 'lazy')
    node.setAttribute('decoding', 'async')
    node.setAttribute('referrerpolicy', 'no-referrer')
  }
})

/**
 * 把 Markdown 转成安全的 HTML。
 * 模型输出属于不可信内容，必须经过 DOMPurify 消毒后再 v-html。
 */
export function renderMarkdown(text) {
  if (!text) return ''

  try {
    const html = marked.parse(text)
    return DOMPurify.sanitize(html, {
      FORBID_TAGS: [
        'style',
        'iframe',
        'form',
        'input',
        'button',
        'textarea',
        'select',
        'object',
        'embed',
      ],
      FORBID_ATTR: ['style'],
      ADD_ATTR: ['target', 'rel', 'loading', 'decoding', 'referrerpolicy'],
    })
  } catch {
    const escaped = String(text)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
    return `<p>${escaped}</p>`
  }
}