<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1 class="logo">微博</h1>
        <p class="login-subtitle">发现更多精彩</p>
      </div>

      <div class="login-form">
        <div class="form-group">
          <input
            v-model="form.username"
            type="text"
            class="form-input"
            placeholder="用户名 / 邮箱"
            @keyup.enter="handleLogin"
          />
        </div>

        <div class="form-group">
          <input
            v-model="form.password"
            type="password"
            class="form-input"
            placeholder="密码"
            @keyup.enter="handleLogin"
          />
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>

        <button class="btn btn-primary btn-block" :loading="loading" @click="handleLogin">
          登录
        </button>

        <div class="demo-accounts">
          <div class="demo-accounts-title">默认测试账号（点击一键填充）</div>
          <div class="demo-accounts-list">
            <button
              v-for="account in defaultAccounts"
              :key="account.username"
              type="button"
              class="demo-account-item"
              @click="fillAccount(account)"
            >
              <span class="demo-account-name">{{ account.username }}</span>
              <span class="demo-account-password">{{ account.password }}</span>
              <span v-if="account.note" class="demo-account-note">{{ account.note }}</span>
            </button>
          </div>
        </div>

        <div class="login-footer">
          <router-link to="/register" class="register-link">还没有账号？立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  username: '',
  password: ''
})
const loading = ref(false)
const error = ref('')

const defaultAccounts = [
  { username: 'web', password: '123456', note: '系统用户' },
  { username: 'user1', password: '123456', note: '测试用户1' },
  { username: 'user2', password: '123456', note: '测试用户2' },
  { username: 'user3', password: '123456', note: '测试用户3' }
]

function fillAccount(account) {
  form.value.username = account.username
  form.value.password = account.password
  error.value = ''
}

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await authStore.login(form.value)
    router.push('/timeline')
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fff5f5 0%, #fff 50%, #fff5f5 100%);
}

.login-container {
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo {
  font-size: 48px;
  color: #e6162d;
  font-weight: bold;
}

.login-subtitle {
  color: #999;
  margin-top: 10px;
}

.login-form {
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.btn-block {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.demo-accounts {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.demo-accounts-title {
  font-size: 13px;
  color: #999;
  margin-bottom: 12px;
  text-align: center;
}

.demo-accounts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.demo-account-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e1e1e1;
  border-radius: 8px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  text-align: left;
}

.demo-account-item:hover {
  border-color: #e6162d;
  background: #fff5f5;
}

.demo-account-name {
  font-weight: 600;
  color: #333;
  min-width: 48px;
}

.demo-account-password {
  color: #666;
}

.demo-account-note {
  margin-left: auto;
  color: #999;
  font-size: 12px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
}

.register-link {
  color: #e6162d;
  font-size: 14px;
}

.register-link:hover {
  text-decoration: underline;
}
</style>
