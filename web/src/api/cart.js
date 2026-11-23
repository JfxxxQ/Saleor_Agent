import { apiFetch } from './http'

/**
 * 商品卡片直接加购，不经过 Agent。
 */
export async function addToCart(token, variantId, quantity = 1) {
  return apiFetch('/cart/lines', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      variant_id: variantId,
      quantity,
    }),
  })
}