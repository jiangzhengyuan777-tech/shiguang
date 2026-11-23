<template>
  <div class="mx-auto max-w-5xl px-10 py-12">
    <h1 class="font-serif text-[1.9rem] font-bold text-ink">开始创作</h1>
    <p class="mt-2 text-sm text-muted">给一个题目，AI 会先出标题方案，你选了之后再往下写。</p>

    <div class="mt-10 flex gap-8">
      <!-- 步骤条 -->
      <div class="w-44 shrink-0">
        <div v-for="(s, i) in steps" :key="s.key" class="relative flex gap-3 pb-8 last:pb-0">
          <div class="flex flex-col items-center">
            <span
              class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold transition-colors"
              :class="
                stepIndex >= i
                  ? 'border-coral bg-coral text-white'
                  : 'border-line bg-paper text-muted'
              "
            >
              {{ i + 1 }}
            </span>
            <span v-if="i < steps.length - 1" class="mt-1 w-px flex-1 bg-line"></span>
          </div>
          <div class="pt-1">
            <div class="text-sm font-medium" :class="stepIndex >= i ? 'text-ink' : 'text-muted'">
              {{ s.label }}
            </div>
            <div class="mt-0.5 text-[11px] leading-snug text-muted/70">{{ s.desc }}</div>
          </div>
        </div>
      </div>

      <!-- 主面板 -->
      <div class="min-w-0 flex-1">
        <!-- 步骤1：输入 -->
        <div v-if="step === 'input'" class="card animate-fade-up p-7">
          <label class="label">选题</label>
          <textarea
            v-model="topic"
            rows="3"
            class="input resize-none text-base"
            placeholder="例如：2026 年 AI 如何改变普通人的工作方式"
          ></textarea>

          <!-- 让 AI 推荐选题 -->
          <div class="mt-2.5 flex flex-wrap items-center gap-2">
            <button
              class="flex items-center gap-1.5 rounded-lg border border-dashed border-coral/40 px-3 py-1.5 text-xs text-coral transition-colors hover:bg-coral-soft"
              :disabled="suggesting"
              @click="askTopics"
            >
              <span>{{ suggesting ? '⏳' : '✨' }}</span>
              {{ suggesting ? '正在想选题…' : '不知道写什么？让 AI 推荐' }}
            </button>
            <template v-if="suggestions.length">
              <span class="text-[11px] text-muted">点一个直接用：</span>
              <button
                v-for="t in suggestions"
                :key="t"
                class="rounded-full border border-line px-3 py-1 text-xs text-ink/70 transition-colors hover:border-coral hover:text-coral"
                @click="pickSuggestion(t)"
              >
                {{ t }}
              </button>
            </template>
          </div>

          <!-- 参考热点 -->
          <div class="mt-6">
            <label class="label">参考热点（可选）</label>
            <div v-if="!reference" class="flex gap-2">
              <input
                v-model="refUrl"
                class="input"
                placeholder="贴一篇新闻 / 公众号文章链接，自动抓取正文"
                @keydown.enter="fetchRef"
              />
              <button class="btn-ghost shrink-0" :disabled="fetchingRef" @click="fetchRef">
                {{ fetchingRef ? '抓取中…' : '抓取' }}
              </button>
            </div>
            <div v-else class="rounded-xl border border-coral/25 bg-coral-soft/50 p-4">
              <div class="flex items-center gap-2 text-sm font-semibold text-ink">
                <span class="text-coral">✓</span>
                <span class="truncate">{{ reference.title }}</span>
                <span class="tag bg-paper text-muted">{{ reference.source }}</span>
                <span class="tag bg-paper text-muted">{{ reference.wordCount }} 字</span>
              </div>
              <p class="mt-2 line-clamp-2 text-xs leading-relaxed text-muted">
                {{ reference.content }}
              </p>
              <button class="mt-2 text-xs text-coral hover:underline" @click="clearRef">移除素材</button>
            </div>
            <p v-if="refError" class="mt-2 text-xs text-red-500">{{ refError }}</p>
          </div>

          <!-- 风格 -->
          <div class="mt-6">
            <label class="label">文风</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="s in styles"
                :key="s.value"
                class="rounded-xl border px-3.5 py-2 text-sm transition-all"
                :class="
                  style === s.value
                    ? 'border-coral bg-coral-soft font-medium text-coral'
                    : 'border-line text-ink/70 hover:border-coral/50'
                "
                @click="style = s.value"
              >
                {{ s.label }}
              </button>
            </div>
          </div>

          <!-- 配图 -->
          <div class="mt-6">
            <label class="label">配图</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="o in imageOptions"
                :key="String(o.value)"
                class="rounded-xl border px-3.5 py-2 text-sm transition-all"
                :class="
                  enableImages === o.value
                    ? 'border-coral bg-coral-soft font-medium text-coral'
                    : 'border-line text-ink/70 hover:border-coral/50'
                "
                @click="enableImages = o.value"
              >
                {{ o.label }}
                <span class="ml-1 text-[11px] opacity-70">{{ o.hint }}</span>
              </button>
            </div>
          </div>

          <div v-if="error" class="mt-5 rounded-lg bg-red-50 px-3.5 py-2.5 text-xs text-red-600">
            {{ error }}
          </div>

          <button
            class="btn-primary mt-7 w-full py-3"
            :disabled="creating || !topic.trim()"
            @click="startCreate"
          >
            {{ creating ? '正在生成标题…' : '生成标题方案' }}
          </button>
        </div>

        <!-- 步骤2：选标题 -->
        <div v-else-if="step === 'title'" class="space-y-3">
          <div class="mb-1 text-sm text-muted">选一个你最想写的方向：</div>
          <button
            v-for="(t, i) in titles"
            :key="i"
            class="card w-full animate-fade-up p-5 text-left transition-all hover:-translate-y-0.5 hover:border-coral/40 hover:shadow-lift"
            :style="{ animationDelay: `${i * 60}ms` }"
            :class="{ 'border-coral bg-coral-soft/40': picked === i }"
            @click="picked = i"
          >
            <div class="font-serif text-lg font-bold leading-snug text-ink">{{ t.mainTitle }}</div>
            <div class="mt-1.5 text-sm text-muted">{{ t.subTitle }}</div>
          </button>

          <div class="mt-6">
            <label class="label">补充要求（可选）</label>
            <input v-model="extra" class="input" placeholder="比如：面向普通职场人，多举例子" />
          </div>

          <div class="mt-5 flex gap-3">
            <button class="btn-ghost" @click="reset">重新开始</button>
            <button class="btn-primary flex-1 py-3" :disabled="picked < 0 || loading" @click="chooseTitle">
              {{ loading ? '正在生成大纲…' : '用这个标题，生成大纲' }}
            </button>
          </div>
        </div>

        <!-- 步骤3：大纲 -->
        <div v-else-if="step === 'outline'" class="card animate-fade-up p-7">
          <div class="mb-5">
            <div class="font-serif text-xl font-bold text-ink">{{ selectedTitle?.mainTitle }}</div>
            <div class="mt-1 text-sm text-muted">{{ selectedTitle?.subTitle }}</div>
          </div>

          <!-- 流式规划中：从原始 JSON 里实时提取章节标题 -->
          <div v-if="!outline.length" class="rounded-xl bg-cream/60 p-5">
            <div class="mb-3 flex items-center gap-2 text-xs font-medium text-coral">
              <span class="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-coral"></span>
              AI 正在规划大纲…
            </div>
            <ul class="space-y-2">
              <li
                v-for="(s, i) in streamedSections"
                :key="i"
                class="flex items-start gap-2 text-sm text-ink/80"
              >
                <span class="shrink-0 text-coral">{{ i + 1 }}.</span>
                <span>{{ s }}</span>
              </li>
            </ul>
            <div class="mt-2 text-xs text-muted">
              {{ streamedSections.length ? `正在生成第 ${streamedSections.length + 1} 节…` : '思考中…' }}
            </div>
          </div>

          <div v-else class="space-y-4">
            <div v-for="(sec, i) in outline" :key="i" class="rounded-xl bg-cream/70 p-4">
              <div class="font-medium text-ink">{{ i + 1 }}. {{ sec.title }}</div>
              <ul class="mt-2 space-y-1">
                <li v-for="(p, j) in sec.points || []" :key="j" class="text-xs leading-relaxed text-muted">
                  · {{ p }}
                </li>
              </ul>
            </div>
          </div>

          <div class="mt-6 flex gap-3">
            <button class="btn-ghost" @click="reset">重新开始</button>
            <button
              class="btn-primary flex-1 py-3"
              :disabled="!outline.length || loading"
              @click="confirmOutlineStep"
            >
              {{ loading ? '正在写正文…' : '确认大纲，开始写正文' }}
            </button>
          </div>
        </div>

        <!-- 步骤4：写作中（流式展示） -->
        <div v-else-if="step === 'writing'" class="card animate-fade-up p-7">
          <div class="mb-3 flex items-center gap-2 text-sm font-medium text-ink">
            <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-coral"></span>
            AI 正在撰写正文…
            <span class="ml-auto text-xs font-normal text-muted">{{ contentStream.length }} 字</span>
          </div>
          <pre class="max-h-96 overflow-y-auto whitespace-pre-wrap font-sans text-sm leading-[1.9] text-ink/85">{{ contentStream }}<span class="animate-pulse text-coral">▍</span></pre>
          <div v-if="generatingImages" class="mt-4 flex items-center gap-2 rounded-lg bg-cream/70 px-3 py-2 text-xs text-muted">
            <span class="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-coral"></span>
            <template v-if="imageTotal">
              正文已完成，正在生成配图 {{ imageDone }}/{{ imageTotal }}…
            </template>
            <template v-else>正文已完成，正在生成配图与图文合成…</template>
          </div>
        </div>

        <!-- 完成 -->
        <div v-else class="card animate-fade-up p-10 text-center">
          <div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-sage/15 text-xl text-sage">
            ✓
          </div>
          <div class="font-serif text-lg font-bold text-ink">文章已生成</div>
          <button class="btn-primary mt-6" @click="openArticle">查看并分发</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { articleApi } from '@/api/article'

