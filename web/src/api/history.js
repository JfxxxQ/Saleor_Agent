import { apiFetch } from './http'

function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
  }
}

export async function fetchHistoryMenu(token) {
  const body = await apiFetch('/history/queryHistoryMenu', {
    headers: authHeaders(token),
  })
  return body.data || []
}

export async function fetchHistoryList(token, historyId) {
  const body = await apiFetch(`/history/queryHistoryList/${historyId}`, {
    headers: authHeaders(token),
  })
  return body.data || []
}

export async function saveChatResult(token, { question, answer, parentId = '0' }) {
  const body = await apiFetch('/history/saveChatResult', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(token),
    },
    body: JSON.stringify({
      question,
      answer,
      parent_id: parentId,
    }),
  })
  return body.data
}

export async function deleteHistory(token, historyId) {
  const body = await apiFetch(`/history/deleteHistory/${historyId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })
  return body.data
}