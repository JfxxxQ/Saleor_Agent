---
name: shopping
description: 导购与购物车。用户要查询商品、加入购物车、修改或删除商品、查看购物车、查询配送方式、选择配送方式或下单时使用。
allowed_tools:
  - get_products
  - create_cart
  - add_checkout_lines
  - delete_checkout_line
  - get_checkout_summary
  - update_checkout_line
  - get_shipping_methods
  - select_shipping_method
  - place_order
---

# 导购与购物车 Skill

## 处理流程

1. 先调用 `get_products(search=...)` 找商品。
2. 从返回的 `variants` 中获取 `variant_id`，禁止编造。
3. 调用 `add_checkout_lines(variant_id, quantity)` 加购。
4. 修改或删除购物车前，先调用 `get_checkout_summary` 获取 `line_id`。
5. 查询配送方式调用 `get_shipping_methods`；
   返回空列表时提示用户去平台填写收货地址。
6. 选择配送方式调用 `select_shipping_method`。
7. 下单前先 `get_checkout_summary`，向用户复述商品、数量、总价、地址和配送方式。
8. 用户明确确认后，调用 `place_order(confirm=True)`。

## 约束

- 所有购物车工具自动使用当前登录用户的购物车。
- 禁止传 `checkout_id`，也不要询问用户 checkout_id。
- 价格和库存以工具结果为准。
- 不询问或保存银行卡号等支付信息。
