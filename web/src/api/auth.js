import { apiFetch } from './http'

export async function login(email, password) {
  const body = await apiFetch('/users/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })

  if (body.code !== 200 || !body.data) {
    throw new Error(body.msg || '登录失败')
  }

  return {
    token: body.data,
    user: body.user,
  }
}

export async function sendRegisterCode(email) {
  return apiFetch('/users/registerCode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
}

export async function register({ email, password, nickname, code }) {
  const body = await apiFetch('/users/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, nickname, code }),
  })

  if (body.code !== 200) {
    throw new Error(body.msg || '注册失败')
  }

  return body
}

export async function fetchMe(token) {
  const body = await apiFetch('/users/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  return body.data
}