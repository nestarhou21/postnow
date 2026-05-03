<template>
  <div class="min-h-screen bg-surface flex flex-col font-body text-on-surface overflow-x-hidden">
    
    <!-- Top Navbar (Zone 1) -->
    <header class="px-6 py-4 border-b border-surface-container-high bg-surface-lowest/80 backdrop-blur-md sticky top-0 z-50 flex justify-between items-center transition-all duration-300">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary text-[28px]" style="font-variation-settings: 'FILL' 1;">coffee</span>
        <span class="text-xl font-extrabold text-primary font-headline tracking-tight">POSTNOW</span>
      </div>
      <div class="flex items-center gap-4">
        <router-link to="/login" class="text-sm font-bold text-on-surface hover:text-primary transition-colors">Sign In</router-link>
        <router-link to="/login?tab=register" class="px-5 py-2.5 rounded-full bg-primary text-on-primary text-sm font-bold shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all">
          Try Free
        </router-link>
      </div>
    </header>

    <!-- Hero Section -->
    <section class="relative pt-20 pb-32 px-6 flex flex-col items-center justify-center overflow-hidden">
      <!-- Background Glows -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[100px] pointer-events-none -z-10"></div>
      
      <div class="max-w-4xl mx-auto text-center z-10">
        <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface-container border border-surface-container-highest mb-8 animate-[fadeUp_0.5s_ease_both]">
          <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
          <span class="text-xs font-bold text-on-surface tracking-wide uppercase">The Poster Generator for Coffee Shops</span>
        </div>
        
        <h1 class="font-headline text-5xl md:text-7xl font-black text-on-surface tracking-tight leading-[1.1] mb-6 animate-[fadeUp_0.7s_ease_both]">
          Brew stunning social media posts in <span class="text-primary">seconds.</span>
        </h1>
        
        <p class="text-lg md:text-xl text-on-surface-variant font-medium max-w-2xl mx-auto mb-10 animate-[fadeUp_0.9s_ease_both]">
          Stop struggling with design tools. Just tell Postnow what you're promoting, and our AI writes the caption and designs a premium, layout-perfect poster for your shop.
        </p>
        
        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 animate-[fadeUp_1.1s_ease_both]">
          <router-link to="/login?tab=register" class="w-full sm:w-auto px-8 py-4 rounded-full bg-primary hover:bg-[#8B6B4A] text-white font-bold text-lg shadow-[0_8px_20px_rgba(119,88,56,0.2)] hover:shadow-[0_12px_28px_rgba(119,88,56,0.3)] hover:-translate-y-1 transition-all flex items-center justify-center gap-2">
            Start Brewing Free
            <span class="material-symbols-outlined text-[20px]">arrow_forward</span>
          </router-link>
          <p class="text-xs font-bold text-on-surface-variant uppercase tracking-widest mt-2 sm:mt-0 sm:ml-4">No credit card required</p>
        </div>
      </div>
      
      <!-- Mascot / Hero Area -->
      <div class="mt-20 relative w-full max-w-5xl mx-auto animate-[fadeUp_1.3s_ease_both]">
        <img src="/Asset.png" alt="Postnow Mascot" class="w-64 h-auto mx-auto relative z-20 animate-[float_4s_ease-in-out_infinite_alternate]" />
        
        <!-- Decorative 'Float' Elements -->
        <div class="absolute top-1/4 left-10 md:left-32 bg-surface-container-lowest p-4 rounded-2xl shadow-xl border border-surface-container rotate-[-6deg] animate-[float_4s_ease-in-out_infinite_alternate]">
          <span class="text-3xl">☕️</span>
          <p class="text-xs font-bold mt-2">New Bean Arrival</p>
        </div>
        <div class="absolute bottom-1/4 right-10 md:right-32 bg-surface-container-lowest p-4 rounded-2xl shadow-xl border border-surface-container rotate-[8deg] animate-[float_5s_ease-in-out_infinite_alternate_reverse]">
          <span class="text-3xl">🥐</span>
          <p class="text-xs font-bold mt-2">Morning Combo</p>
        </div>
      </div>
    </section>

    <!-- How it Works Section -->
    <section class="py-24 bg-surface-container-lowest border-y border-surface-container px-6 relative z-10">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-16">
          <h2 class="font-headline text-3xl md:text-5xl font-black mb-4">How it works</h2>
          <p class="text-on-surface-variant font-medium">Four simple steps from idea to Instagram.</p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div v-for="(step, i) in steps" :key="i" class="bg-surface p-8 rounded-3xl border border-surface-container-high shadow-sm relative group hover:shadow-md hover:-translate-y-1 transition-all">
            <div class="w-12 h-12 rounded-full bg-primary-container/20 text-primary flex items-center justify-center font-black text-xl mb-6 shadow-inner group-hover:scale-110 transition-transform">
              {{ i + 1 }}
            </div>
            <h3 class="font-bold text-lg text-on-surface mb-2">{{ step.title }}</h3>
            <p class="text-sm text-on-surface-variant">{{ step.desc }}</p>
            
            <!-- Connection Line (Desktop) -->
            <div v-if="i < 3" class="hidden md:block absolute top-14 left-full w-full h-[2px] bg-gradient-to-r from-surface-container-highest to-transparent -translate-x-8 z-[-1]"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- Poster Gallery -->
    <section class="py-24 px-6">
      <div class="max-w-7xl mx-auto">
        <div class="text-center mb-16">
          <h2 class="font-headline text-4xl mb-4 font-black">Crafted for Coffee</h2>
          <p class="text-on-surface-variant font-medium">Real examples generated completely by Postnow AI.</p>
        </div>
        
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
          <div v-for="(img, i) in gallery" :key="i" class="aspect-[4/5] rounded-3xl overflow-hidden shadow-sm border border-surface-container group">
             <img :src="img.src" :alt="img.alt" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
          </div>
        </div>
      </div>
    </section>

    <!-- Final CTA -->
    <section class="py-24 px-6 bg-navy-black text-white relative overflow-hidden">
      <!-- Decorative background -->
      <div class="absolute inset-0 opacity-10" style="background-image: radial-gradient(#ffffff 1px, transparent 1px); background-size: 20px 20px;"></div>
      <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-3xl h-[400px] bg-primary rounded-full blur-[150px] opacity-20 pointer-events-none"></div>

      <div class="max-w-3xl mx-auto text-center relative z-10">
        <h2 class="font-headline text-4xl md:text-5xl font-black mb-6">Ready to elevate your shop's marketing?</h2>
        <p class="text-white/70 font-medium mb-10 text-lg">Join hundreds of cafes saving hours every week while looking better than ever on social media.</p>
        <router-link to="/login?tab=register" class="inline-flex px-10 py-5 rounded-full bg-white text-navy-black font-black text-lg shadow-[0_0_30px_rgba(255,255,255,0.2)] hover:shadow-[0_0_40px_rgba(255,255,255,0.4)] hover:scale-105 transition-all">
          Create Your Free Account
        </router-link>
      </div>
    </section>

    <!-- Footer -->
    <footer class="py-12 border-t border-surface-container text-center bg-surface-lowest">
      <div class="flex items-center justify-center gap-2 mb-4">
        <span class="material-symbols-outlined text-primary text-[24px]" style="font-variation-settings: 'FILL' 1;">coffee</span>
        <span class="text-lg font-extrabold text-primary font-headline tracking-tight">POSTNOW</span>
      </div>
      <p class="text-sm text-on-surface-variant font-medium">&copy; 2026 Postnow AI. Designed for Specialty Coffee.</p>
    </footer>

  </div>
