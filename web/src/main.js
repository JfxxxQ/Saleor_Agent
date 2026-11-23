import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './style.css'
import './styles/auth.css'
import './styles/chat.css'
import './styles/markdown.css'

const app = createApp(App)

// Pinia 必须先安装，路由守卫里会使用 useAuthStore()
app.use(createPinia())
app.use(router)
app.mount('#app')