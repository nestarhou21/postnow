<template>
  <div class="min-h-screen bg-surface flex flex-col font-body text-on-surface">

    <!-- Header -->
    <header class="px-6 sm:px-8 py-4 border-b border-surface-container-high bg-surface-lowest flex justify-between items-center sticky top-0 z-50 shadow-sm">
      <div class="flex items-center gap-3">
        <span class="material-symbols-outlined text-primary text-[28px]" style="font-variation-settings: 'FILL' 1;">coffee</span>
        <span class="text-xl font-extrabold text-primary font-headline tracking-tight">POSTNOW</span>
      </div>
      <div class="flex items-center gap-4">
        <button @click="router.push('/history')" class="text-xs font-bold uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors hidden sm:block">
          History
        </button>
        <button @click="logout" class="text-xs font-bold uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors">
          Logout
        </button>
      </div>
    </header>

    <!-- Main -->
    <main class="flex-1 max-w-2xl w-full mx-auto px-4 sm:px-6 py-10 flex flex-col gap-8">

      <!-- Title -->
      <div>
        <h1 class="font-headline text-4xl sm:text-5xl font-extrabold text-on-surface tracking-tight">What's your promotion today?</h1>
        <p class="text-on-surface-variant mt-2 font-medium">Generate a bilingual poster in under 2 minutes.</p>
      </div>

      <!-- Shop badge -->
      <div v-if="auth.profile" class="flex items-center gap-2 px-4 py-2 bg-surface-container rounded-full border border-surface-container-high w-fit">
        <div class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
        <span class="text-xs font-bold text-on-surface-variant tracking-wide">{{ auth.profile.shop_name }} · {{ auth.profile.aesthetic }}</span>
      </div>

      <!-- Promotion input -->
      <div class="flex flex-col gap-2">
        <label class="text-xs font-bold uppercase tracking-widest text-on-surface-variant">Promotion</label>
        <textarea
          v-model="prompt"
          :disabled="loading"
          placeholder="e.g. Buy 1 Get 1 Latte this weekend"
          rows="3"
          class="w-full bg-surface-container-low border border-surface-container-high focus:border-primary focus:ring-2 focus:ring-primary/20 rounded-2xl px-5 py-4 text-base text-on-surface outline-none resize-none transition-all placeholder:text-on-surface-variant/50 disabled:opacity-50"
        ></textarea>
      </div>

      <!-- Reference photo upload -->
      <div class="flex flex-col gap-2">
        <label class="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
          Reference Photo
          <span class="ml-2 font-normal normal-case text-on-surface-variant/60">(optional — upload a coffee shop photo)</span>
        </label>

        <!-- Preview state -->
        <div v-if="photoPreview" class="relative rounded-2xl overflow-hidden border border-surface-container-high group">
          <img :src="photoPreview" class="w-full h-52 object-cover" alt="Reference photo" />
          <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <button @click="removePhoto" class="px-4 py-2 bg-white rounded-full text-sm font-bold text-on-surface shadow-md hover:bg-gray-100 transition-colors flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">delete</span>
              Remove photo
            </button>
          </div>
        </div>

        <!-- Drop zone -->
        <div
          v-else
          @click="fileInput?.click()"
          @dragover.prevent="dragOver = true"
          @dragleave="dragOver = false"
          @drop.prevent="handleDrop"
          :class="[
            'border-2 border-dashed rounded-2xl h-36 flex flex-col items-center justify-center gap-2 cursor-pointer transition-all',
            dragOver
              ? 'border-primary bg-primary/5'
              : 'border-surface-container-highest bg-surface-container-low hover:border-primary/50 hover:bg-surface-container'
          ]"
        >
          <span class="material-symbols-outlined text-[32px] text-on-surface-variant">add_photo_alternate</span>
          <p class="text-sm text-on-surface-variant font-medium">Click to upload or drag and drop</p>
          <p class="text-xs text-on-surface-variant/60">JPG, PNG, WEBP up to 10 MB</p>
        </div>

        <input
          ref="fileInput"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          class="hidden"
          @change="handleFileChange"
        />
      </div>

      <!-- Template picker -->
      <div class="flex flex-col gap-3">
        <label class="text-xs font-bold uppercase tracking-widest text-on-surface-variant">Poster Style</label>
        <div class="grid grid-cols-2 gap-3">
          <button
            v-for="t in templates"
            :key="t.id"
            @click="selectedTemplate = t.id"
            :class="[
              'p-4 rounded-2xl border-2 text-left transition-all',
              selectedTemplate === t.id
                ? 'border-primary bg-primary/5 shadow-sm'
                : 'border-surface-container-high bg-surface-container-low hover:border-primary/40'
            ]"
          >
            <div class="text-xl mb-1.5">{{ t.icon }}</div>
            <div class="font-bold text-sm text-on-surface">{{ t.label }}</div>
            <div class="text-xs text-on-surface-variant mt-0.5">{{ t.desc }}</div>
          </button>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="flex items-start gap-3 bg-error/10 text-error rounded-2xl px-5 py-4 text-sm font-medium">
        <span class="material-symbols-outlined text-[20px] mt-0.5 shrink-0">error</span>
        <span>{{ error }}</span>
      </div>

      <!-- Generate button -->
      <button
        @click="generate"
        :disabled="!prompt.trim() || loading"
        class="w-full bg-primary text-white font-bold text-base py-5 rounded-full shadow-[0_8px_16px_rgba(119,88,56,0.2)] hover:bg-[#8B6B4A] hover:-translate-y-0.5 hover:shadow-[0_12px_24px_rgba(119,88,56,0.3)] active:translate-y-0 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 flex items-center justify-center gap-3"
      >
        <span v-if="loading" class="flex items-center gap-3">
          <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
          Brewing your post...
        </span>
        <span v-else class="flex items-center gap-2">
          <span class="material-symbols-outlined text-[20px]">auto_awesome</span>
          Create My Post
        </span>
      </button>

    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const router = useRouter()
