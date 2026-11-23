<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
} from 'vue'
import { useRouter } from 'vue-router'
import BrandMark from '@/components/BrandMark.vue'
import MessageBubble from '@/components/MessageBubble.vue'
import { streamChat } from '@/api/chat'
import { fetchMe } from '@/api/auth'
import { addToCart } from '@/api/cart'
import {
  fetchHistoryMenu,
  fetchHistoryList,
  saveChatResult,
  deleteHistory,
} from '@/api/history'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const messages = ref([])
const input = ref('')
const isStreaming = ref(false)
const messageListRef = ref(null)
const textareaRef = ref(null)
const showScrollButton = ref(false)
const addingProductKey = ref('')
const toastMessage = ref('')
const historyItems = ref([])
const historyLoading = ref(false)
const historyError = ref('')
const activeHistoryId = ref(null)
const rootHistoryId = ref(null)
const sidebarOpen = ref(false)
const conversationLoading = ref(false)

let controller = null
let autoScroll = true
let stoppedByUser = false
let toastTimer = null

const PRODUCT_CARD_LIMIT = 20

const suggestions = [
  '帮我找一件 T 恤',
  '推荐 100 元以内的礼物',
  '查询我的购物车',
  '有哪些配送方式？',
]

const userLabel = computed(() => auth.user?.email || '已登录用户')

onMounted(async () => {
  if (!auth.token) {
    router.replace('/login')
    return
  }

  try {
    const me = await fetchMe(auth.token)
    if (me) {
      auth.setUser({ ...(auth.user || {}), ...me })
    }
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      auth.logout()
      router.replace({ path: '/login', query: { loggedOut: '1' } })
    }
    // 网络异常不强制退出，发送消息时会再次提示
  }

  await loadHistoryMenu()
  resizeTextarea()
})

function newId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

async function send(text = input.value) {
  const question = String(text || '').trim()
  if (!question || isStreaming.value) return

  input.value = ''
  resizeTextarea()

  messages.value.push({
    id: newId(),
    role: 'user',
    content: question,
    status: 'done',
    createdAt: Date.now(),
  })

  const assistant = reactive({
    id: newId(),
    role: 'assistant',
    content: '',
    products: [],
    status: 'streaming',
    createdAt: Date.now(),
  })
  messages.value.push(assistant)

  isStreaming.value = true
  autoScroll = true
  stoppedByUser = false
  controller = new AbortController()
  await scrollToBottom(true)

  try {
    await streamChat({
      question,
      token: auth.token,
      signal: controller.signal,
      onDelta(delta) {
        assistant.content += delta
        scrollToBottom()
      },
      onProducts(items) {
        if (!Array.isArray(items)) return

        const seen = new Set(
          assistant.products.map((item) => item.id || item.variant_id || item.name)
        )

        for (const item of items) {
          if (assistant.products.length >= PRODUCT_CARD_LIMIT) break

          const key = item.id || item.variant_id || item.name
          if (!key || seen.has(key)) continue
          seen.add(key)
          assistant.products.push(item)
        }

        scrollToBottom()
      },
      onError(error) {
        assistant.status = 'error'
        assistant.content += `${assistant.content ? '\n\n' : ''}[错误] ${error.message}`
      },
      onDone() {
        assistant.status = 'done'
      },
    })

    if (!stoppedByUser && assistant.status !== 'error' && assistant.content.trim()) {
      await persistTurn(question, assistant.content)
    }
  } catch (error) {
    if (stoppedByUser || error.name === 'AbortError') {
      assistant.status = 'done'
      return
    }

    if (error.status === 401 || error.status === 403) {
      auth.logout()
      router.replace({ path: '/login', query: { loggedOut: '1' } })
      return
    }

    assistant.status = 'error'
    const message = error.message || '请求失败，请稍后重试'
    assistant.content += `${assistant.content ? '\n\n' : ''}[错误] ${message}`
  } finally {
    if (assistant.status === 'streaming') {
      assistant.status = 'done'
    }
    isStreaming.value = false
    controller = null
    scrollToBottom()
  }
}

function stop() {
  if (!controller) return
  stoppedByUser = true
  controller.abort()
  controller = null
  isStreaming.value = false
}

