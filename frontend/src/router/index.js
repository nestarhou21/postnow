// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/',          component: () => import('../views/MarketingView.vue'),  meta: { guest: true } },
  { path: '/login',     component: () => import('../views/LoginView.vue'),      meta: { guest: true } },
  { path: '/onboarding',component: () => import('../views/OnboardingView.vue'), meta: { auth: true } },
  { path: '/home',      component: () => import('../views/HomeView.vue'),       meta: { auth: true } },
  { path: '/result/:id',component: () => import('../views/ResultView.vue'),     meta: { auth: true } },
  { path: '/history',   component: () => import('../views/HistoryView.vue'),    meta: { auth: true } },
  { path: '/profile',   component: () => import('../views/ProfileView.vue'),    meta: { auth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.auth && !auth.isLoggedIn) return '/login'
  if (to.meta.guest && auth.isLoggedIn) return '/home'

  // If logged in but no profile fetched yet, fetch it
  if (auth.isLoggedIn && !auth.user) {
    try { await auth.fetchMe() } catch { auth.logout(); return '/login' }
  }

  // Redirect to onboarding if profile not set (except if already going there)
  if (auth.isLoggedIn && !auth.hasProfile && to.path !== '/onboarding') {
    return '/onboarding'
  }
})

export default router