const auth   = useAuthStore()

const prompt           = ref('')
const selectedTemplate = ref('centered')
const loading          = ref(false)
const error            = ref('')
const dragOver         = ref(false)
const fileInput        = ref(null)
const photoPreview     = ref('')
const photoBase64      = ref('')
const photoMime        = ref('image/jpeg')

const templates = [
  { id: 'centered',    icon: '☕', label: 'Centered',    desc: 'Product hero shot' },
  { id: 'text_banner', icon: '✍️', label: 'Text Banner', desc: 'Bold typography' },
  { id: 'lifestyle',   icon: '🌿', label: 'Lifestyle',   desc: 'Warm cafe scene' },
  { id: 'minimal',     icon: '⬜', label: 'Minimal',     desc: 'Clean & elegant' },
]

function logout() {
  auth.logout()
  router.push('/login')
}

function removePhoto() {
  photoPreview.value  = ''
  photoBase64.value   = ''
  if (fileInput.value) fileInput.value.value = ''
}

function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (file) loadPhoto(file)
}

function handleDrop(e) {
  dragOver.value = false
  const file = e.dataTransfer.files?.[0]
  if (file && file.type.startsWith('image/')) loadPhoto(file)
}

function loadPhoto(file) {
  if (file.size > 10 * 1024 * 1024) {
    error.value = 'Photo must be under 10 MB.'
    return
  }
  photoMime.value = file.type || 'image/jpeg'
  const reader = new FileReader()
  reader.onload = (e) => {
    const dataUrl = e.target.result
    photoPreview.value = dataUrl
    // Strip the "data:image/...;base64," prefix — backend expects raw base64
    photoBase64.value  = dataUrl.split(',')[1]
  }
  reader.readAsDataURL(file)
}

async function generate() {
  if (!prompt.value.trim() || loading.value) return
  error.value   = ''
  loading.value = true

  try {
    const body = {
      prompt:      prompt.value.trim(),
      template_id: selectedTemplate.value,
    }
    if (photoBase64.value) {
      body.reference_image_base64 = photoBase64.value
      body.reference_image_mime   = photoMime.value
    }

    const res = await api.post('/generate', body)

    // Store result in sessionStorage so ResultView can read it
    sessionStorage.setItem('postnow_result', JSON.stringify({
      id:         res.data.generation_id,
      image_url:  res.data.image_data_url,
      caption_en: res.data.en_caption,
      caption_km: res.data.kh_caption,
      hashtags:   res.data.hashtags,
    }))

    router.push(`/result/${res.data.generation_id}`)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Generation failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
