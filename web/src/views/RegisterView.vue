<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import BrandPanel from '@/components/BrandPanel.vue'
import BrandMark from '@/components/BrandMark.vue'
import { login, register, sendRegisterCode } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const code = ref('')
const nickname = ref('')
const password = ref('')
const confirmPassword = ref('')
const agreed = ref(false)

const showPassword = ref(false)
const showConfirmPassword = ref(false)

const countdown = ref(0)
const sendingCode = ref(false)
const submitting = ref(false)
const error = ref('')
const notice = ref('')

let timer = null

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function startCountdown() {
  clearInterval(timer)
  countdown.value = 60
  timer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

function onCodeInput(event) {
  code.value = event.target.value.replace(/\D/g, '').slice(0, 6)
}

async function sendCode() {
  error.value = ''
  notice.value = ''

  if (!emailPattern.test(email.value.trim())) {
    error.value = '请先输入有效的邮箱地址'
    return
  }

  sendingCode.value = true
  try {
    await sendRegisterCode(email.value.trim())
    notice.value = '验证码已发送，请查收邮箱（60 秒内有效）'
    startCountdown()
  } catch (err) {
    if (err.status === 409) {
      error.value = '该邮箱已经注册，请直接登录'
    } else if (err.status === 429) {
      error.value = '验证码发送过于频繁，请稍后再试'
    } else {
      error.value = err.message || '验证码发送失败，请稍后重试'
    }
  } finally {
    sendingCode.value = false
  }
}

async function submit() {
  error.value = ''
  notice.value = ''

  if (!emailPattern.test(email.value.trim())) {
    error.value = '请输入有效的邮箱地址'
    return
  }
  if (code.value.length !== 6) {
    error.value = '请输入 6 位邮箱验证码'
    return
  }
  if (nickname.value.trim().length < 2 || nickname.value.trim().length > 20) {
    error.value = '昵称长度应为 2–20 个字符'
    return
  }
  if (password.value.length < 8) {
    error.value = '密码至少需要 8 位'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  if (!agreed.value) {
    error.value = '请先阅读并同意服务条款'
    return
  }

  submitting.value = true

  try {
    await register({
      email: email.value.trim(),
      password: password.value,
      nickname: nickname.value.trim(),
      code: code.value,
    })
  } catch (err) {
    error.value = err.message || '注册失败，请稍后重试'
    submitting.value = false
    return
  }

  try {
    // 注册接口不返回 token，前端自动登录
    const result = await login(email.value.trim(), password.value)
    auth.setAuth(result.token, result.user)
    notice.value = '注册成功，正在进入聊天…'
    router.replace('/chat')
  } catch {
    router.replace({
      path: '/login',
      query: { email: email.value.trim(), registered: '1' },
    })
  } finally {
    submitting.value = false
  }
}

onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="auth-page">
    <BrandPanel />

    <main class="auth-main">
      <div class="auth-mobile-brand">
        <BrandMark :size="36" />
        <span>Saleor 智能购物助手</span>
      </div>

      <section class="auth-card auth-card-wide" aria-labelledby="register-title">
        <p class="eyebrow">CREATE ACCOUNT</p>
        <h1 id="register-title">创建账号</h1>
        <p class="auth-subtitle">
          注册后即可使用智能助手找商品、加购物车和下单。
        </p>

        <p v-if="notice" class="alert success" role="status">{{ notice }}</p>
        <p v-if="error" class="alert error" role="alert">{{ error }}</p>

        <form class="auth-form" novalidate @submit.prevent="submit">
          <label class="auth-field">
            <span class="field-label">邮箱</span>
            <span class="code-row">
              <input
                v-model="email"
                type="email"
                name="email"
                autocomplete="email"
                placeholder="you@example.com"
              />
              <button
                type="button"
                class="code-btn"
                :disabled="sendingCode || countdown > 0"
                @click="sendCode"
              >
                {{
                  countdown > 0
                    ? `${countdown}s 后重发`
                    : sendingCode
                      ? '发送中…'
                      : '发送验证码'
                }}
              </button>
            </span>
          </label>

          <label class="auth-field">
            <span class="field-label">验证码</span>
            <input
              :value="code"
              type="text"
              name="code"
              inputmode="numeric"
              autocomplete="one-time-code"
              maxlength="6"
              placeholder="6 位数字验证码"
              @input="onCodeInput"
            />
          </label>

          <label class="auth-field">
            <span class="field-label">昵称</span>
            <input
              v-model="nickname"
              type="text"
              name="nickname"
              autocomplete="nickname"
              maxlength="20"
              placeholder="给自己起个昵称"
            />
          </label>

          <label class="auth-field">
            <span class="field-label">密码</span>
            <span class="password-box">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                name="new-password"
                autocomplete="new-password"
                placeholder="至少 8 位，建议包含字母和数字"
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

          <label class="auth-field">
            <span class="field-label">确认密码</span>
            <span class="password-box">
              <input
                v-model="confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                name="confirm-password"
                autocomplete="new-password"
                placeholder="再次输入密码"
              />
              <button
                type="button"
                class="reveal-btn"
                :aria-label="showConfirmPassword ? '隐藏密码' : '显示密码'"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                {{ showConfirmPassword ? '隐藏' : '显示' }}
              </button>
            </span>
          </label>

          <label class="agreement">
            <input v-model="agreed" type="checkbox" />
            <span>我已阅读并同意服务条款和隐私政策</span>
          </label>

          <button class="primary-btn" type="submit" :disabled="submitting">
            <span v-if="submitting" class="spinner" aria-hidden="true"></span>
            {{ submitting ? '注册中…' : '注册' }}
          </button>
        </form>

        <p class="auth-switch">
          已有账号？
          <RouterLink to="/login">去登录</RouterLink>
        </p>
      </section>

      <p class="auth-copyright">Saleor 智能购物助手 · 体验版</p>
    </main>
  </div>
</template>