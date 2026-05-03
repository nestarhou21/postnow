<template>
  <div class="min-h-screen flex bg-[#FDFCFB] font-mono text-[#111111]">
    
    <!-- Left: Brand Panel -->
    <div class="hidden lg:flex flex-col flex-1 border-r border-[#E0E0E0] p-12 relative overflow-hidden bg-white">
      <div class="relative z-10 flex flex-col h-full justify-between">
        <div>
          <div class="flex items-center gap-4 mb-24">
            <span class="font-bold tracking-tighter text-xl uppercase bg-black text-white px-3 py-1">POSTNOW</span>
            <span class="text-xs text-gray-500 uppercase tracking-widest border-l border-gray-300 pl-4">System Access</span>
          </div>
          <h1 class="text-5xl font-bold uppercase tracking-tighter leading-[1.1] mb-6 max-w-lg">
            Strict Control.<br/>Absolute Precision.
          </h1>
          <p class="text-sm text-gray-500 uppercase tracking-widest leading-loose max-w-md">
            Section 1: Fine-tuned Caption Generation.<br/>
            Section 2: Gemini Direct Image Integration.
          </p>
        </div>

        <div class="space-y-4">
          <div class="flex items-center gap-4 border-t border-black pt-4">
            <span class="text-xs font-bold uppercase tracking-widest w-24">Status</span>
            <span class="text-xs text-green-600 uppercase tracking-widest flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-green-600 block"></span> Systems Online
            </span>
          </div>
          <div class="flex items-center gap-4 border-t border-[#E0E0E0] pt-4">
            <span class="text-xs font-bold uppercase tracking-widest w-24">Auth</span>
            <span class="text-xs text-gray-500 uppercase tracking-widest">Mock Enabled (Accepts All)</span>
          </div>
        </div>
      </div>
      
      <!-- Abstract Grid Graphic -->
      <div class="absolute inset-0 z-0 opacity-5 pointer-events-none" style="background-image: linear-gradient(#000 1px, transparent 1px), linear-gradient(90deg, #000 1px, transparent 1px); background-size: 32px 32px;"></div>
    </div>

    <!-- Right: Form Panel -->
    <div class="w-full lg:w-[600px] flex flex-col items-center justify-center p-8 sm:p-16 relative bg-[#FAFAFA]">
      
      <!-- Mobile Logo -->
      <div class="flex lg:hidden items-center gap-4 absolute top-8 left-8">
        <span class="font-bold tracking-tighter text-lg uppercase bg-black text-white px-2 py-0.5">POSTNOW</span>
      </div>

      <div class="w-full max-w-sm">
        
        <div class="mb-12 border-b border-black pb-4">
          <h2 class="text-3xl font-bold uppercase tracking-tight mb-1">
            Authentication
          </h2>
          <p class="text-xs text-gray-500 uppercase tracking-widest">
            Enter any credentials to proceed.
          </p>
        </div>

        <form @submit.prevent="submit" class="space-y-8">
          <div>
            <label class="block text-xs font-bold uppercase tracking-widest mb-3">Email Address</label>
            <input 
              v-model="email" 
              type="email" 
              placeholder="operator@system.local" 
              required 
              class="w-full bg-white border border-gray-300 focus:border-black focus:ring-1 focus:ring-black rounded-sm px-4 py-3 text-sm transition-colors outline-none font-sans" 
            />
          </div>

          <div>
            <label class="block text-xs font-bold uppercase tracking-widest mb-3">Passcode</label>
            <input 
              v-model="password" 
              type="password" 
              placeholder="••••••••" 
              required 
              class="w-full bg-white border border-gray-300 focus:border-black focus:ring-1 focus:ring-black rounded-sm px-4 py-3 text-sm transition-colors outline-none font-sans" 
            />
          </div>

          <p v-if="error" class="text-red-700 bg-red-50 text-xs font-bold uppercase tracking-widest p-4 border border-red-200">
            [Error] {{ error }}
          </p>

          <button 
            type="submit" 
            :disabled="loading" 
            class="w-full bg-black text-white font-bold uppercase tracking-widest text-xs py-5 rounded-sm hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-4 flex items-center justify-center gap-2"
          >
            <span v-if="loading">Verifying...</span>
            <span v-else>Initialize Session</span>
          </button>
        </form>

        <div class="mt-16 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-center">
          Terminal Access Only
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth   = useAuthStore()
const router = useRouter()

const email    = ref('')
const password = ref('')
const error    = ref('')
const loading  = ref(false)

async function submit() {
  error.value   = ''
  loading.value = true
  try {
    // Simply using login since it's mocked to accept anything
    await auth.login(email.value, password.value)
    router.push(auth.hasProfile ? '/home' : '/onboarding')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Authentication failed. Retry.'
  } finally {
    loading.value = false
  }
}
</script>
