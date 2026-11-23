<template>
  <div class="flex min-h-screen">
    <!-- 侧边栏 -->
    <aside class="fixed inset-y-0 left-0 z-20 flex w-[236px] flex-col border-r border-line bg-paper/80 backdrop-blur">
      <div class="px-6 pb-6 pt-7">
        <router-link to="/" class="flex items-center gap-2.5">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-coral to-amber text-lg text-white shadow-soft">
            ✎
          </span>
          <div>
            <div class="font-serif text-lg font-bold tracking-wide text-ink">拾光</div>
            <div class="text-[11px] text-muted">一句话，写成一篇</div>
          </div>
        </router-link>
      </div>

      <nav class="flex-1 space-y-1 px-3">
        <router-link
          v-for="item in navs"
          :key="item.to"
          :to="item.to"
          class="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors"
          :class="
            isActive(item.to)
              ? 'bg-coral-soft font-semibold text-coral'
              : 'text-ink/70 hover:bg-cream hover:text-ink'
          "
        >
          <span class="text-base">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="border-t border-line px-3 py-4">
        <div class="flex items-center gap-3 rounded-xl px-3 py-2">
          <div class="flex h-9 w-9 items-center justify-center rounded-full bg-coral-soft text-sm font-bold text-coral">
            {{ (auth.user?.userName || 'U').slice(0, 1) }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-medium text-ink">{{ auth.user?.userName || '用户' }}</div>
            <div class="truncate text-[11px] text-muted">
              {{ auth.isAdmin ? '管理员 · 不限次' : auth.isVip ? '会员 · 不限次' : `剩余 ${auth.quota} 次` }}
            </div>
          </div>
          <button class="text-xs text-muted hover:text-coral" title="退出登录" @click="auth.logout()">
            退出
          </button>
        </div>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="ml-[236px] flex-1">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()

const navs = [
  { to: '/', label: '工作台', icon: '◈' },
  { to: '/create', label: '开始创作', icon: '✎' },
  { to: '/library', label: '文章库', icon: '☰' },
  { to: '/vip', label: '会员', icon: '♛' },
]

const isActive = (to: string) =>
  computed(() => (to === '/' ? route.path === '/' : route.path.startsWith(to))).value
</script>
