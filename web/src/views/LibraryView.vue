<template>
  <div class="mx-auto max-w-5xl px-10 py-12">
    <div class="flex items-end justify-between">
      <div>
        <h1 class="font-serif text-[1.9rem] font-bold text-ink">文章库</h1>
        <p class="mt-2 text-sm text-muted">共 {{ total }} 篇 · 点开可以分发到公众号或小红书</p>
      </div>
      <router-link to="/create" class="btn-primary">写一篇</router-link>
    </div>

    <!-- 筛选 -->
    <div class="mt-8 flex flex-wrap items-center gap-2">
      <input v-model="keyword" class="input max-w-xs" placeholder="搜索标题或选题" />
      <button
        v-for="f in filters"
        :key="f.value"
        class="rounded-full border px-3.5 py-1.5 text-xs transition-colors"
        :class="
          status === f.value
            ? 'border-coral bg-coral-soft font-medium text-coral'
            : 'border-line text-muted hover:border-coral/50'
        "
        @click="status = f.value"
      >
        {{ f.label }}
      </button>
    </div>

    <!-- 列表 -->
    <div v-if="loading" class="mt-8"><SkeletonList :rows="4" /></div>
    <div v-else-if="!filtered.length" class="card mt-10">
      <EmptyState
        :title="articles.length ? '没有符合条件的文章' : '文章库还是空的'"
        :desc="articles.length ? '换个关键词或筛选条件试试' : '去写一篇，写完会自动出现在这里'"
        :action="articles.length ? '' : '开始创作'"
        @action="router.push('/create')"
      />
    </div>
    <div v-else class="mt-8 space-y-3">
      <router-link
        v-for="(a, i) in filtered"
        :key="a.taskId"
        :to="`/article/${a.taskId}`"
        class="card group flex animate-fade-up items-center gap-5 p-5 transition-all hover:-translate-y-0.5 hover:shadow-lift"
        :style="{ animationDelay: `${i * 55}ms` }"
      >
        <div class="min-w-0 flex-1">
          <div class="mb-2 flex items-center gap-2">
            <span class="tag" :class="statusCls(a.status)">{{ statusText(a.status) }}</span>
            <span class="text-[11px] text-muted">{{ (a.createTime || '').replace('T', ' ').slice(0, 16) }}</span>
          </div>
          <h3 class="truncate font-serif text-[16px] font-semibold text-ink group-hover:text-coral">
            {{ a.mainTitle || a.topic }}
          </h3>
          <p class="mt-1 truncate text-xs text-muted">{{ a.topic }}</p>
        </div>
        <span class="shrink-0 text-muted transition-transform group-hover:translate-x-1">→</span>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { articleApi } from '@/api/article'
import EmptyState from '@/components/EmptyState.vue'
import SkeletonList from '@/components/SkeletonList.vue'

const router = useRouter()

const loading = ref(true)
const articles = ref<any[]>([])
const total = ref(0)
const keyword = ref('')
const status = ref('')

const filters = [
  { label: '全部', value: '' },
  { label: '已完成', value: 'COMPLETED' },
  { label: '生成中', value: 'PROCESSING' },
  { label: '失败', value: 'FAILED' },
]

const filtered = computed(() => {
  let list = articles.value
  if (status.value) list = list.filter((a) => a.status === status.value)
  if (keyword.value.trim()) {
    const k = keyword.value.trim().toLowerCase()
    list = list.filter(
      (a) =>
        (a.mainTitle || '').toLowerCase().includes(k) || (a.topic || '').toLowerCase().includes(k),
    )
  }
  return list
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

onMounted(async () => {
  try {
    const res = await articleApi.list({ pageNum: 1, pageSize: 100 })
    articles.value = res.data?.data?.records || []
    total.value = res.data?.data?.total ?? res.data?.data?.totalRow ?? articles.value.length
  } finally {
    loading.value = false
  }
})
</script>
