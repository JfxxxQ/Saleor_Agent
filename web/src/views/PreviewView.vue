<script setup>
import { ref } from 'vue'
import MessageBubble from '@/components/MessageBubble.vue'

function productImage(label, from, to) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 480 480">
    <defs>
      <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="${from}" />
        <stop offset="1" stop-color="${to}" />
      </linearGradient>
    </defs>
    <rect width="480" height="480" fill="url(#g)" />
    <circle cx="380" cy="90" r="130" fill="rgba(255,255,255,.16)" />
    <circle cx="80" cy="420" r="90" fill="rgba(255,255,255,.1)" />
    <text x="42" y="414" font-family="Arial, sans-serif" font-size="52" font-weight="700" fill="rgba(255,255,255,.94)">${label}</text>
  </svg>`

  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

const products = [
  {
    id: 'preview-p1',
    name: 'Monospace Tee',
    description: '宽松版型，基础百搭',
    productType: 'Top',
    image: productImage('TEE', '#E85D2A', '#7B2B11'),
    price: { amount: 12, currency: 'USD' },
    price_max: { amount: 20, currency: 'USD' },
    variants: [
      { id: 'variant-ms-s', name: 'S', price: { amount: 20, currency: 'USD' } },
      { id: 'variant-ms-m', name: 'M', price: { amount: 20, currency: 'USD' } },
      { id: 'variant-ms-l', name: 'L', price: { amount: 20, currency: 'USD' } },
      { id: 'variant-ms-xl', name: 'XL', price: { amount: 20, currency: 'USD' } },
      { id: 'variant-ms-xxl', name: 'XXL', price: { amount: 12, currency: 'USD' } },
    ],
  },
  {
    id: 'preview-p2',
    name: 'Blue Polygon Shirt',
    description: '几何图案，偏街头风格',
    productType: 'Top',
    image: productImage('SHIRT', '#2B6CB0', '#123B63'),
    price: { amount: 30, currency: 'USD' },
    price_max: { amount: 30, currency: 'USD' },
    variants: [
      { id: 'variant-bp-s', name: 'S', price: { amount: 30, currency: 'USD' } },
      { id: 'variant-bp-m', name: 'M', price: { amount: 30, currency: 'USD' } },
      { id: 'variant-bp-l', name: 'L', price: { amount: 30, currency: 'USD' } },
    ],
  },
  {
    id: 'preview-p3',
    name: 'Dark Polygon Tee',
    description: '深色系，适合通勤',
    productType: 'Top',
    image: productImage('DARK', '#3B3A38', '#121110'),
    price: { amount: 20, currency: 'USD' },
    price_max: { amount: 20, currency: 'USD' },
    variants: [
      { id: 'variant-dp-m', name: 'M', price: { amount: 20, currency: 'USD' } },
      { id: 'variant-dp-l', name: 'L', price: { amount: 20, currency: 'USD' } },
    ],
  },
]

const sampleMessage = {
  id: 'preview-message',
  role: 'assistant',
  status: 'done',
  content: `## 我找到 3 件适合你的 T 恤

根据你的偏好，我筛选了这几件：

| 商品 | 特点 | 价格 |
| --- | --- | --- |
| Monospace Tee | 宽松版型，基础百搭 | $20.00 |
| Blue Polygon Shirt | 几何图案，偏街头 | $30.00 |
| Dark Polygon Tee | 深色系，适合通勤 | $20.00 |

> 库存和最终价格以结算页为准。

也可以直接对我说：\`帮我把 Monospace Tee 加入购物车\`。

需要我把哪一件加入购物车？`,
  products,
}

const toast = ref('')

function onProductAdd(product) {
  toast.value = `预览模式：实际会发送「帮我把「${product.name}」加入购物车」`
  setTimeout(() => {
    toast.value = ''
  }, 2600)
}
</script>

<template>
  <div class="preview-page">
    <header class="preview-header">
      <div>
        <p class="preview-eyebrow">DEV PREVIEW</p>
        <h1>Markdown 与商品卡片预览</h1>
      </div>
      <RouterLink class="preview-back" to="/chat">返回聊天</RouterLink>
    </header>

    <main class="preview-content">
      <p class="preview-note">
        开发环境预览页，不会调用后端。访问
        <code>/preview</code>
        查看 Markdown 和商品卡片效果。多规格商品需要先选择尺码，
        “加入购物车”按钮才可用。
      </p>

      <div class="preview-chat">
        <MessageBubble
          :message="sampleMessage"
          @product-add="onProductAdd"
        />
      </div>

      <p v-if="toast" class="preview-toast" role="status">{{ toast }}</p>
    </main>
  </div>
</template>

<style scoped>
.preview-page {
  min-height: 100dvh;
  background:
    radial-gradient(circle at 50% -10%, rgba(232, 93, 42, 0.07), transparent 40%),
    var(--bg);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  max-width: 940px;
  margin: 0 auto;
  padding: 28px 24px 18px;
}

.preview-eyebrow {
  margin: 0 0 6px;
  color: var(--primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.preview-header h1 {
  margin: 0;
  color: var(--text);
  font-size: 24px;
  letter-spacing: -0.03em;
}

.preview-back {
  flex: 0 0 auto;
  padding: 8px 13px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
}

.preview-back:hover {
  border-color: #d6ccc0;
  color: var(--text);
  text-decoration: none;
}

.preview-content {
  max-width: 940px;
  margin: 0 auto;
  padding: 0 24px 60px;
}

.preview-note {
  margin: 0 0 18px;
  padding: 10px 13px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.preview-note code {
  padding: 1px 5px;
  border-radius: 4px;
  background: #f2ede6;
  font-family: var(--font-mono);
  font-size: 11px;
}

.preview-chat {
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.preview-toast {
  position: fixed;
  bottom: 28px;
  left: 50%;
  max-width: min(90vw, 520px);
  margin: 0;
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--text);
  color: #fff;
  font-size: 12px;
  box-shadow: var(--shadow-float);
  transform: translateX(-50%);
}

@media (max-width: 768px) {
  .preview-header {
    align-items: flex-start;
    flex-direction: column;
    padding: 22px 16px 14px;
  }

  .preview-header h1 {
    font-size: 20px;
  }

  .preview-content {
    padding: 0 14px 40px;
  }

  .preview-chat {
    padding: 16px 12px;
    border-radius: 16px;
  }
}
</style>