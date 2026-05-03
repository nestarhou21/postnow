<template>
  <div class="min-h-screen bg-bg flex flex-col font-body bg-surface text-on-surface">
    <!-- Top Bar -->
    <header class="px-8 py-6 border-b border-surface-container-high bg-surface-lowest flex justify-center lg:justify-start">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary text-[28px]" style="font-variation-settings: 'FILL' 1;">coffee</span>
        <span class="text-2xl font-extrabold text-primary font-headline tracking-tight">POSTNOW</span>
      </div>
    </header>

    <main class="flex-1 flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      <!-- Background glows -->
      <div class="absolute top-1/4 -right-20 w-96 h-96 bg-primary-container/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
      <div class="absolute bottom-1/4 -left-20 w-96 h-96 bg-secondary-container/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

      <div class="w-full max-w-2xl relative z-10">
        
        <!-- Mascot Row -->
        <div class="flex items-end gap-4 mb-10 transition-all duration-500">
          <img src="/Asset.png" alt="Brew" class="w-28 drop-shadow-xl animate-[float_4s_ease-in-out_infinite]" />
          <div class="bg-surface-container-lowest border border-outline-variant/30 p-4 rounded-2xl rounded-bl-sm shadow-md mb-2">
            <p class="text-sm font-bold text-on-surface-variant">
              <span v-if="step === 1">Hi! I'm Brew. Let's set up your shop!</span>
              <span v-else-if="step === 2">Great name! What's your vibe?</span>
              <span v-else>Almost done — pick your brand colors!</span>
            </p>
          </div>
        </div>

        <!-- Step Track -->
        <div class="relative flex items-center justify-between mb-12">
          <!-- Track line background -->
          <div class="absolute top-1/2 left-4 right-4 h-0.5 bg-surface-container-high -translate-y-1/2 z-0"></div>
          <!-- Track line active -->
          <div class="absolute top-1/2 left-4 h-0.5 bg-primary transition-all duration-500 -translate-y-1/2 z-0" :style="{ width: ((step - 1) / 2 * 100) + '%' }"></div>

          <div v-for="i in 3" :key="i" class="flex flex-col items-center gap-2 z-10">
            <div :class="[
              'w-10 h-10 rounded-full border-[3px] flex items-center justify-center text-sm font-bold transition-all duration-300 shadow-sm bg-surface',
              step > i ? 'bg-primary border-primary text-on-primary' : 
              step === i ? 'border-primary text-primary' : 'border-surface-variant text-on-surface-variant'
            ]">
              <span v-if="step > i" class="material-symbols-outlined text-[20px]" style="font-variation-settings: 'FILL' 1;">check</span>
              <span v-else>{{ i }}</span>
            </div>
            <span :class="[
              'text-[11px] font-bold tracking-widest uppercase transition-colors',
              step >= i ? 'text-on-surface' : 'text-on-surface-variant'
            ]">{{ ['Shop Name', 'Aesthetic', 'Colors'][i - 1] }}</span>
          </div>
        </div>

        <!-- Main Card -->
        <div class="bg-surface-container-lowest rounded-[24px] shadow-[0_20px_40px_rgba(61,35,20,0.06)] border border-surface-container-high p-8 md:p-10 transition-all duration-300">
          
          <!-- Step 1 -->
          <div v-if="step === 1" class="animate-[fadeUp_0.4s_ease_both]">
            <h2 class="font-headline text-3xl font-extrabold text-on-surface mb-2">What's your shop called?</h2>
            <p class="text-on-surface-variant text-sm font-medium mb-8">This name will appear on every poster we generate for you.</p>
            
            <div class="relative">
              <input
                v-model="shopName"
                type="text"
                placeholder="e.g. Slow Drip Café"
                maxlength="60"
                class="w-full bg-surface-container border border-transparent focus:border-primary/30 focus:ring-4 focus:ring-primary/10 rounded-xl px-5 py-4 text-on-surface text-lg font-bold placeholder:text-on-surface-variant/40 transition-all outline-none shadow-inner"
                @keyup.enter="shopName.trim() && (step = 2)"
              />
              <div class="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-bold text-on-surface-variant">
                {{ shopName.length }}/60
              </div>
            </div>

            <button class="w-full bg-primary text-white font-bold text-base py-4 rounded-full shadow-[0_8px_16px_rgba(119,88,56,0.15)] hover:bg-[#8B6B4A] hover:shadow-[0_12px_24px_rgba(119,88,56,0.25)] hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-10 flex items-center justify-center gap-2" :disabled="!shopName.trim()" @click="step = 2">
              Next — Choose Aesthetic
              <span class="material-symbols-outlined">arrow_forward</span>
            </button>
          </div>

          <!-- Step 2 -->
          <div v-if="step === 2" class="animate-[fadeUp_0.4s_ease_both]">
            <h2 class="font-headline text-3xl font-extrabold text-on-surface mb-2">What's your aesthetic?</h2>
            <p class="text-on-surface-variant text-sm font-medium mb-8">This shapes the mood of every poster and caption.</p>
            
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
              <div
                v-for="opt in aesthetics" :key="opt.value"
                @click="aesthetic = opt.value"
                :class="[
                  'border-2 rounded-2xl p-5 cursor-pointer transition-all flex flex-col justify-center items-center text-center gap-2 relative overflow-hidden group',
                  aesthetic === opt.value ? 'border-primary bg-primary/5 shadow-md scale-100' : 'border-surface-container-high bg-surface hover:bg-surface-container hover:border-outline-variant/50'
                ]"
              >
                <!-- Active background gradient -->
                <div v-if="aesthetic === opt.value" class="absolute inset-0 bg-gradient-to-b from-primary/10 to-transparent pointer-events-none"></div>
                <span class="text-4xl mb-2 group-hover:scale-110 transition-transform">{{ opt.emoji }}</span>
                <span class="font-headline font-bold text-on-surface uppercase tracking-widest text-xs">{{ opt.label }}</span>
                <span class="text-xs font-medium text-on-surface-variant">{{ opt.desc }}</span>
              </div>
            </div>

            <div class="flex gap-4">
              <button class="px-6 py-4 rounded-full bg-surface-container font-bold text-on-surface hover:bg-surface-variant transition-colors flex items-center gap-2" @click="step = 1">
                <span class="material-symbols-outlined">arrow_back</span>
                Back
              </button>
              <button class="flex-1 bg-primary text-white font-bold text-base py-4 rounded-full shadow-[0_8px_16px_rgba(119,88,56,0.15)] hover:bg-[#8B6B4A] hover:shadow-[0_12px_24px_rgba(119,88,56,0.25)] hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2" :disabled="!aesthetic" @click="step = 3">
                Next — Pick Colors
                <span class="material-symbols-outlined">arrow_forward</span>
              </button>
            </div>
          </div>

          <!-- Step 3 -->
          <div v-if="step === 3" class="animate-[fadeUp_0.4s_ease_both]">
            <h2 class="font-headline text-3xl font-extrabold text-on-surface mb-2">Your brand colors</h2>
            <p class="text-on-surface-variant text-sm font-medium mb-8">We use these to consistently brand your generated posters.</p>
            
            <div class="flex justify-center gap-6 sm:gap-12 mb-8">
              <div v-for="(c, i) in colors" :key="i" class="flex flex-col items-center gap-3">
                <div class="w-16 h-16 rounded-full p-1 border-2 shadow-sm transition-colors relative" :style="{ borderColor: colors[i] }">
                  <!-- Real color input inside the circle -->
                  <input type="color" v-model="colors[i]" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" :title="`Color ${i + 1}`" />
                  <div class="w-full h-full rounded-full" :style="{ backgroundColor: colors[i] }"></div>
                </div>
                <div class="flex flex-col items-center">
                  <span class="text-xs uppercase tracking-widest font-bold text-on-surface-variant">Color {{ i + 1 }}</span>
                  <span class="text-xs font-mono text-on-surface font-semibold">{{ colors[i] }}</span>
                </div>
              </div>
            </div>

            <!-- Gradient Preview -->
            <div class="mb-10">
              <p class="text-xs font-bold text-on-surface uppercase tracking-widest mb-3 text-center">Gradient Preview</p>
              <div class="h-10 rounded-xl shadow-inner border border-surface-container-highest" :style="{ background: previewGradient }"></div>
            </div>

            <p v-if="saveError" class="text-error text-sm font-semibold bg-error-container/50 px-4 py-3 rounded-lg border border-error/20 mb-6 flex items-center gap-2">
              <span class="material-symbols-outlined text-[18px]">error</span>
              {{ saveError }}
            </p>

            <div class="flex gap-4">
              <button class="px-6 py-4 rounded-full bg-surface-container font-bold text-on-surface hover:bg-surface-variant transition-colors flex items-center gap-2" @click="step = 2">
                <span class="material-symbols-outlined">arrow_back</span>
                Back
              </button>
              <button class="flex-1 bg-primary text-white font-bold text-base py-4 rounded-full shadow-[0_8px_16px_rgba(119,88,56,0.15)] hover:bg-[#8B6B4A] hover:shadow-[0_12px_24px_rgba(119,88,56,0.25)] hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2" :disabled="saving" @click="save">
                <span v-if="saving" class="material-symbols-outlined animate-spin">progress_activity</span>
                <span v-else>Finish Setup</span>
                <span v-if="!saving" class="material-symbols-outlined">check</span>
              </button>
            </div>
          </div>

        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const router = useRouter()
const auth   = useAuthStore()

const step     = ref(1)
const shopName = ref('')
const aesthetic= ref('')
const colors   = ref(['#C87941', '#FFF8F0', '#5C3317'])
const saving   = ref(false)
const saveError= ref('')

const aesthetics = [
  { value: 'Cozy',       emoji: '🌿', label: 'Cozy',       desc: 'Warm, soft & inviting' },
  { value: 'Bold',       emoji: '⚡', label: 'Bold',       desc: 'Vibrant & energetic' },
  { value: 'Minimalist', emoji: '🤍', label: 'Minimalist', desc: 'Clean, simple & elegant' },
]

const previewGradient = computed(
  () => `linear-gradient(90deg, ${colors.value.join(', ')})`
)

async function save() {
  saving.value   = true
  saveError.value = ''
  try {
    await api.post('/profile', {
      shop_name: shopName.value.trim(),
      aesthetic: aesthetic.value,
      colors: colors.value,
    })
    auth.hasProfile = true
    router.push('/home')
  } catch (e) {
    saveError.value = e.response?.data?.detail || 'Failed to save. Try again.'
  } finally {
    saving.value = false
  }
}
</script>

<style>
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(-10px); }
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
