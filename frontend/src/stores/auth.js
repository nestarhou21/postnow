// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('postnow_token') || null)
  const user = ref(null)
  const hasProfile = ref(false)
  const profile = ref(null)
  
  const isLoggedIn = computed(() => !!token.value)

  async function login(email, password) {
    token.value = "mock_token_" + email
    localStorage.setItem('postnow_token', token.value)
    await fetchMe()
  }

  async function register(email, password) {
    token.value = "mock_token_" + email
    localStorage.setItem('postnow_token', token.value)
    await fetchMe()
  }

  async function fetchMe() {
    if (!token.value) throw new Error("No token")
    user.value = { email: "test@example.com", id: 1 }
    hasProfile.value = true
    profile.value = { brand_name: "Mock Brand" }
  }

  function logout() {
    token.value = null
    user.value = null
    hasProfile.value = false
    localStorage.removeItem('postnow_token')
  }

  return { token, user, hasProfile, isLoggedIn, login, register, fetchMe, logout }
})