const router = useRouter()
const route = useRoute()

type Step = 'input' | 'title' | 'outline' | 'writing' | 'done'

const steps = [
  { key: 'input', label: '选题', desc: '输入题目与素材' },
  { key: 'title', label: '标题', desc: '从方案里挑一个' },
  { key: 'outline', label: '大纲', desc: '确认文章结构' },
  { key: 'writing', label: '正文', desc: 'AI 撰写全文' },
]

const step = ref<Step>('input')
const topic = ref('')
const extra = ref('')
const style = ref('')
const taskId = ref('')
const titles = ref<any[]>([])
const picked = ref(-1)
const outline = ref<any[]>([])
const selectedTitle = ref<any>(null)
const loading = ref(false)
const creating = ref(false)
const error = ref('')

// ---- SSE 流式状态 ----
let es: EventSource | null = null
let pollTimer: number | null = null
const outlineStream = ref('')   // 大纲逐字内容
const contentStream = ref('')   // 正文逐字内容
const streaming = ref(false)    // 是否正在流式接收
const generatingImages = ref(false) // 正文写完后进入配图阶段
const imageDone = ref(0)        // 已生成配图数
const imageTotal = ref(0)       // 需要生成的配图总数

/** 从流式 JSON 片段里实时提取已完成的小节标题 */
const streamedSections = computed(() => {
  const matches = [...outlineStream.value.matchAll(/"title"\s*:\s*"([^"]+)"/g)]
  return matches.map((m) => m[1])
})

