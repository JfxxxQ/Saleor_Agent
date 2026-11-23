<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import BrandPanel from '@/components/BrandPanel.vue'
import BrandMark from '@/components/BrandMark.vue'
import { login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const notice = ref('')

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

onMounted(() => {
  if (typeof route.query.email === 'string') {
    email.value = route.query.email
  }
  if (route.query.registered === '1') {
    notice.value = '注册成功，请使用新账号登录'
  }
  if (route.query.loggedOut === '1') {
    notice.value = '你已退出登录'
  }
})

async function submit() {
  error.value = ''
  notice.value = ''

  if (!emailPattern.test(email.value.trim())) {
    error.value = '请输入有效的邮箱地址'
    return
  }
  if (!password.value) {
    error.value = '请输入密码'
    return
  }

  loading.value = true
  try {
    const result = await login(email.value.trim(), password.value)
    auth.setAuth(result.token, result.user)

    const redirect =
      typeof route.query.redirect === 'string' &&
      route.query.redirect.startsWith('/')
        ? route.query.redirect
        : '/chat'

    router.replace(redirect)
  } catch (err) {
    error.value = err.message || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <BrandPanel />

    <main class="auth-main">
      <div class="auth-mobile-brand">
        <BrandMark :size="36" />
        <span>Saleor 智能购物助手</span>
      </div>

      <section class="auth-card" aria-labelledby="login-title">
        <p class="eyebrow">WELCOME BACK</p>
        <h1 id="login-title">欢迎回来</h1>
        <p class="auth-subtitle">
          登录后即可让智能助手帮你找商品、加购物车和下单。
        </p>

        <p v-if="notice" class="alert success" role="status">{{ notice }}</p>
        <p v-if="error" class="alert error" role="alert">{{ error }}</p>

        <form class="auth-form" novalidate @submit.prevent="submit">
          <label class="auth-field">
            <span class="field-label">邮箱</span>
            <input
              v-model="email"
              type="email"
              name="email"
              autocomplete="email"
              placeholder="you@example.com"
              autofocus
            />
          </label>

          <label class="auth-field">
            <span class="field-label">密码</span>
            <span class="password-box">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                name="password"
                autocomplete="current-password"
                placeholder="请输入密码"
              />
              <button
                type="button"
                class="reveal-btn"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? '隐藏' : '显示' }}
              </button>
            </span>
          </label>

          <button class="primary-btn" type="submit" :disabled="loading">
            <span v-if="loading" class="spinner" aria-hidden="true"></span>
            {{ loading ? '登录中…' : '登录' }}
          </button>
        </form>

        <p class="auth-switch">
          还没有账号？
          <RouterLink to="/register">立即注册</RouterLink>
        </p>
      </section>

      <p class="auth-copyright">Saleor 智能购物助手 · 体验版</p>
    </main>
  </div>
</template>