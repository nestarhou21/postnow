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
            <p class="text-sm text-[#aaa] leading-relaxed">
              I help Cambodian café owners create professional promotional posters and bilingual captions.
              Describe your promotion, ask me a marketing question, or upload a drink photo to get started.
            </p>
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

          <!-- Bot text reply (greeting / Q&A) -->
          <div v-else-if="msg.role === 'bot'" class="flex gap-3 items-start">
            <img :src="botAvatar" class="w-8 h-8 rounded-full object-cover shrink-0 mt-0.5" />
            <div class="bg-[#1e1c18] border border-white/6 rounded-2xl rounded-tl-sm px-5 py-4 max-w-lg">
              <p class="text-sm text-[#ccc] leading-relaxed whitespace-pre-line" v-html="msg.html"></p>
            </div>
          </div>

          <!-- Loading -->
          <div v-else-if="msg.role === 'loading'" class="flex gap-3 items-start">
            <img :src="botAvatar" class="w-8 h-8 rounded-full object-cover shrink-0 mt-0.5" />
            <div class="bg-[#1e1c18] border border-white/6 rounded-2xl rounded-tl-sm px-5 py-4">
              <div class="flex items-center gap-3">
                <div class="flex gap-1 shrink-0">
                  <span class="w-1.5 h-1.5 bg-[#C8A27C] rounded-full animate-bounce [animation-delay:0ms]"></span>
                  <span class="w-1.5 h-1.5 bg-[#C8A27C] rounded-full animate-bounce [animation-delay:150ms]"></span>
                  <span class="w-1.5 h-1.5 bg-[#C8A27C] rounded-full animate-bounce [animation-delay:300ms]"></span>
                </div>
                <span class="text-sm text-[#888]">{{ msg.text }}</span>
              </div>
            </div>
          </div>

          <!-- Poster result -->
          <div v-else-if="msg.role === 'assistant'" class="flex gap-3 items-start">
            <img :src="botAvatar" class="w-8 h-8 rounded-full object-cover shrink-0 mt-0.5" />
            <div class="bg-[#1e1c18] border border-white/6 rounded-2xl rounded-tl-sm px-5 py-5 max-w-xl w-full flex flex-col gap-4">
              <div>
                <p class="text-[10px] text-[#555] uppercase tracking-widest mb-2.5 font-bold">Your Poster</p>
                <img :src="msg.image_url" class="rounded-xl w-full border border-white/8 shadow-2xl" />
              </div>
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
              <div class="flex flex-wrap gap-1.5">
                <span v-for="tag in msg.hashtags.split(' ').filter(t => t)" :key="tag"
                  class="text-[10px] px-2.5 py-1 rounded-full bg-[#C8A27C]/10 text-[#C8A27C] border border-[#C8A27C]/20 font-medium">
                  {{ tag }}
                </span>
              </div>
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

    <!-- Input -->
    <div class="shrink-0 px-4 pb-5 pt-3 border-t border-white/6">
      <div class="max-w-2xl mx-auto flex flex-col gap-2.5">

        <!-- Image preview -->
        <div v-if="photoPreview" class="bg-[#1e1c18] border border-white/8 rounded-2xl p-3 flex items-center gap-3">
          <img :src="photoPreview" class="h-20 w-20 object-cover rounded-xl border border-white/10 shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="text-xs text-[#aaa] font-medium">Photo attached</p>
            <p class="text-[10px] text-[#555] mt-0.5">Will be used as reference for the drink</p>
          </div>
          <button @click="removePhoto" class="text-[#555] hover:text-red-400 transition-colors shrink-0">
            <span class="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <!-- Input bar -->
        <div :class="['flex items-end gap-2 bg-[#1e1c18] border rounded-2xl px-4 py-3 transition-all', inputFocused ? 'border-[#C8A27C]/40' : 'border-white/8']">
          <button @click="fileInput?.click()" class="text-[#555] hover:text-[#C8A27C] transition-colors mb-0.5 shrink-0" title="Attach drink photo">
            <span class="material-symbols-outlined text-[22px]">attach_file</span>
          </button>
          <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFileChange" />
          <textarea
            ref="promptEl"
            v-model="prompt"
            :disabled="loading"
            placeholder="Describe your promotion, or ask a marketing question…"
            rows="1"
            @focus="inputFocused = true"
            @blur="inputFocused = false"
            @input="autoGrow"
            @keydown.enter.exact.prevent="send"
            @keydown.shift.enter="null"
            class="flex-1 bg-transparent outline-none resize-none text-sm text-[#ece8e3] placeholder:text-[#444] max-h-32 leading-relaxed disabled:opacity-40"
          ></textarea>
          <button @click="send" :disabled="!prompt.trim() || loading"
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

// ── Shop name extraction from chat ───────────────────────────────────────────

const SHOP_NAME_PATTERNS = [
  /my (?:shop|café|cafe|coffee shop|store|restaurant) (?:is called|is named|is|called|named) ["']?([A-Za-z0-9 &'-]{2,30})["']?/i,
  /(?:shop|café|cafe|coffee shop) name[:\s]+["']?([A-Za-z0-9 &'-]{2,30})["']?/i,
  /i (?:own|run|have|manage) ["']?([A-Za-z0-9 &'-]{2,25})\s*(?:café|cafe|coffee|shop|bar)/i,
  /["']([A-Za-z0-9 &'-]{2,25})\s*(?:café|cafe|coffee|shop|bar)["']/i,
  /(?:called|named|it's|its)\s+["']?([A-Za-z0-9 &'-]{2,25})\s*(?:café|cafe|coffee|shop)?["']?/i,
]

function tryExtractShopName(text) {
  for (const pattern of SHOP_NAME_PATTERNS) {
    const m = text.match(pattern)
    if (m && m[1]) {
      const name = m[1].trim()
      if (name.length >= 2) return name
    }
  }
  return null
}

// ── Intent detection ──────────────────────────────────────────────────────────

const GREETING_TRIGGERS = [
  'hi', 'hello', 'hey', 'hiya', 'sup', "what's up", 'good morning',
  'good afternoon', 'good evening', 'how are you', 'who are you',
  'what can you do', 'what do you do', 'help', 'start',
]

const QUESTION_TRIGGERS = [
  'hashtag', 'caption', 'best time', 'when to post', 'how to market',
  'social media', 'instagram', 'facebook', 'engagement', 'followers',
  'how to grow', 'tips', 'advice', 'photography', 'photo tips',
  'promotion idea', 'how to write', 'what makes a good', 'grow my',
  'increase', 'strategy', 'content',
]

function detectIntent(text) {
  const t = text.toLowerCase().trim()
  if (GREETING_TRIGGERS.some(p => t === p || t.startsWith(p + ' ') || t.endsWith(' ' + p))) return 'greeting'
  if (QUESTION_TRIGGERS.some(p => t.includes(p))) return 'question'
  return 'generate'
}

// ── Greeting responses ────────────────────────────────────────────────────────

const GREETINGS = [
  "Hey! I'm POSTNOW — your AI marketing assistant for Cambodian café promotions.\n\nTell me your promotion (e.g. <em>\"Buy 1 Get 1 Latte this weekend\"</em>) and I'll generate a professional poster with bilingual captions in English and Khmer. You can also upload a photo of your drink for a more personalised result. ☕",
  "Hello! I'm POSTNOW, built to help café owners in Cambodia create beautiful promotional content.\n\nJust describe your offer and I'll handle the poster design and captions. What promotion would you like to advertise today?",
  "Hi there! Great to meet you. I can generate branded promotional posters and bilingual captions for your café.\n\nYou can also ask me marketing questions — like the best hashtags to use or when to post on Instagram. What can I help with?",
  "Hey! I'm POSTNOW. I turn your promotion ideas into professional café posters and social media captions — in under a minute.\n\nType your promotion below, or ask me anything about café marketing. 🫰",
  "Hello! I help café owners stand out on social media with AI-generated posters and captions.\n\nDescribe your promotion, upload a drink photo, or ask me a marketing question to get started.",
]
let greetingIndex = 0

// ── Coffee marketing Q&A ──────────────────────────────────────────────────────

const COFFEE_QA = [
  {
    keywords: ['hashtag'],
    answer: `<strong>Recommended hashtags for Cambodian cafés:</strong>

🇺🇸 English: #PhnomPenhCafe #CambodiaCoffee #CoffeeLovers #CaféLife #LatteArt #BubbleTea #CambodiaFood
🇰🇭 Khmer: #កាហ្វេភ្នំពេញ #កាហ្វេខ្មែរ #ភ្នំពេញ

Aim for <strong>8–12 hashtags</strong> per post. Mix popular ones (#CoffeeLovers) with local niche ones (#PhnomPenhCafe) for the best reach.`,
  },
  {
    keywords: ['best time', 'when to post', 'posting time'],
    answer: `<strong>Best times to post for Cambodian café audiences:</strong>

⏰ <strong>7–9 AM</strong> — Morning coffee crowd checking their phones
⏰ <strong>12–2 PM</strong> — Lunch break scrollers
⏰ <strong>4–7 PM</strong> — After-work peak — highest engagement
⏰ <strong>8–10 PM</strong> — Evening casual browsing

<strong>Friday and Saturday evenings</strong> get the highest engagement for promotional posts.`,
  },
  {
    keywords: ['caption', 'how to write', 'copy'],
    answer: `<strong>A great café caption has 3 parts:</strong>

1. <strong>Hook</strong> — Stop the scroll. E.g. <em>"Your Monday just got better ☕"</em>
2. <strong>Offer</strong> — State the promotion clearly and briefly
3. <strong>Call to action</strong> — <em>"Come visit us today"</em> or <em>"Tag a friend you'd bring"</em>

Keep the <strong>first line under 125 characters</strong> — everything after is hidden behind "more". Make that first line count.`,
  },
  {
    keywords: ['grow', 'followers', 'engagement', 'instagram', 'facebook', 'social media', 'strategy', 'content', 'increase'],
    answer: `<strong>Top tips to grow your café's social media:</strong>

📸 <strong>Post 4–5 times per week</strong> — consistency beats perfection
🎬 <strong>Show the drink being made</strong> — process videos get 3× more views
🤝 <strong>Reply to every comment</strong> in the first hour — algorithm rewards this
📍 <strong>Always tag your location</strong> — local discovery is huge
🎁 <strong>Giveaways work</strong> — "Tag 2 friends to win a free drink" grows fast
🕐 <strong>Use Stories daily</strong> — keeps you at the top of followers' feeds`,
  },
  {
    keywords: ['promotion idea', 'offer', 'deal', 'discount idea'],
    answer: `<strong>Proven promotion ideas for Cambodian cafés:</strong>

☕ <strong>Buy 1 Get 1</strong> — most shared promotion type
🎂 <strong>Birthday discount</strong> — 50% off on your birthday month
⏰ <strong>Happy hour</strong> — e.g. 2–5 PM daily special price
📱 <strong>Social share deal</strong> — discount for showing the post at the counter
👥 <strong>Bring a friend</strong> — both customers get a free upgrade
🗓️ <strong>Weekly special</strong> — new drink every Monday creates weekly anticipation`,
  },
  {
    keywords: ['photo', 'picture', 'shoot', 'photography', 'photo tips'],
    answer: `<strong>Quick drink photography tips:</strong>

💡 <strong>Natural light always wins</strong> — shoot near a window, never use the flash
🎨 <strong>Clean background</strong> — marble, wood, or plain white surface
📐 <strong>Offset the drink slightly</strong> — don't centre it perfectly, it looks more natural
💧 <strong>Condensation is your friend</strong> — shoot cold drinks immediately after making
🌿 <strong>One prop maximum</strong> — a flower, leaf, or ingredient makes it look styled
📱 <strong>Portrait mode</strong> — creates the professional bokeh blur behind the drink`,
  },
]

function findQAAnswer(text) {
  const t = text.toLowerCase()
  for (const qa of COFFEE_QA) {
    if (qa.keywords.some(k => t.includes(k))) return qa.answer
  }
  return `Great question! Here are some quick café marketing tips:\n\n☕ Post consistently (4–5× per week)\n📍 Always tag your location\n🎁 Run a simple giveaway to grow fast\n⏰ Best posting times: 7–9 AM, 4–7 PM, and Friday evenings\n\nFeel free to ask me something more specific — or tell me your promotion and I'll generate a poster!`
}

// ── Simple markdown-ish formatter ─────────────────────────────────────────────

function fmt(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
}

// ── Main send handler ─────────────────────────────────────────────────────────

function send() {
  if (!prompt.value.trim() || loading.value) return

  const text  = prompt.value.trim()
  const photo = photoPreview.value

  // Always try to extract shop name from what the user typed
  const detected = tryExtractShopName(text)
  if (detected) {
    shopName.value = detected
    showToast(`Shop name set to "${detected}"`)
  }

  // If a photo is attached, always generate — user is uploading a drink
  const intent = photo ? 'generate' : detectIntent(text)

  messages.value.push({ role: 'user', text, photo })
  prompt.value       = ''
  photoPreview.value = ''
  if (promptEl.value) promptEl.value.style.height = 'auto'
  scrollToBottom()

  if (intent === 'greeting') {
    const reply = GREETINGS[greetingIndex % GREETINGS.length]
    greetingIndex++
    setTimeout(() => {
      messages.value.push({ role: 'bot', html: fmt(reply) })
      scrollToBottom()
    }, 400)
    return
  }

  if (intent === 'question') {
    const answer = findQAAnswer(text)
    setTimeout(() => {
      messages.value.push({ role: 'bot', html: answer })
      scrollToBottom()
    }, 400)
    return
  }

  // Generate poster
  generatePoster(text)
}

// ── Poster generation ─────────────────────────────────────────────────────────

const LOADING_STEPS = [
  'Analyzing your promotion…',
  'Crafting a creative concept…',
  'Generating your poster with Gemini…',
  'Writing bilingual captions…',
  'Almost done…',
]

async function generatePoster(text) {
  loading.value = true

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

// ── Helpers ───────────────────────────────────────────────────────────────────

function autoGrow(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

function scrollToBottom() {
  nextTick(() => { if (chatEl.value) chatEl.value.scrollTop = chatEl.value.scrollHeight })
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
