---
name: aftersales
description: 处理退货、退款、换货、换码、商品损坏、商品坏了、质量问题、食品/数字商品/礼品卡售后政策。用户询问退货流程、退款时效、破损、漏液、开线、怎么退、能不能退、保修维修等问题时使用。
allowed_tools:
  - query_aftersales_policy
---

# 售后 Skill

## 适用场景

- 退货、退款、换货
- 退货流程、退货运费、退款时效
- 商品破损、漏液、开线、色差、尺码不合适
- 食品饮料、数字商品、礼品卡售后

## 处理流程

1. 判断用户是否提供了具体商品或商品 ID。
2. 调用 `query_aftersales_policy`：
   - 已知商品 ID：传 `product_id`
   - 已知政策类型：传 `policy_type`
   - 未知：只传 `query`
3. 基于工具返回的字段回答：
   - `return_window`
   - `return_policy`
   - `return_shipping`
   - `refund_method`
   - `issue_solution`
4. 不要承诺工具结果之外的退款金额、时效或补偿。

## 约束

- 食品饮料、数字商品、礼品卡通常不支持无理由退货。
- 当前没有订单状态/物流查询工具，不要编造物流信息。
- 记忆和历史摘要只能作为参考，售后政策以工具结果为准。