async function handleProductAdd(product) {
  if (isStreaming.value || addingProductKey.value) return

  const variantId = product?.variant_id
  if (!variantId) {
    showToast('请先选择商品规格')
    return
  }

  const key = product.id || variantId || product.name
  addingProductKey.value = key

  try {
    // 直接调用购物车接口，不经过 Agent，也不在聊天里插入用户消息
    await addToCart(auth.token, variantId, 1)
    showToast(`已加入购物车：${product.name || '商品'}`)
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      auth.logout()
      router.replace({ path: '/login', query: { loggedOut: '1' } })
      return
    }

    showToast(`加入购物车失败：${error.message || '请稍后重试'}`)
  } finally {
    addingProductKey.value = ''
  }
}

function showToast(message) {
  toastMessage.value = message
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastMessage.value = ''
    toastTimer = null
  }, 2600)
}

function handleAuthFailure() {
  auth.logout()
  router.replace({ path: '/login', query: { loggedOut: '1' } })
}

async function loadHistoryMenu() {
  if (!auth.token) return

  historyLoading.value = true
  historyError.value = ''

  try {
    historyItems.value = await fetchHistoryMenu(auth.token)
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      handleAuthFailure()
      return
    }
    historyError.value = error.message || '历史记录加载失败'
  } finally {
    historyLoading.value = false
  }
}

async function selectHistory(item) {
  if (isStreaming.value) {
    showToast('请先停止当前生成')
    return
  }

  if (activeHistoryId.value === item.history_id && messages.value.length) {
    sidebarOpen.value = false
    return
  }

  activeHistoryId.value = item.history_id
  rootHistoryId.value = item.history_id
  conversationLoading.value = true

  try {
    const list = await fetchHistoryList(auth.token, item.history_id)

    messages.value = list.map((message) => ({
      id: newId(),
      role: message.role,
      content: message.content || '',
      status: 'done',
      createdAt: Date.now(),
    }))

    sidebarOpen.value = false
    await scrollToBottom(true)
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      handleAuthFailure()
      return
    }
    showToast(`加载历史对话失败：${error.message || '请稍后重试'}`)
  } finally {
    conversationLoading.value = false
  }
}

async function removeHistoryItem(item) {
  if (!window.confirm('删除这条历史对话？')) return

  try {
    await deleteHistory(auth.token, item.history_id)

    historyItems.value = historyItems.value.filter(
      (history) => history.history_id !== item.history_id
    )

    if (activeHistoryId.value === item.history_id) {
      newChat(true)
    }

    showToast('历史对话已删除')
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      handleAuthFailure()
      return
    }
    showToast(`删除失败：${error.message || '请稍后重试'}`)
  }
}

async function persistTurn(question, answer) {
  if (!auth.token || !answer.trim()) return

  const parentId =
    rootHistoryId.value == null ? '0' : String(rootHistoryId.value)

  try {
    const newId = await saveChatResult(auth.token, {
      question,
      answer,
      parentId,
    })

    if (rootHistoryId.value == null && newId) {
      rootHistoryId.value = newId
      activeHistoryId.value = newId
      await loadHistoryMenu()
    }
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      handleAuthFailure()
      return
    }
    showToast(`历史记录保存失败：${error.message || '请稍后重试'}`)
  }
}

function newChat(skipConfirm = false) {
  if (
    !skipConfirm &&
    messages.value.length &&
    !window.confirm('清空当前对话？')
  ) {
    return
  }

  stop()
  messages.value = []
  input.value = ''
  showScrollButton.value = false
  autoScroll = true
  rootHistoryId.value = null
  activeHistoryId.value = null
  sidebarOpen.value = false
  resizeTextarea()
}

function logout() {
  stop()
  auth.logout()
  router.replace({ path: '/login', query: { loggedOut: '1' } })
}

function resizeTextarea() {
  nextTick(() => {
    const el = textareaRef.value
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  })
}

function onKeydown(event) {
  if (event.isComposing || event.keyCode === 229) return

  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    send()
  }
}

async function scrollToBottom(force = false) {
  if (force) autoScroll = true
  if (!autoScroll) {
    showScrollButton.value = true
    return
  }

  await nextTick()
  const el = messageListRef.value
  if (el) {
    el.scrollTop = el.scrollHeight
  }
  showScrollButton.value = false
}

function onScroll() {
  const el = messageListRef.value
  if (!el) return

  const nearBottom =
    el.scrollHeight - el.scrollTop - el.clientHeight < 80
  autoScroll = nearBottom
  showScrollButton.value = !nearBottom && messages.value.length > 0
}

onBeforeUnmount(() => {
  controller?.abort()
  clearTimeout(toastTimer)
})
</script>

