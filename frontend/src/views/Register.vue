<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1 class="logo">微博</h1>
        <p class="login-subtitle">加入我们，发现更多精彩</p>
      </div>

      <div class="login-form">
        <div class="form-group">
          <input
            v-model="form.username"
            type="text"
            class="form-input"
            placeholder="用户名（3-20位字母、数字或下划线）"
          />
        </div>

        <div class="form-group">
          <input
            v-model="form.email"
            type="email"
            class="form-input"
            placeholder="邮箱"
          />
        </div>

        <div class="form-group">
          <input
            v-model="form.password"
            type="password"
            class="form-input"
            placeholder="密码（至少6位）"
          />
        </div>

        <div class="form-group">
          <input
            v-model="form.confirmPassword"
            type="password"
            class="form-input"
            placeholder="确认密码"
            @keyup.enter="handleRegister"
          />
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>
        <div v-if="success" class="success-message">{{ success }}</div>

        <button class="btn btn-primary btn-block" :loading="loading" @click="handleRegister">
          注册
        </button>

        <div class="login-footer">
          <router-link to="/login" class="register-link">已有账号？立即登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../api'

const router = useRouter()

const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})
const loading = ref(false)
const error = ref('')
const success = ref('')

async function handleRegister() {
  error.value = ''
  success.value = ''

  // 验证
  if (!form.value.username || !form.value.email || !form.value.password) {
    error.value = '请填写所有必填项'
    return
  }

  if (form.value.password !== form.value.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }

  if (form.value.password.length < 6) {
    error.value = '密码长度至少6位'
    return
  }

  loading.value = true

  try {
    await authAPI.register(form.value)
    success.value = '注册成功，请登录'
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } catch (e) {
    error.value = e.message || '注册失败'
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

.success-message {
  color: #4caf50;
  font-size: 14px;
  margin-bottom: 15px;
  text-align: center;
}
</style>