// 热点素材
const refUrl = ref('')
const fetchingRef = ref(false)
const refError = ref('')
const reference = ref<any>(null)

// AI 推荐选题
const suggesting = ref(false)
const suggestions = ref<string[]>([])

const askTopics = async () => {
  suggesting.value = true
  try {
    const res = await articleApi.suggestTopics(style.value || undefined, 5)
    if (res.data.code === 0) suggestions.value = res.data.data || []
    else error.value = res.data.message || '生成选题失败'
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    suggesting.value = false
  }
}

const pickSuggestion = (t: string) => {
  topic.value = t
  suggestions.value = []
}

const styles = [
  { label: '默认', value: '' },
  { label: '公众号官方', value: 'wechat_official' },
  { label: '营销号', value: 'marketing' },
  { label: '小红书', value: 'xiaohongshu' },
]

// 是否生成配图
const enableImages = ref(true)
const imageOptions = [
  { label: '自动配图', value: true, hint: '约 +30s' },
  { label: '纯文字', value: false, hint: '最快出稿' },
]

const stepIndex = computed(() => {
  const order: Step[] = ['input', 'title', 'outline', 'writing']
  const i = order.indexOf(step.value)
  return i < 0 ? order.length : i
})

const fetchRef = async () => {
  refError.value = ''
  if (!refUrl.value.trim()) return
  fetchingRef.value = true
  try {
    const res = await articleApi.fetchUrl(refUrl.value.trim())
    if (res.data.code === 0) reference.value = res.data.data
    else refError.value = res.data.message || '抓取失败'
  } catch (e) {
    refError.value = (e as Error).message
  } finally {
    fetchingRef.value = false
  }
}

