<template>
  <div class="mx-auto max-w-4xl px-10 py-10">
    <!-- 头部操作 -->
    <div class="mb-6 flex items-center justify-between">
      <button class="text-sm text-muted transition-colors hover:text-coral" @click="router.back()">
        ← 返回
      </button>
      <div class="flex gap-2">
        <button v-if="article?.status === 'FAILED'" class="btn-ghost" @click="retryCreate">
          ↻ 重新创作
        </button>
        <button
          class="btn-soft"
          :disabled="!article || article.status !== 'COMPLETED'"
          @click="openDistribute"
        >
          分发到平台
        </button>
      </div>
    </div>

    <div v-if="loading" class="py-20 text-center text-sm text-muted">加载中…</div>

    <article v-else-if="article" class="card animate-fade-up px-10 py-12">
      <header class="border-b border-line pb-8">
        <div class="mb-4 flex items-center gap-2">
          <span class="tag" :class="statusCls(article.status)">{{ statusText(article.status) }}</span>
          <span class="text-xs text-muted">{{ (article.createTime || '').replace('T', ' ').slice(0, 16) }}</span>
        </div>
        <h1 class="font-serif text-[2rem] font-bold leading-snug text-ink">
          {{ article.mainTitle || article.topic }}
        </h1>
        <p v-if="article.subTitle" class="mt-3 text-base text-muted">{{ article.subTitle }}</p>
      </header>

      <div v-if="article.status === 'FAILED'" class="mt-8 rounded-xl bg-red-50 p-5 text-sm text-red-600">
        生成失败：{{ article.errorMessage || '未知原因' }}
      </div>

      <div
        v-else
        class="prose-shiguang mt-10"
        v-html="renderedBody"
      ></div>
    </article>

    <!-- 分发弹层 -->
    <div
      v-if="showDistribute"
      class="animate-fade-in fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-6 backdrop-blur-sm"
    >
      <div class="animate-scale-in flex max-h-[86vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-paper shadow-lift">
        <div class="flex items-center justify-between border-b border-line px-6 py-4">
          <div class="font-serif text-lg font-bold text-ink">分发到平台</div>
          <button class="text-muted hover:text-coral" @click="showDistribute = false">✕</button>
        </div>

        <div class="flex gap-1 border-b border-line px-6">
          <button
            v-for="t in [{ k: 'wechat', l: '公众号' }, { k: 'xhs', l: '小红书' }]"
            :key="t.k"
            class="relative px-4 py-3 text-sm transition-colors"
            :class="tab === t.k ? 'font-semibold text-coral' : 'text-muted hover:text-ink'"
            @click="switchTab(t.k as 'wechat' | 'xhs')"
          >
            {{ t.l }}
            <span v-if="tab === t.k" class="absolute inset-x-3 -bottom-px h-0.5 rounded bg-coral"></span>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <!-- 公众号 -->
          <div v-if="tab === 'wechat'">
            <div class="mb-4 flex flex-wrap gap-2">
              <button class="btn-primary" :disabled="!wechatData" @click="copyRich">复制富文本</button>
              <button class="btn-ghost" :disabled="!wechatData" @click="copyHtml">复制 HTML</button>
              <button class="btn-ghost" :disabled="wechatLoading" @click="loadWechat">
                {{ wechatData ? '重新生成' : '生成公众号版' }}
              </button>
            </div>
            <div v-if="wechatLoading" class="py-14 text-center text-sm text-muted">正在排版…</div>
            <div v-else-if="wechatData" class="rounded-xl border border-line p-6">
              <div class="mb-2 text-xs text-muted">标题：{{ wechatData.title }}</div>
              <div class="mb-4 text-xs text-muted">摘要：{{ wechatData.digest }}</div>
              <div class="max-h-80 overflow-y-auto border-t border-line pt-4" v-html="wechatData.html"></div>
            </div>
            <div v-else class="py-14 text-center text-sm text-muted">点「生成公众号版」开始排版</div>
            <p class="mt-4 text-[11px] leading-relaxed text-muted">
              复制后到公众号后台正文里 Ctrl+V，样式会保留；图片若是外链需在公众号里重新上传。
            </p>
          </div>

          <!-- 小红书 -->
          <div v-else>
            <div class="mb-4 flex flex-wrap gap-2">
              <button class="btn-primary" :disabled="!xhsData" @click="copyXhs">复制文案</button>
              <button class="btn-ghost" :disabled="xhsLoading" @click="loadXhs">
                {{ xhsData ? '重新改写' : '生成小红书文案' }}
              </button>
            </div>
            <div v-if="xhsLoading" class="py-14 text-center text-sm text-muted">AI 正在改写…</div>
            <div v-else-if="xhsData" class="rounded-xl bg-[#FFF7F9] p-6">
              <div class="font-serif text-lg font-bold text-[#FF2442]">{{ xhsData.title }}</div>
              <div class="mt-3 whitespace-pre-wrap text-sm leading-[1.9] text-ink/85">{{ xhsData.body }}</div>
              <div class="mt-4 flex flex-wrap gap-1.5">
                <span v-for="t in xhsData.tags" :key="t" class="tag bg-[#FFE9EF] text-[#FF2442]">{{ t }}</span>
              </div>
            </div>
            <div v-else class="py-14 text-center text-sm text-muted">点「生成小红书文案」让 AI 改写</div>
            <p class="mt-4 text-[11px] text-muted">小红书是纯文本，复制后直接粘贴到 App 或创作中心。</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import { articleApi } from '@/api/article'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const article = ref<any>(null)
