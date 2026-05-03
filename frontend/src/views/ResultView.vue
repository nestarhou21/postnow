<template>
  <div class="min-h-screen bg-surface flex flex-col font-body text-on-surface">
    <!-- Top Header -->
    <header class="px-8 py-5 border-b border-surface-container-high bg-surface-lowest flex justify-between items-center sticky top-0 z-50 shadow-sm">
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-2 cursor-pointer" @click="router.push('/home')">
          <span class="material-symbols-outlined text-primary text-[28px]" style="font-variation-settings: 'FILL' 1;">coffee</span>
          <span class="text-xl font-extrabold text-primary font-headline tracking-tight hidden sm:block">POSTNOW</span>
        </div>
        
        <button class="flex items-center gap-1.5 text-on-surface-variant hover:text-primary transition-colors font-bold text-sm" @click="router.push('/home')">
          <span class="material-symbols-outlined text-[18px]">arrow_back</span>
          Back to Generator
        </button>
      </div>
      
      <div v-if="auth.profile" class="flex items-center gap-4">
        <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-surface-container rounded-full border border-surface-container-highest">
          <div class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
          <span class="text-xs font-bold text-on-surface-variant tracking-wide">{{ auth.profile.shop_name }}</span>
        </div>
      </div>
    </header>

    <main class="flex-1 max-w-[1200px] w-full mx-auto p-4 sm:p-8">
      
      <div v-if="loading" class="flex flex-col items-center justify-center h-[60vh] gap-6">
        <div class="relative">
          <div class="w-24 h-24 rounded-full border-[4px] border-surface-container-high border-t-primary animate-spin"></div>
          <span class="material-symbols-outlined text-primary text-[32px] absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">coffee</span>
        </div>
        <h2 class="font-headline text-2xl font-bold text-on-surface animate-pulse">Brewing your post...</h2>
        <p class="text-on-surface-variant font-medium text-sm max-w-sm text-center">We're designing the visual and writing captions perfectly tailored to your shop's aesthetic.</p>
      </div>

      <div v-else-if="error" class="flex flex-col items-center justify-center h-[50vh] gap-4">
        <span class="material-symbols-outlined text-error text-[48px]">error</span>
        <h2 class="font-headline text-2xl font-bold text-on-surface">Couldn't load result</h2>
        <p class="text-on-surface-variant">{{ error }}</p>
        <button @click="router.push('/home')" class="mt-4 px-6 py-3 rounded-full bg-surface-container text-on-surface font-bold hover:bg-surface-variant transition-colors">
          Return Home
        </button>
      </div>

      <div v-else-if="post" class="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 animate-[fadeUp_0.5s_ease_both]">
        
        <!-- Left Column: The Image -->
        <div class="flex flex-col gap-6">
          <div class="bg-surface-container-lowest p-4 sm:p-6 rounded-[32px] shadow-[0_24px_50px_rgba(61,35,20,0.08)] border border-surface-container-high">
            <div class="rounded-[20px] overflow-hidden bg-surface-container aspect-[4/5] relative">
              <img :src="post.image_url" alt="Generated Poster" class="w-full h-full object-cover" />
              <!-- Watermark/Logo overlay option -->
              <div class="absolute bottom-4 right-4 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-lg shadow-sm border border-black/5 flex items-center gap-1.5">
                 <span class="material-symbols-outlined text-primary text-[14px]" style="font-variation-settings: 'FILL' 1;">coffee</span>
                 <span class="font-headline font-black tracking-tight text-[10px] text-on-surface uppercase">{{ auth.profile?.shop_name }}</span>
              </div>
            </div>
          </div>
          
          <button @click="downloadImage" class="w-full bg-primary text-white font-bold text-lg py-4 rounded-full shadow-[0_8px_16px_rgba(119,88,56,0.15)] hover:bg-[#8B6B4A] hover:shadow-[0_12px_24px_rgba(119,88,56,0.25)] hover:-translate-y-1 active:translate-y-0 transition-all flex items-center justify-center gap-2">
            <span class="material-symbols-outlined text-[22px]">download</span>
            Download High-Res Poster
          </button>
        </div>

        <!-- Right Column: The Captions & Actions -->
        <div class="flex flex-col gap-8">
          
          <div>
            <h1 class="font-headline text-4xl font-extrabold text-on-surface tracking-tight mb-2">Ready to post.</h1>
            <p class="text-on-surface-variant text-base font-medium">Here are your generated captions based on the promotion.</p>
          </div>

          <!-- English Caption Bento -->
          <div class="bg-surface-container-low rounded-3xl p-6 border border-surface-container-high relative group transition-shadow hover:shadow-md">
            <div class="flex justify-between items-start mb-4">
              <div class="flex items-center gap-2">
                <span class="text-xl">🇺🇸</span>
                <h3 class="font-bold text-on-surface uppercase tracking-widest text-xs">English Caption</h3>
              </div>
              <button @click="copy(post.caption_en)" class="text-primary hover:text-on-primary-container p-2 rounded-full hover:bg-primary-container/20 transition-colors" title="Copy">
                <span class="material-symbols-outlined text-[20px]">content_copy</span>
              </button>
            </div>
            <p class="text-on-surface font-medium whitespace-pre-wrap leading-relaxed text-sm">{{ post.caption_en }}</p>
          </div>

          <!-- Khmer Caption Bento -->
          <div class="bg-surface-container-low rounded-3xl p-6 border border-surface-container-high relative group transition-shadow hover:shadow-md">
            <div class="flex justify-between items-start mb-4">
              <div class="flex items-center gap-2">
                <span class="text-xl">🇰🇭</span>
                <h3 class="font-bold text-on-surface uppercase tracking-widest text-xs">Khmer Caption</h3>
              </div>
              <button @click="copy(post.caption_km)" class="text-primary hover:text-on-primary-container p-2 rounded-full hover:bg-primary-container/20 transition-colors" title="Copy">
                <span class="material-symbols-outlined text-[20px]">content_copy</span>
              </button>
            </div>
            <p class="text-on-surface font-medium whitespace-pre-wrap leading-relaxed text-sm font-['Battambang']">{{ post.caption_km }}</p>
          </div>

          <!-- Edit/Renovate option -->
          <div class="bg-primary/5 rounded-3xl p-6 border border-primary-container/30 mt-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h4 class="font-bold text-on-surface text-sm mb-1 line-clamp-1">Not quite perfect?</h4>
              <p class="text-on-surface-variant text-xs">Regenerate with a different twist.</p>
            </div>
            <button @click="renovate" class="w-full sm:w-auto px-6 py-3 rounded-full bg-surface-container-lowest text-primary font-bold border border-primary/20 shadow-sm hover:shadow-md hover:bg-white transition-all whitespace-nowrap flex items-center justify-center gap-2">
              <span class="material-symbols-outlined text-[18px]">refresh</span>
              Renovate
            </button>
          </div>

        </div>

      </div>
    </main>

    <!-- Toast Notification -->
    <div v-if="toastMsg" class="fixed bottom-8 left-1/2 -translate-x-1/2 bg-on-surface text-surface text-sm font-bold px-6 py-3 rounded-full shadow-xl animate-[fadeUp_0.3s_ease_both] z-50 flex items-center gap-2">
      <span class="material-symbols-outlined text-green-400 text-[18px]">check_circle</span>
      {{ toastMsg }}
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()

const post      = ref(null)
const loading   = ref(true)
const error     = ref('')
const toastMsg  = ref('')

onMounted(() => {
  try {
    const stored = sessionStorage.getItem('postnow_result')
    if (stored) {
      const data = JSON.parse(stored)
      if (String(data.id) === String(route.params.id)) {
        post.value    = data
        loading.value = false
        return
      }
    }
    error.value = "Result not found. Please generate a new post."
  } catch {
    error.value = "Could not load result."
  } finally {
    loading.value = false
  }
})

function logout() {
  auth.logout()
  router.push('/login')
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    toastMsg.value = 'Copied to clipboard!'
    setTimeout(() => { toastMsg.value = '' }, 3000)
  } catch (e) {
    alert('Failed to copy to clipboard.')
  }
}

function downloadImage() {
  if (!post.value) return
  // simple direct download via link
  const link = document.createElement('a')
  link.href = post.value.image_url
  link.download = `postnow-${post.value.id}.png`
  link.target = "_blank"
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function renovate() {
  // Regenerate with same parameters could be implemented,
  // For now, redirect to home to try again
  router.push('/home')
}
</script>

<style>
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
