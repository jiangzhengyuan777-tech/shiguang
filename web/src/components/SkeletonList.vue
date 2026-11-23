<template>
  <div class="space-y-3">
    <div
      v-for="i in rows"
      :key="i"
      class="card flex items-center gap-5 p-5"
      :style="{ animationDelay: `${i * 60}ms` }"
    >
      <div class="min-w-0 flex-1">
        <div class="mb-3 flex items-center gap-2">
          <div class="h-4 w-14 animate-pulse rounded bg-line"></div>
          <div class="h-3 w-24 animate-pulse rounded bg-line/70"></div>
        </div>
        <div class="h-4 w-3/5 animate-pulse rounded bg-line"></div>
        <div class="mt-2 h-3 w-2/5 animate-pulse rounded bg-line/60"></div>
      </div>
      <div class="h-3 w-6 animate-pulse rounded bg-line/60"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ rows?: number }>(), { rows: 4 })
</script>
