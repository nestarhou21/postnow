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
      
      <div v-if="auth.profile || auth.user" class="flex items-center gap-4">
        <div class="flex items-center gap-3">
          <button class="w-10 h-10 rounded-full border-2 border-primary bg-primary/10 flex items-center justify-center font-headline font-bold text-primary shadow-inner pointer-events-none">
            <span class="material-symbols-outlined text-[20px]">person</span>
          </button>
        </div>
      </div>
    </header>

    <main class="flex-1 max-w-[800px] w-full mx-auto p-4 sm:p-8">
      
      <div class="mb-8">
        <h1 class="font-headline text-3xl font-extrabold text-on-surface tracking-tight mb-2">Shop Profile.</h1>
        <p class="text-on-surface-variant text-sm font-medium">Manage your workspace details and branding preferences.</p>
      </div>

      <div class="bg-surface-container-lowest rounded-3xl p-6 md:p-10 shadow-sm border border-surface-container-high flex flex-col gap-8">
        
        <div v-if="successMsg" class="bg-green-100 text-green-800 border border-green-200 px-4 py-3 rounded-xl text-sm font-bold flex items-center gap-2">
          <span class="material-symbols-outlined text-[18px]">check_circle</span>
          {{ successMsg }}
        </div>

        <form @submit.prevent="saveProfile" class="flex flex-col gap-6">
           <div class="flex flex-col gap-2">
              <label class="text-xs font-bold uppercase tracking-widest text-on-surface-variant">Shop Name</label>
              <input 
                v-model="shopName" 
                type="text" 
                class="w-full bg-surface-container-low border border-surface-container focus:border-primary/50 focus:ring-4 focus:ring-primary/10 rounded-xl px-4 py-3 text-on-surface font-medium outline-none transition-all"
                placeholder="e.g. The Daily Grind"
              />
           </div>

           <div class="flex flex-col gap-2">
              <label class="text-xs font-bold uppercase tracking-widest text-on-surface-variant">Account Email</label>
              <input 
                :value="auth.user?.email" 
                disabled
                type="text" 
                class="w-full bg-surface-container-high border border-surface-container-highest rounded-xl px-4 py-3 text-on-surface-variant font-medium outline-none cursor-not-allowed opacity-70"
              />
              <p class="text-xs text-on-surface-variant mt-1">Email cannot be changed directly. Contact support.</p>
           </div>
           
           <hr class="border-surface-container my-2" />

           <div>
              <p class="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4">Danger Zone</p>
              <button type="button" @click="logout" class="px-6 py-3 rounded-xl border border-error/30 text-error font-bold hover:bg-error-container/20 transition-colors flex items-center gap-2 w-max">
                 <span class="material-symbols-outlined text-[18px]">logout</span>
                 Sign Out of Postnow
              </button>
           </div>

           <div class="mt-4 flex justify-end">
              <button type="submit" :disabled="!isChanged" class="px-8 py-3 rounded-full bg-primary text-white font-bold shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95">
                 Save Changes
              </button>
           </div>
        </form>

      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth   = useAuthStore()

const shopName   = ref('')
const initialVal = ref('')
const successMsg = ref('')

onMounted(() => {
  shopName.value = auth.profile?.shop_name || auth.user?.email?.split('@')[0] || 'My Coffee Shop'
  initialVal.value = shopName.value
})

const isChanged = computed(() => shopName.value.trim() !== initialVal.value && shopName.value.trim().length > 0)

function saveProfile() {
  if (!isChanged.value) return
  
  // Minimal mock update since backend is unavailable
  auth.user.shop_name = shopName.value.trim()
  initialVal.value = shopName.value.trim()
  
  // Update local storage reference used in mock fetchMe
  const storedUser = JSON.parse(localStorage.getItem('postnow_user') || '{}')
  storedUser.shop_name = shopName.value.trim()
  localStorage.setItem('postnow_user', JSON.stringify(storedUser))
  
  successMsg.value = 'Shop profile updated successfully.'
  setTimeout(() => successMsg.value = '', 3000)
}

function logout() {
  auth.logout()
  router.push('/')
}
</script>
