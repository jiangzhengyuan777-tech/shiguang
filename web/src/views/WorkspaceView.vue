<template>
  <div class="mx-auto max-w-5xl px-10 py-12">
    <!-- 问候 -->
    <div class="mb-10">
      <p class="text-sm text-muted">{{ today }}</p>
      <h1 class="mt-2 font-serif text-[2rem] font-bold leading-snug text-ink">
        {{ greeting }}，{{ auth.user?.userName || '创作者' }}👋
      </h1>
      <p class="mt-2 text-sm text-muted">今天想写点什么？给个题目，或者贴一篇热点。</p>
    </div>

    <!-- 创作入口 -->
    <div class="card p-7">
      <textarea
        v-model="quickTopic"
        rows="3"
        class="w-full resize-none border-0 bg-transparent text-lg leading-relaxed text-ink placeholder:text-muted/50 focus:outline-none"
        placeholder="例如：2026 年 AI 如何改变普通人的工作方式"
        @keydown.enter.ctrl.prevent="goCreate"
      ></textarea>
      <div class="mt-4 flex items-center justify-between border-t border-line pt-4">
        <div class="flex min-w-0 flex-wrap items-center gap-2">
          <button
            v-for="t in hotTopics"
            :key="t"
            class="rounded-full border border-line px-3 py-1 text-xs text-muted transition-colors hover:border-coral hover:text-coral"
            @click="pickTopic(t)"
          >
            {{ t }}
          </button>
          <button
            class="flex items-center gap-1 rounded-full border border-dashed border-coral/40 px-3 py-1 text-xs text-coral transition-colors hover:bg-coral-soft"
            :disabled="shuffling"
            @click="shuffleTopics"
          >
            <span>{{ shuffling ? '⏳' : '🎲' }}</span>
            {{ shuffling ? '想选题中…' : '换一批灵感' }}
          </button>
        </div>
        <button class="btn-primary shrink-0" @click="goCreate">
          开始创作
          <span class="text-xs opacity-80">⌘↵</span>
        </button>
      </div>
    </div>

    <!-- 最近文章 -->
    <div class="mt-12">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="font-serif text-lg font-bold text-ink">最近创作</h2>
        <router-link to="/library" class="text-xs text-muted hover:text-coral">查看全部 →</router-link>
      </div>

      <div v-if="loading"><SkeletonList :rows="2" /></div>
      <div v-else-if="!recent.length" class="card">
        <EmptyState
          title="还没有作品"
          desc="上面那个输入框就是起点，写你的第一篇"
          action="马上开始"
          @action="router.push('/create')"
        />
      </div>
      <div v-else class="grid gap-4 sm:grid-cols-2">
        <router-link
          v-for="(a, i) in recent"
          :key="a.taskId"
          :to="`/article/${a.taskId}`"
          class="card group animate-fade-up p-5 transition-all hover:-translate-y-0.5 hover:shadow-lift"
          :style="{ animationDelay: `${i * 70}ms` }"
        >
          <div class="mb-3 flex items-center gap-2">
            <span class="tag" :class="statusCls(a.status)">{{ statusText(a.status) }}</span>
            <span class="text-[11px] text-muted">{{ (a.createTime || '').slice(0, 10) }}</span>
          </div>
          <h3 class="line-clamp-2 font-serif text-[15px] font-semibold leading-relaxed text-ink group-hover:text-coral">
            {{ a.mainTitle || a.topic }}
          </h3>
          <p class="mt-2 line-clamp-1 text-xs text-muted">{{ a.topic }}</p>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { articleApi } from '@/api/article'
import EmptyState from '@/components/EmptyState.vue'
import SkeletonList from '@/components/SkeletonList.vue'

const auth = useAuthStore()
const router = useRouter()

const quickTopic = ref('')
const loading = ref(true)
const recent = ref<any[]>([])

const hotTopics = ref<string[]>([
  '2026年AI如何改变职场',
  '普通人如何用AI提升效率',
  '为什么年轻人开始反向消费',
  '远程办公的利与弊',
])
const shuffling = ref(false)

/** 换一批：让 AI 按随机平台调性推选题，给灵感区注入活力 */
const shuffleTopics = async () => {
  shuffling.value = true
  try {
    const platforms = ['marketing', 'xiaohongshu', 'wechat_official']
    const style = platforms[Math.floor(Math.random() * platforms.length)]
    const res = await articleApi.suggestTopics(style, 4)
    if (res.data.code === 0 && res.data.data?.length) {
      hotTopics.value = res.data.data.slice(0, 4)
    }
  } catch {
    // 静默失败，保留原有选题
  } finally {
    shuffling.value = false
  }
}

const pickTopic = (t: string) => {
  quickTopic.value = t
}

const today = computed(() =>
  new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }),
)

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const statusText = (s: string) =>
  ({ COMPLETED: '已完成', PROCESSING: '生成中', PENDING: '等待中', FAILED: '失败' } as any)[s] || s

const statusCls = (s: string) =>
  ({
    COMPLETED: 'bg-sage/12 text-sage',
    PROCESSING: 'bg-amber-light text-[#B7791F]',
    PENDING: 'bg-cream text-muted',
    FAILED: 'bg-red-50 text-red-500',
  } as any)[s] || 'bg-cream text-muted'

const goCreate = () => {
  router.push({ path: '/create', query: quickTopic.value ? { topic: quickTopic.value } : {} })
}

onMounted(async () => {
  try {
    const res = await articleApi.list({ pageNum: 1, pageSize: 4 })
    recent.value = res.data?.data?.records || []
  } catch {
    recent.value = []
  } finally {
    loading.value = false
  }
})
</script>
