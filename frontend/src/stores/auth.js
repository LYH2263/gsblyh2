import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('token') || null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(credentials) {
    const res = await authAPI.login(credentials)
    token.value = res.access_token
    user.value = res.user
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res.user))
    return res
  }

  async function register(data) {
    const res = await authAPI.register(data)
    return res
  }

  async function fetchCurrentUser() {
    try {
      const res = await authAPI.getCurrentUser()
      user.value = res.user
      localStorage.setItem('user', JSON.stringify(res.user))
      return res.user
    } catch (error) {
      logout()
      throw error
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function updateUser(newUser) {
    user.value = { ...user.value, ...newUser }
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    register,
    fetchCurrentUser,
    logout,
    updateUser
  }
})