const clearRef = () => {
  reference.value = null
  refUrl.value = ''
  refError.value = ''
}

const reset = () => {
  closeSSE()
  stopStatusPoll()
  step.value = 'input'
  titles.value = []
  outline.value = []
  picked.value = -1
  selectedTitle.value = null
  taskId.value = ''
  error.value = ''
  outlineStream.value = ''
  contentStream.value = ''
  streaming.value = false
  generatingImages.value = false
  imageDone.value = 0
  imageTotal.value = 0
  creating.value = false
  loading.value = false
}

// ===================== SSE 流式 =====================
const closeSSE = () => {
  if (es) {
    es.close()
    es = null
  }
}

/**
 * 配图阶段的轮询兜底：
 * SSE 连接可能因空闲被代理断开（此时单张完成消息会丢失），
 * 这里直接查任务详情，保证进度和完成状态一定拿得到。
 */
const startStatusPoll = () => {
  if (pollTimer) return
  pollTimer = window.setInterval(async () => {
    if (!taskId.value) return
    try {
      const d = await articleApi.detail(taskId.value)
      const data = d.data?.data
      if (!data) return
      if (data.images?.length) imageDone.value = data.images.length
      if (data.status === 'COMPLETED') {
        stopStatusPoll()
        generatingImages.value = false
        loading.value = false
        step.value = 'done'
        closeSSE()
      } else if (data.status === 'FAILED') {
        stopStatusPoll()
        generatingImages.value = false
        loading.value = false
        error.value = data.errorMessage || '生成失败'
        closeSSE()
      }
    } catch {
      // 忽略瞬时错误，下一轮再试
    }
  }, 2500)
}

const stopStatusPoll = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const connectSSE = (tid: string) => {
  closeSSE()
  es = new EventSource(`/api/article/progress/${tid}`)
  es.onmessage = (ev) => {
    if (!ev.data) return
    try {
      handleSSE(JSON.parse(ev.data))
    } catch {
      // 忽略非 JSON 的心跳/空行
    }
  }
  // EventSource 断线会自己重连，这里不主动关闭
  es.onerror = () => {}
}

