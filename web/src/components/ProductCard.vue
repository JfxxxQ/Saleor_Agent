<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  adding: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['add'])

const imageFailed = ref(false)
const selectedVariantId = ref('')

const variants = computed(() =>
  Array.isArray(props.product?.variants) ? props.product.variants : []
)

const selectedVariant = computed(
  () =>
    variants.value.find((variant) => variant.id === selectedVariantId.value) ||
    null
)

const hasMultipleVariants = computed(() => variants.value.length > 1)

const imageUrl = computed(
  () => props.product.image || props.product.thumbnail?.url || ''
)

const showPlaceholder = computed(() => !imageUrl.value || imageFailed.value)

const canAdd = computed(() => {
  if (props.disabled || props.adding) return false
  if (variants.value.length === 0) return true
  return Boolean(selectedVariantId.value)
})

const buttonText = computed(() => {
  if (props.adding) return '加入中…'
  if (hasMultipleVariants.value && !selectedVariantId.value) {
    return '请选择规格'
  }
  return '加入购物车'
})

const productType = computed(
  () => props.product.productType || props.product.type || ''
)

const displayPrice = computed(() => {
  if (selectedVariant.value?.price?.amount != null) {
    return formatMoney(
      selectedVariant.value.price.amount,
      selectedVariant.value.price.currency
    )
  }

  return formatMoney(
    props.product.price?.amount,
    props.product.price?.currency
  )
})

const showPriceFrom = computed(() => {
  if (selectedVariant.value?.price?.amount != null) return false

  const min = Number(props.product.price?.amount)
  const max = Number(props.product.price_max?.amount)

  return Number.isFinite(min) && Number.isFinite(max) && max > min
})

watch(
  () => props.product,
  (product) => {
    const list = Array.isArray(product?.variants) ? product.variants : []
    // 单规格自动选中；多规格让用户自己选
    selectedVariantId.value = list.length === 1 ? list[0].id : ''
  },
  { immediate: true }
)

function formatMoney(amount, currency = 'USD') {
  if (amount == null || amount === '') return ''

  const value = Number(amount)
  if (Number.isNaN(value)) return ''

  try {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency,
      currencyDisplay: 'narrowSymbol',
      maximumFractionDigits: 2,
    }).format(value)
  } catch {
    return `${currency} ${value.toFixed(2)}`
  }
}

function addToCart() {
  if (!canAdd.value) return

  emit('add', {
    ...props.product,
    variant_id:
      selectedVariantId.value || props.product.variant_id || null,
    variant_name: selectedVariant.value?.name || '',
  })
}
</script>

<template>
  <article class="product-card">
    <div class="product-card__media">
      <img
        v-if="!showPlaceholder"
        :src="imageUrl"
        :alt="product.name || '商品图片'"
        loading="lazy"
        decoding="async"
        @error="imageFailed = true"
      />
      <div v-else class="product-card__placeholder" aria-hidden="true">
        <span>{{ (product.name || '商品').slice(0, 1) }}</span>
      </div>

      <span v-if="productType" class="product-card__type">{{ productType }}</span>
    </div>

    <div class="product-card__body">
      <h3 class="product-card__name" :title="product.name">
        {{ product.name || '未命名商品' }}
      </h3>

      <p v-if="product.description" class="product-card__desc">
        {{ product.description }}
      </p>

      <div
        v-if="variants.length"
        class="product-card__variants"
        role="group"
        aria-label="选择商品规格"
      >
        <button
          v-for="variant in variants"
          :key="variant.id"
          type="button"
          class="variant-chip"
          :class="{ 'is-active': selectedVariantId === variant.id }"
          :disabled="disabled || adding"
          :aria-pressed="selectedVariantId === variant.id"
          @click="selectedVariantId = variant.id"
        >
          {{ variant.name || '默认' }}
        </button>
      </div>

      <div class="product-card__footer">
        <strong class="product-card__price">
          {{ displayPrice || '价格待定' }}
          <span v-if="showPriceFrom" class="product-card__from">起</span>
        </strong>

        <button
          type="button"
          class="product-card__add"
          :disabled="!canAdd"
          :aria-label="`把 ${product.name || '商品'} 加入购物车`"
          @click="addToCart"
        >
          {{ buttonText }}
        </button>
      </div>
    </div>
  </article>
</template>

<style scoped>
.product-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--surface);
  box-shadow: 0 4px 16px rgba(31, 29, 26, 0.04);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    border-color 0.15s ease;
}

.product-card:hover {
  border-color: rgba(232, 93, 42, 0.28);
  box-shadow: 0 12px 28px rgba(31, 29, 26, 0.09);
  transform: translateY(-2px);
}

.product-card__media {
  position: relative;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  background:
    radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.7), transparent 45%),
    linear-gradient(135deg, #fdebe4, #f2e3d7);
}

.product-card__media img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.25s ease;
}

.product-card:hover .product-card__media img {
  transform: scale(1.03);
}

.product-card__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: rgba(201, 74, 31, 0.6);
  font-size: 38px;
  font-weight: 700;
}

.product-card__type {
  position: absolute;
  top: 9px;
  left: 9px;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 650;
  backdrop-filter: blur(6px);
}

.product-card__body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 4px;
  padding: 12px 13px 13px;
}

.product-card__name {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--text);
  font-size: 14px;
  font-weight: 650;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.product-card__desc {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
}

.product-card__variants {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-top: 8px;
}

.variant-chip {
  min-width: 30px;
  height: 26px;
  padding: 0 8px;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: #fff;
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    color 0.15s ease,
    opacity 0.15s ease;
}

.variant-chip:hover:not(:disabled) {
  border-color: rgba(232, 93, 42, 0.4);
  color: var(--text);
}

.variant-chip.is-active {
  border-color: var(--primary);
  background: var(--primary-soft);
  color: var(--primary-hover);
  font-weight: 700;
}

.variant-chip:disabled {
  opacity: 0.5;
}

.product-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 8px;
}

.product-card__price {
  color: var(--primary-hover);
  font-size: 15px;
  font-weight: 750;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.product-card__from {
  margin-left: 1px;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-secondary);
}

.product-card__add {
  flex: 0 0 auto;
  height: 31px;
  padding: 0 11px;
  border: 1px solid rgba(232, 93, 42, 0.22);
  border-radius: 9px;
  background: var(--primary-soft);
  color: var(--primary-hover);
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
  transition:
    background 0.15s ease,
    color 0.15s ease,
    opacity 0.15s ease;
}

.product-card__add:hover:not(:disabled) {
  background: var(--primary);
  color: #fff;
}

.product-card__add:disabled {
  opacity: 0.45;
}

@media (max-width: 480px) {
  .product-card__footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .product-card__add {
    width: 100%;
  }
}
</style>