<template>
  <div class="chat-page">
    <aside class="history-sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-head">
        <div>
          <p class="sidebar-kicker">HISTORY</p>
          <h2>历史对话</h2>
        </div>
        <button
          type="button"
          class="sidebar-close"
          aria-label="关闭历史记录"
          @click="sidebarOpen = false"
        >
          ×
        </button>
      </div>

      <button type="button" class="sidebar-new" @click="newChat()">
        ＋ 新对话
      </button>

      <div class="history-list">
        <p v-if="historyLoading" class="history-hint">加载中…</p>
        <p v-else-if="historyError" class="history-error">{{ historyError }}</p>
        <p v-else-if="!historyItems.length" class="history-hint">
          还没有历史对话
        </p>

        <div
          v-for="item in historyItems"
          :key="item.history_id"
          class="history-item"
          :class="{ active: activeHistoryId === item.history_id }"
          role="button"
          tabindex="0"
          @click="selectHistory(item)"
          @keydown.enter="selectHistory(item)"
        >
          <div class="history-item-text">
            <span class="history-question">
              {{ item.question || '未命名对话' }}
            </span>
            <span class="history-time">{{ item.createTime || '' }}</span>
          </div>
          <button
            type="button"
            class="history-delete"
            aria-label="删除历史对话"
            @click.stop="removeHistoryItem(item)"
          >
            ×
          </button>
        </div>
      </div>

      <div class="sidebar-footer">
        <span class="sidebar-user">{{ userLabel }}</span>
        <button type="button" class="sidebar-logout" @click="logout">
          退出
        </button>
      </div>
    </aside>

    <div
      v-if="sidebarOpen"
      class="sidebar-overlay"
      @click="sidebarOpen = false"
    ></div>

    <div class="chat-main">
    <header class="chat-header">
      <button
        type="button"
        class="sidebar-toggle"
        aria-label="打开历史记录"
        @click="sidebarOpen = true"
      >
        ☰
      </button>
      <div class="chat-brand">
        <BrandMark :size="38" />
        <div class="chat-brand-text">
          <div class="chat-title-line">
            <h1>Saleor 智能购物助手</h1>
            <span class="beta-badge">体验版</span>
          </div>
          <p>{{ userLabel }}</p>
        </div>
      </div>

      <div class="chat-actions">
        <button type="button" class="ghost-btn" @click="newChat">新对话</button>
        <button type="button" class="ghost-btn" @click="logout">退出</button>
      </div>
    </header>

    <div class="experience-notice" role="note">
      <span class="notice-dot" aria-hidden="true"></span>
      对话会自动保存到历史记录，可从左侧继续之前的会话。
    </div>

    <main ref="messageListRef" class="message-list" @scroll="onScroll">
      <div v-if="conversationLoading" class="conversation-loading">
        正在加载历史对话…
      </div>

      <section v-else-if="messages.length === 0" class="welcome-panel">
        <BrandMark :size="56" />
        <h2>你好，我是你的智能购物助手</h2>
        <p>可以帮你找商品、加入购物车、了解配送方式。</p>

        <div class="suggestion-grid">
          <button
            v-for="item in suggestions"
            :key="item"
            type="button"
            class="suggestion-chip"
            @click="send(item)"
          >
            {{ item }}
          </button>
        </div>
      </section>

      <div v-else class="messages-inner" aria-live="polite">
        <MessageBubble
          v-for="message in messages"
          :key="message.id"
          :message="message"
          :product-disabled="isStreaming || Boolean(addingProductKey)"
          :adding-key="addingProductKey"
          @product-add="handleProductAdd"
        />
      </div>
    </main>

    <button
      v-if="showScrollButton"
      type="button"
      class="scroll-latest"
      @click="scrollToBottom(true)"
    >
      回到最新 ↓
    </button>

    <p v-if="toastMessage" class="chat-toast" role="status">
      {{ toastMessage }}
    </p>

    <footer class="chat-composer">
      <div class="composer-shell">
        <textarea
          ref="textareaRef"
          v-model="input"
          rows="1"
          maxlength="2000"
          placeholder="描述你想买的商品，例如：帮我找一件宽松的黑色 T 恤"
          @input="resizeTextarea"
          @keydown="onKeydown"
        ></textarea>

        <button
          v-if="!isStreaming"
          type="button"
          class="send-btn"
          :disabled="!input.trim()"
          @click="send()"
        >
          发送
        </button>
        <button
          v-else
          type="button"
          class="stop-btn"
          @click="stop"
        >
          停止
        </button>
      </div>

      <p class="composer-hint">AI 可能会出错，请核对商品和订单信息。</p>
    </footer>
    </div>
  </div>
</template>