const handleSSE = (msg: any) => {
  switch (msg.type) {
    case 'TITLES_GENERATED':
    case 'AGENT1_COMPLETE':
      if (msg.titleOptions?.length) {
        titles.value = msg.titleOptions
        creating.value = false
        step.value = 'title'
      }
      break

    case 'AGENT2_STREAMING':
      // 大纲逐字推送：先进入大纲步骤，边收边显示
      streaming.value = true
      step.value = 'outline'
      outlineStream.value += msg.content || ''
      break

    case 'OUTLINE_GENERATED':
      outline.value = msg.outline || []
      loading.value = false
      break

    case 'AGENT2_COMPLETE':
      if (msg.outline?.length) outline.value = msg.outline
      break

    case 'AGENT3_STREAMING':
      streaming.value = true
      step.value = 'writing'
      contentStream.value += msg.content || ''
      break

    case 'AGENT3_COMPLETE':
      // 正文写完，后面是配图分析 + 生成 + 合成；启动状态轮询兜底
      generatingImages.value = true
      startStatusPoll()
      break

    case 'AGENT4_COMPLETE':
      // 收到配图需求总数，用于显示 3/6 这样的进度
      imageTotal.value = (msg.imageRequirements || []).length
      imageDone.value = 0
      break

    case 'IMAGE_COMPLETE':
      imageDone.value += 1
      break

    case 'ALL_COMPLETE':
      streaming.value = false
      generatingImages.value = false
      loading.value = false
      step.value = 'done'
      stopStatusPoll()
      closeSSE()
      break

    case 'ERROR':
      error.value = msg.message || '生成失败'
      streaming.value = false
      creating.value = false
      loading.value = false
      closeSSE()
      break
  }
}

const startCreate = async () => {
  if (!topic.value.trim()) return
  error.value = ''
  creating.value = true
  outlineStream.value = ''
  contentStream.value = ''
  try {
    const res = await articleApi.create({
      topic: topic.value.trim(),
      style: style.value || undefined,
      referenceContent: reference.value?.content || undefined,
      enableImages: enableImages.value,
    })
    if (res.data.code !== 0) throw new Error(res.data.message || '创建失败')
    taskId.value = res.data.data
    // 建连后一切由 SSE 驱动（标题方案到达会切到下一步）
    connectSSE(taskId.value)

    // 兜底：若 15 秒内没收到任何 SSE 消息（连接建立晚于任务启动），补查一次
    setTimeout(async () => {
      if (step.value !== 'input' || !creating.value) return
      try {
        const d = await articleApi.detail(taskId.value)
        const data = d.data?.data
        if (data?.titleOptions?.length) {
          titles.value = data.titleOptions
          creating.value = false
          step.value = 'title'
        }
      } catch {
        // 忽略
      }
    }, 15000)
  } catch (e) {
    error.value = (e as Error).message
    creating.value = false
  }
}

const chooseTitle = async () => {
  const t = titles.value[picked.value]
  if (!t) return
  selectedTitle.value = t
  loading.value = true
  outlineStream.value = ''
  try {
    await articleApi.confirmTitle({
      taskId: taskId.value,
      selectedMainTitle: t.mainTitle,
      selectedSubTitle: t.subTitle,
      userDescription: extra.value || undefined,
    })
    // 大纲由 SSE 推送，这里只切步骤占位
    step.value = 'outline'
  } catch (e) {
    error.value = (e as Error).message
    loading.value = false
  }
}

const confirmOutlineStep = async () => {
  loading.value = true
  contentStream.value = ''
  step.value = 'writing'
  try {
    await articleApi.confirmOutline({ taskId: taskId.value, outline: outline.value })
    // 正文由 SSE 推送
  } catch (e) {
    error.value = (e as Error).message
    loading.value = false
    step.value = 'outline'
  }
}

const openArticle = () => router.push(`/article/${taskId.value}`)

onBeforeUnmount(() => {
  closeSSE()
  stopStatusPoll()
})

onMounted(() => {
  const t = route.query.topic as string
  if (t) topic.value = t
  const s = route.query.style as string
  if (s) style.value = s
})
</script>

<style scoped>
@keyframes slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(300%); }
}
</style>
