<template>
  <div class="h-screen flex flex-col bg-[#111009] text-[#ece8e3] overflow-hidden">

    <!-- Header -->
    <header class="flex items-center justify-between px-5 py-3 border-b border-white/8 shrink-0">
      <div class="flex items-center gap-2.5">
        <img :src="botAvatar" class="w-8 h-8 rounded-full object-cover" />
        <span class="font-bold text-[#C8A27C] text-base tracking-tight">POSTNOW</span>
        <span class="text-xs text-[#444] hidden sm:block">· AI Poster Generator</span>
      </div>
      <div class="flex items-center gap-2">
        <input v-model="shopName" placeholder="Shop name"
          class="hidden sm:block bg-[#1e1c18] border border-white/8 text-[#ece8e3] text-xs rounded-lg px-3 py-1.5 outline-none focus:border-[#C8A27C]/40 w-36 placeholder:text-[#444]" />
        <select v-model="aesthetic"
          class="hidden sm:block bg-[#1e1c18] border border-white/8 text-[#777] text-xs rounded-lg px-2 py-1.5 outline-none focus:border-[#C8A27C]/40">
          <option>Cozy</option><option>Bold</option><option>Minimalist</option>
        </select>
      </div>
    </header>

    <!-- Chat -->
    <div ref="chatEl" class="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-5">
      <div class="max-w-2xl w-full mx-auto flex flex-col gap-5">

        <!-- Welcome -->
        <div class="flex gap-3 items-start">
          <img :src="botAvatar" class="w-8 h-8 rounded-full object-cover shrink-0 mt-0.5" />
          <div class="bg-[#1e1c18] border border-white/6 rounded-2xl rounded-tl-sm px-5 py-4 max-w-lg">
            <p class="font-semibold text-[#C8A27C] mb-1.5">Welcome to POSTNOW</p>
            <p class="text-sm text-[#aaa] leading-relaxed">Tell me your promotion and I'll generate a branded poster with captions in English and Khmer. Attach a photo of your drink for a more personalised result.</p>
          </div>
        </div>

        <!-- Messages -->
        <template v-for="(msg, i) in messages" :key="i">

          <!-- User -->
          <div v-if="msg.role === 'user'" class="flex gap-3 items-start flex-row-reverse">
            <div class="w-8 h-8 rounded-full bg-[#3a2e25] border border-white/10 flex items-center justify-center shrink-0 mt-0.5 text-sm">🧑</div>
            <div class="bg-[#2a2218] border border-white/6 rounded-2xl rounded-tr-sm px-5 py-3.5 max-w-lg">
              <p class="text-sm text-[#ece8e3] leading-relaxed">{{ msg.text }}</p>
              <img v-if="msg.photo" :src="msg.photo" class="mt-3 rounded-xl max-h-48 w-full object-contain border border-white/10 bg-[#111]" />
            </div>
          </div>

          <!-- Loading with steps -->
          <div v-else-if="msg.role === 'loading'" class="flex gap-3 items-start">
            <img :src="botAvatar" class="w-8 h-8 rounded-full object-cover shrink-0 mt-0.5" />
            <div class="bg-[#1e1c18] border border-white/6 rounded-2xl rounded-tl-sm px-5 py-4">
              <div class="flex items-center gap-3">
                <div class="flex gap-1 shrink-0">
                  <span class="w-1.5 h-1.5 bg-[#C8A27C] rounded-full animate-bounce [animation-delay:0ms]"></span>
                  <span class="w-1.5 h-1.5 bg-[#C8A27C] rounded-full animate-bounce [animation-delay:150ms]"></span>
                  <span class="w-1.5 h-1.5 bg-[#C8A27C] rounded-full animate-bounce [animation-delay:300ms]"></span>
                </div>
                <span class="text-sm text-[#888] transition-all">{{ msg.text }}</span>
              </div>
            </div>
          </div>

          <!-- Result -->
          <div v-else-if="msg.role === 'assistant'" class="flex gap-3 items-start">
            <img :src="botAvatar" class="w-8 h-8 rounded-full object-cover shrink-0 mt-0.5" />
            <div class="bg-[#1e1c18] border border-white/6 rounded-2xl rounded-tl-sm px-5 py-5 max-w-xl w-full flex flex-col gap-4">

              <!-- Poster -->
              <div>
                <p class="text-[10px] text-[#555] uppercase tracking-widest mb-2.5 font-bold">Your Poster</p>
                <img :src="msg.image_url" class="rounded-xl w-full border border-white/8 shadow-2xl" />
              </div>

              <!-- Captions -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                <div class="bg-[#111009] rounded-xl p-4 border border-white/6">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-[10px] font-bold text-[#555] uppercase tracking-widest">🇺🇸 English</span>
                    <button @click="copy(msg.caption_en)" class="text-[#555] hover:text-[#C8A27C] transition-colors">
                      <span class="material-symbols-outlined text-[15px]">content_copy</span>
                    </button>
                  </div>
                  <p class="text-xs text-[#bbb] leading-relaxed">{{ msg.caption_en }}</p>
                </div>
                <div class="bg-[#111009] rounded-xl p-4 border border-white/6">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-[10px] font-bold text-[#555] uppercase tracking-widest">🇰🇭 Khmer</span>
                    <button @click="copy(msg.caption_km)" class="text-[#555] hover:text-[#C8A27C] transition-colors">
                      <span class="material-symbols-outlined text-[15px]">content_copy</span>
                    </button>
                  </div>
                  <p class="text-xs text-[#bbb] leading-relaxed">{{ msg.caption_km }}</p>
                </div>
              </div>

              <!-- Hashtags -->
              <div class="flex flex-wrap gap-1.5">
                <span v-for="tag in msg.hashtags.split(' ').filter(t => t)" :key="tag"
                  class="text-[10px] px-2.5 py-1 rounded-full bg-[#C8A27C]/10 text-[#C8A27C] border border-[#C8A27C]/20 font-medium">
                  {{ tag }}
                </span>
              </div>

              <!-- Download -->
              <button @click="downloadImage(msg.image_url, msg.id)"
                class="flex items-center gap-2 w-fit px-5 py-2.5 bg-[#C8A27C] hover:bg-[#b8926c] text-[#111] rounded-full text-xs font-bold transition-all">
                <span class="material-symbols-outlined text-[16px]">download</span>
                Download Poster
              </button>
            </div>
          </div>

          <!-- Error -->
          <div v-else-if="msg.role === 'error'" class="flex gap-3 items-start">
            <img :src="botAvatar" class="w-8 h-8 rounded-full object-cover shrink-0 mt-0.5" />
            <div class="bg-red-950/30 border border-red-500/20 rounded-2xl rounded-tl-sm px-5 py-4 max-w-lg text-sm text-red-400">
              {{ msg.text }}
            </div>
          </div>

        </template>
      </div>
    </div>

    <!-- Input area -->
    <div class="shrink-0 px-4 pb-5 pt-3 border-t border-white/6">
      <div class="max-w-2xl mx-auto flex flex-col gap-2.5">

        <!-- Image preview (larger, full width) -->
        <div v-if="photoPreview" class="bg-[#1e1c18] border border-white/8 rounded-2xl p-3 flex items-center gap-3">
          <img :src="photoPreview" class="h-20 w-20 object-cover rounded-xl border border-white/10 shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="text-xs text-[#aaa] font-medium">Photo attached</p>
            <p class="text-[10px] text-[#555] mt-0.5">This will be used as reference for the drink</p>
          </div>
          <button @click="removePhoto" class="text-[#555] hover:text-red-400 transition-colors shrink-0">
            <span class="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <!-- Input bar -->
        <div :class="[
          'flex items-end gap-2 bg-[#1e1c18] border rounded-2xl px-4 py-3 transition-all',
          inputFocused ? 'border-[#C8A27C]/40' : 'border-white/8'
        ]">
          <button @click="fileInput?.click()" class="text-[#555] hover:text-[#C8A27C] transition-colors mb-0.5 shrink-0" title="Attach drink photo">
            <span class="material-symbols-outlined text-[22px]">attach_file</span>
          </button>
          <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFileChange" />

          <textarea
            ref="promptEl"
            v-model="prompt"
            :disabled="loading"
            placeholder="Describe your promotion… e.g. Buy 1 Get 1 Latte this weekend"
            rows="1"
            @focus="inputFocused = true"
            @blur="inputFocused = false"
            @input="autoGrow"
            @keydown.enter.exact.prevent="generate"
            @keydown.shift.enter="null"
            class="flex-1 bg-transparent outline-none resize-none text-sm text-[#ece8e3] placeholder:text-[#444] max-h-32 leading-relaxed disabled:opacity-40"
          ></textarea>

          <button @click="generate" :disabled="!prompt.trim() || loading"
            class="w-8 h-8 rounded-xl flex items-center justify-center mb-0.5 transition-all disabled:opacity-25 disabled:cursor-not-allowed shrink-0"
            :class="prompt.trim() && !loading ? 'bg-[#C8A27C] hover:bg-[#b8926c]' : 'bg-[#2a2820]'">
            <svg width="14" height="14" viewBox="0 0 24 24" :fill="prompt.trim() && !loading ? '#111' : '#666'">
              <path d="M2 21l21-9L2 3v7l15 2-15 2z"/>
            </svg>
          </button>
        </div>

        <p class="text-center text-[10px] text-[#333]">Enter to send · Shift+Enter for new line · Cmd+V to paste image</p>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="toast" class="fixed bottom-24 left-1/2 -translate-x-1/2 bg-[#2a2820] text-[#ece8e3] text-xs font-bold px-5 py-2.5 rounded-full shadow-xl z-50 flex items-center gap-2 border border-white/10">
      <span class="material-symbols-outlined text-green-400 text-[15px]">check_circle</span>
      {{ toast }}
    </div>

  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import api from '../api'
import botAvatar from '../assets/bot.png'

const prompt       = ref('')
const shopName     = ref('My Café')
const aesthetic    = ref('Cozy')
const loading      = ref(false)
const inputFocused = ref(false)
const toast        = ref('')
const photoPreview = ref('')
const photoBase64  = ref('')
const photoMime    = ref('image/jpeg')
const messages     = ref([])
const chatEl       = ref(null)
const promptEl     = ref(null)
const fileInput    = ref(null)

const LOADING_STEPS = [
  'Analyzing your promotion…',
  'Crafting a creative concept…',
  'Generating your poster with Gemini…',
  'Writing bilingual captions…',
  'Almost done…',
]

function autoGrow(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

function scrollToBottom() {
  nextTick(() => {
    if (chatEl.value) chatEl.value.scrollTop = chatEl.value.scrollHeight
  })
}

function removePhoto() {
  photoPreview.value = ''
  photoBase64.value  = ''
  if (fileInput.value) fileInput.value.value = ''
}

function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (file) loadPhoto(file)
}

function loadPhoto(file) {
  if (file.size > 10 * 1024 * 1024) { showToast('Photo must be under 10 MB'); return }
  photoMime.value = file.type || 'image/jpeg'
  const reader = new FileReader()
  reader.onload = (e) => {
    photoPreview.value = e.target.result
    photoBase64.value  = e.target.result.split(',')[1]
  }
  reader.readAsDataURL(file)
}

document.addEventListener('paste', (e) => {
  for (const item of e.clipboardData.items) {
    if (item.type.startsWith('image/')) { loadPhoto(item.getAsFile()); break }
  }
})

async function generate() {
  if (!prompt.value.trim() || loading.value) return

  const text  = prompt.value.trim()
  const photo = photoPreview.value

  messages.value.push({ role: 'user', text, photo })
  prompt.value       = ''
  photoPreview.value = ''
  if (promptEl.value) promptEl.value.style.height = 'auto'
  scrollToBottom()

  loading.value = true

  // Loading message with cycling steps
  const loadingMsg = { role: 'loading', text: LOADING_STEPS[0] }
  messages.value.push(loadingMsg)
  scrollToBottom()

  let step = 0
  const stepInterval = setInterval(() => {
    step = Math.min(step + 1, LOADING_STEPS.length - 1)
    loadingMsg.text = LOADING_STEPS[step]
  }, 6000)

  try {
    const body = {
      prompt:    text,
      shop_name: shopName.value || 'My Café',
      aesthetic: aesthetic.value,
      colors:    ['#C8A27C', '#5A3E2B'],
    }
    if (photoBase64.value) {
      body.reference_image_base64 = photoBase64.value
      body.reference_image_mime   = photoMime.value
    }
    photoBase64.value = ''

    const res = await api.post('/generate/guest', body)
    const d   = res.data

    messages.value.pop()
    messages.value.push({
      role:       'assistant',
      id:         d.generation_id,
      image_url:  d.image_data_url,
      caption_en: d.en_caption,
      caption_km: d.kh_caption,
      hashtags:   d.hashtags || '',
    })
  } catch (e) {
    messages.value.pop()
    messages.value.push({ role: 'error', text: e.response?.data?.detail || 'Generation failed. Please try again.' })
  } finally {
    clearInterval(stepInterval)
    loading.value = false
    scrollToBottom()
  }
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    showToast('Copied to clipboard')
  } catch { showToast('Could not copy') }
}

function downloadImage(url, id) {
  const a = document.createElement('a')
  a.href     = url
  a.download = `postnow-poster-${id || Date.now()}.png`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function showToast(msg) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 3000)
}
</script>
