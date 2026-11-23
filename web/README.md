# Saleor 智能购物助手前端

Vue 3 + Vite + JavaScript + Pinia + Vue Router + `@microsoft/fetch-event-source`。

## 启动

```bash
npm install
npm run dev
```

打开 `http://localhost:5173`。

> 请使用 `localhost` 访问，不要用 `127.0.0.1`。后端 CORS 目前只允许
> `http://localhost:5173`。

后端默认地址：

```env
VITE_API_BASE_URL=http://localhost:8001
```

如果后端端口变化，修改 `.env` 后重启 Vite。

## 页面

| 路由 | 页面 |
|---|---|
| `/login` | 邮箱密码登录 |
| `/register` | 邮箱验证码注册 |
| `/chat` | 智能助手聊天页 |

## 已实现

- 登录失败、注册验证码 409/429、网络异常提示
- 注册成功后自动登录
- 登录态 Pinia + localStorage
- 路由守卫：未登录不能进入 `/chat`
- SSE 流式聊天（POST + Authorization Header）
- 停止生成、复制回复、新对话、退出登录
- Markdown 渲染：`marked` + `DOMPurify`，支持表格、代码块、列表、引用
- 商品卡片：图片、名称、价格、规格选择、加入购物车
- 卡片加购直接调用 `POST /cart/lines`，不经过 Agent，也不在聊天里插入用户消息
- 体验版提示：不保存历史，刷新清空
- 桌面/移动端响应式

## 商品卡片 SSE 协议

后端 `get_products` 在传入 `search` 时会发送：

```json
{
  "type": "products",
  "items": [
    {
      "id": "UHJvZHVjdDoxNTI=",
      "name": "Monospace Tee",
      "image": "http://localhost:8000/media/thumbnails/...",
      "price": { "amount": 12, "currency": "USD" },
      "price_max": { "amount": 20, "currency": "USD" },
      "productType": "Top",
      "variants": [
        {
          "id": "UHJvZHVjdFZhcmlhbnQ6MzQ5",
          "name": "M",
          "price": { "amount": 20, "currency": "USD" }
        }
      ]
    }
  ]
}
```

规则：

- `search` 为空：只返回文字列表，不展示图片卡片；
- `search` 有值：展示所有匹配商品的图片卡片；
- 单次事件最多 20 张卡片；
- 多规格商品需要用户在卡片上选择尺码，选择后“加入购物车”按钮才可用；
- 点击加购直接调用：
  ```http
  POST /cart/lines
  Authorization: Bearer <JWT>
  Content-Type: application/json

  { "variant_id": "UHJvZHVjdFZhcmlhbnQ6MzQ5", "quantity": 1 }
  ```
- 加购成功只显示页面 Toast，不在聊天里产生用户消息；
- 如果用户后续询问购物车，Agent 再通过 `get_checkout_summary` 查询。

## 开发预览

开发环境访问：

```text
http://localhost:5173/preview
```

可以查看 Markdown 和商品卡片的样式，不会调用后端。该路由只在 `npm run dev` 下注册。

## 说明

当前还没有接入记忆系统，所以：

- 不展示历史会话侧栏；
- 刷新页面后聊天内容清空；
- 每次提问独立处理。

后续接入 checkpointer/长期记忆后，再补历史会话、商品卡片和购物车侧栏。