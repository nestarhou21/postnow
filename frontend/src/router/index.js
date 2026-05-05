// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/',          component: () => import('../views/HomeView.vue') },
  { path: '/home',      component: () => import('../views/HomeView.vue') },
  { path: '/login',     component: () => import('../views/LoginView.vue') },
  { path: '/onboarding',component: () => import('../views/OnboardingView.vue') },
  { path: '/result/:id',component: () => import('../views/ResultView.vue') },
  { path: '/history',   component: () => import('../views/HistoryView.vue') },
  { path: '/profile',   component: () => import('../views/ProfileView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