</template>

<script setup>
const steps = [
  { title: "Define the Vibe", desc: "Tell us about your shop's unique aesthetic and upload your logo once." },
  { title: "Write a Prompt", desc: "Simply type what you want to promote. 'Half off lattes until 2PM today!'" },
  { title: "AI Magic", desc: "Our engine crafts a stunning, layout-perfect poster with matching captions." },
  { title: "Post & Pour", desc: "Download your high-res image, copy the bilingual captions, and get back to brewing." }
]

const gallery = [
  { alt: "Promo 1", src: "https://images.unsplash.com/photo-1497935586351-b67a49e012bf?w=500&q=80" },
  { alt: "Promo 2", src: "https://images.unsplash.com/photo-1559525839-b184a4d698c7?w=500&q=80" },
  { alt: "Promo 3", src: "https://images.unsplash.com/photo-1498804103079-a6351b050096?w=500&q=80" },
  { alt: "Promo 4", src: "https://images.unsplash.com/photo-1600093463592-8e36ae95ef56?w=500&q=80" }
]
</script>

<style scoped>
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(30px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes float {
  from { transform: translateY(0px) rotate(var(--tw-rotate)); }
  to   { transform: translateY(-15px) rotate(calc(var(--tw-rotate) + 2deg)); }
}
.bg-navy-black {
  background-color: #1a1a1a;
}
</style>