const showDistribute = ref(false)
const tab = ref<'wechat' | 'xhs'>('wechat')

const wechatData = ref<any>(null)
const xhsData = ref<any>(null)
const wechatLoading = ref(false)
const xhsLoading = ref(false)

const taskId = computed(() => route.params.taskId as string)

const renderedBody = computed(() => {
  // 优先渲染图文合成后的 fullContent（图片占位符已被替换），否则退回纯正文
  const md = article.value?.fullContent || article.value?.content || ''
  return md ? marked.parse(md) : '<p class="text-muted">正文为空</p>'
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

const openDistribute = () => {
  showDistribute.value = true
  if (tab.value === 'wechat' && !wechatData.value) loadWechat()
  if (tab.value === 'xhs' && !xhsData.value) loadXhs()
}

/** 失败的文章：带着原选题和文风重新发起创作 */
const retryCreate = () => {
  const a = article.value
  if (!a) return
  router.push({
    path: '/create',
    query: { topic: a.topic || '', style: a.style || '' },
  })
}

const switchTab = (k: 'wechat' | 'xhs') => {
  tab.value = k
  if (k === 'wechat' && !wechatData.value) loadWechat()
  if (k === 'xhs' && !xhsData.value) loadXhs()
}

const loadWechat = async () => {
  wechatLoading.value = true
  try {
    const res = await articleApi.toWechat(taskId.value)
    if (res.data.code === 0) wechatData.value = res.data.data
  } finally {
    wechatLoading.value = false
  }
}

const loadXhs = async () => {
  xhsLoading.value = true
  try {
    const res = await articleApi.toXiaohongshu(taskId.value)
    if (res.data.code === 0) xhsData.value = res.data.data
  } finally {
    xhsLoading.value = false
  }
}

const copyRich = async () => {
  if (!wechatData.value) return
  const html = wechatData.value.html
  const plain = html.replace(/<[^>]+>/g, '').replace(/\n{3,}/g, '\n\n').trim()
  try {
    if (navigator.clipboard && (window as any).ClipboardItem) {
      const item = new (window as any).ClipboardItem({
        'text/html': new Blob([html], { type: 'text/html' }),
        'text/plain': new Blob([plain], { type: 'text/plain' }),
      })
      await navigator.clipboard.write([item])
    } else {
      await navigator.clipboard.writeText(html)
    }
    alert('已复制富文本，去公众号后台 Ctrl+V 粘贴')
  } catch {
    alert('复制失败，请用「复制 HTML」或手动选中复制')
  }
}

const copyHtml = async () => {
  if (!wechatData.value) return
  await navigator.clipboard.writeText(wechatData.value.html)
  alert('已复制 HTML 源码')
}

const copyXhs = async () => {
  if (!xhsData.value) return
  const d = xhsData.value
  await navigator.clipboard.writeText(`${d.title}\n\n${d.body}\n\n${d.tags.join(' ')}`)
  alert('已复制小红书文案')
}

onMounted(async () => {
  try {
    const res = await articleApi.detail(taskId.value)
    article.value = res.data?.data || null
  } finally {
    loading.value = false
  }
})
</script>
