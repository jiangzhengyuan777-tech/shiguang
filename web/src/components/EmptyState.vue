<template>
  <div class="flex flex-col items-center justify-center px-6 py-16 text-center">
    <!-- 暖色线稿插画 -->
    <svg viewBox="0 0 120 120" class="mb-5 h-24 w-24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="60" cy="60" r="46" fill="#FFF1ED" />
      <circle cx="60" cy="60" r="46" stroke="#FFD9CF" stroke-width="1.5" stroke-dasharray="4 6" />
      <rect x="38" y="42" width="44" height="34" rx="4" fill="#FFFFFF" stroke="#FF6B4A" stroke-width="2" />
      <path d="M46 54h28M46 62h20M46 70h12" stroke="#FFB84D" stroke-width="2" stroke-linecap="round" />
      <circle cx="86" cy="38" r="7" fill="#FF6B4A" opacity="0.9" />
      <path d="M83.5 38l2 2 3.5-3.6" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
    </svg>

    <div class="font-serif text-base font-semibold text-ink">{{ title }}</div>
    <p v-if="desc" class="mt-1.5 max-w-xs text-xs leading-relaxed text-muted">{{ desc }}</p>

    <button v-if="action" class="btn-primary mt-5" @click="$emit('action')">
      {{ action }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  desc?: string
  action?: string
}>()
defineEmits<{ action: [] }>()
</script>
