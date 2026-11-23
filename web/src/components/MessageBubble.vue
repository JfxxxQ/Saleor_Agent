<script setup>
import { computed, ref } from 'vue'
import BrandMark from './BrandMark.vue'
import ProductCard from './ProductCard.vue'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
  productDisabled: {
    type: Boolean,
    default: false,
  },
  addingKey: {
    type: String,
    default: '',
  },
})

defineEmits(['product-add'])

const copied = ref(false)

const isUser = computed(() => props.message.role === 'user')
const isError = computed(() => props.message.status === 'error')
const isStreaming = computed(() => props.message.status === 'streaming')
const isEmptyStreaming = computed(
  () => !props.message.content && isStreaming.value
)

const hasProducts = computed(
  () => Array.isArray(props.message.products) && props.message.products.length > 0
)

const showBubble = computed(
  () => isUser.value || Boolean(props.message.content) || isStreaming.value
)

const renderedContent = computed(() =>
  isUser.value ? '' : renderMarkdown(props.message.content)
)

async function copy() {
  const text = props.message.content || ''
  if (!text) return

  try {
    await navigator.clipboard.writeText(text)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }

  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 1500)
}
</script>

<template>
  <div class="message-row" :class="[isUser ? 'user' : 'assistant']">
    <BrandMark v-if="!isUser" :size="30" class="message-avatar" />

    <div class="message-stack" :class="{ 'has-products': hasProducts }">
      <div
        v-if="showBubble"
        class="message-bubble"
        :class="[
          isUser ? 'user' : 'assistant',
          { error: isError, streaming: isStreaming },
        ]"
      >
        <span v-if="isEmptyStreaming" class="typing-dots" aria-label="正在思考">
          <i></i><i></i><i></i>
        </span>

        <span v-else-if="isUser" class="message-text">
          {{ message.content }}
        </span>

        <div
          v-else
          class="markdown-body"
          v-html="renderedContent"
        ></div>

        <span
          v-if="isStreaming && message.content"
          class="stream-caret"
          aria-hidden="true"
        ></span>
      </div>

      <button
        v-if="!isUser && message.content && !isStreaming"
        type="button"
        class="copy-btn"
        @click="copy"
      >
        {{ copied ? '已复制' : '复制' }}
      </button>

      <div v-if="hasProducts" class="product-grid">
        <ProductCard
          v-for="(product, index) in message.products"
          :key="product.id || product.variant_id || product.name || index"
          :product="product"
          :disabled="productDisabled"
          :adding="
            addingKey === (product.id || product.variant_id || product.name)
          "
          @add="$emit('product-add', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-stack.has-products {
  width: 100%;
  max-width: 100%;
}

.message-stack.has-products .message-bubble {
  max-width: 680px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 12px;
  width: 100%;
  margin-top: 12px;
}

@media (max-width: 768px) {
  .message-stack.has-products {
    width: 100%;
    max-width: 100%;
  }

  .product-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
}

@media (max-width: 420px) {
  .product-grid {
    grid-template-columns: 1fr;
  }
}
</style>