---
name: support
description: 商品咨询与售前支持。用户询问商品、商品详情、商品对比、商品属性、商品关联或区别时使用。不处理售后、订单和购物车。
allowed_tools:
  - get_products
  - compare_products
  - generate_cypher
---

# 商品咨询 Skill

## 适用场景
- 商品搜索、商品详情
- 两个商品的区别/对比
- 商品属性、材质、颜色、价格
- 商品之间的关联

## 处理流程
1. 用户说中文品类时，先翻译成英文关键词：
   果汁 → juice；T恤 → tee / shirt；鞋 → shoe；黑色 → black。
2. 商品搜索调用 `get_products(search=...)`。
3. 商品对比调用 `compare_products(product_id_a, product_id_b)`。
4. 需要图关系时使用 `generate_cypher`。

## 约束
- 商品是否存在、价格、库存、规格以工具结果为准。
- 记忆和历史摘要不能覆盖工具结果。
- 不处理退货、退款、订单、购物车。
- 不编造商品 ID、variant_id、价格或属性。

