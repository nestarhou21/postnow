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
      
      <div class="flex justify-between items-end mb-8">
        <div>
          <h1 class="font-headline text-3xl font-extrabold text-on-surface tracking-tight mb-2">Your History.</h1>
          <p class="text-on-surface-variant text-sm font-medium">Past generation results for your shop.</p>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center py-20">
        <span class="material-symbols-outlined animate-spin text-primary text-[40px]">progress_activity</span>
      </div>

      <div v-else-if="error" class="bg-error-container/20 border border-error/20 p-6 rounded-2xl flex flex-col items-center gap-3">
        <span class="material-symbols-outlined text-error text-[32px]">error</span>
        <p class="text-error font-bold">{{ error }}</p>
      </div>

      <div v-else-if="posts.length === 0" class="flex flex-col items-center justify-center py-24 bg-surface-container-low rounded-3xl border border-surface-container border-dashed">
        <span class="material-symbols-outlined text-outline-variant text-[64px] mb-4">image_filter_none</span>
        <h3 class="font-bold text-xl text-on-surface mb-2">No posts yet</h3>
        <p class="text-on-surface-variant mb-6 font-medium">Generate your first promotion to see it here.</p>
        <button @click="router.push('/home')" class="bg-primary text-white font-bold px-6 py-3 rounded-full shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all">
          Go to Generator
        </button>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div 
          v-for="post in posts" 
          :key="post.id"
          class="bg-surface-container-lowest rounded-2xl overflow-hidden shadow-sm border border-surface-container-high transition-all hover:shadow-lg hover:-translate-y-1 cursor-pointer group flex flex-col"
          @click="router.push(`/result/${post.id}`)"
        >
          <div class="aspect-[4/5] bg-surface-container relative w-full overflow-hidden">
            <img :src="post.image_url" alt="Thumb" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
            <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
              <span class="bg-white/90 text-on-surface font-bold text-sm px-4 py-2 rounded-full backdrop-blur-sm">View Details</span>
            </div>
          </div>
          <div class="p-4 flex-1 flex flex-col justify-between">
             <p class="text-sm font-medium text-on-surface line-clamp-2 leading-snug mb-3">
               {{ post.prompt_preview || 'No prompt info' }}
             </p>
             <div class="flex items-center justify-between mt-auto">
               <span class="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant bg-surface-container px-2 py-1 rounded-md">ID: {{ post.id }}</span>
               <span class="material-symbols-outlined text-outline-variant text-[18px] group-hover:text-primary transition-colors">arrow_forward</span>
             </div>
          </div>
        </div>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const router = useRouter()
const auth   = useAuthStore()

const posts   = ref([])
const loading = ref(true)
const error   = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/history')
    posts.value = res.data
  } catch (e) {
    error.value = "Failed to load history."
  } finally {
    loading.value = false
  }
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
