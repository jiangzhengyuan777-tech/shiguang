<template>
  <div class="flex min-h-screen">
    <!-- 左：品牌区 -->
    <div
      class="relative hidden flex-1 overflow-hidden bg-gradient-to-br from-[#FF8A65] via-[#FF6B4A] to-[#E85535] lg:block"
    >
      <div
        class="absolute inset-0 opacity-[0.18]"
        style="background-image: radial-gradient(#fff 1px, transparent 1px); background-size: 22px 22px"
      ></div>
      <div class="relative flex h-full flex-col justify-between p-14 text-white">
        <div class="flex items-center gap-2.5">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20 text-lg">✎</span>
          <span class="font-serif text-2xl font-bold tracking-wide">拾光</span>
        </div>

        <div>
          <h1 class="font-serif text-[2.6rem] font-bold leading-[1.3]">
            一句话命题<br />
            AI 替你写完一篇
          </h1>
          <p class="mt-5 max-w-sm text-sm leading-relaxed text-white/80">
            热点抓取 · 多智能体创作 · 公众号与小红书一键排版，把灵感变成能直接发布的内容。
          </p>
          <div class="mt-8 flex flex-wrap gap-2 text-xs">
            <span v-for="t in tags" :key="t" class="rounded-full bg-white/15 px-3 py-1.5">{{ t }}</span>
          </div>
        </div>

        <div class="text-xs text-white/60">© 2026 拾光 · 内容创作工作台</div>
      </div>
    </div>

    <!-- 右：表单区 -->
    <div class="flex w-full items-center justify-center px-6 py-10 lg:w-[520px]">
      <div class="w-full max-w-sm">
        <div class="mb-8 flex items-center gap-2.5 lg:hidden">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-coral to-amber text-lg text-white">✎</span>
          <span class="font-serif text-xl font-bold text-ink">拾光</span>
        </div>

        <h2 class="font-serif text-3xl font-bold text-ink">
          {{ registerMode ? '创建账号' : '欢迎回来' }}
        </h2>
        <p class="mt-2 text-sm text-muted">
          {{ registerMode ? '注册后即可开始创作' : '登录后继续你的创作' }}
        </p>

        <form class="mt-9 space-y-5" @submit.prevent="submit">
          <div>
            <label class="label">账号</label>
            <input
              v-model="account"
              class="input"
              placeholder="请输入账号"
              autocomplete="username"
            />
          </div>
          <div>
            <label class="label">密码</label>
            <input
              v-model="password"
              type="password"
              class="input"
              placeholder="请输入密码"
              :autocomplete="registerMode ? 'new-password' : 'current-password'"
            />
          </div>
          <div v-if="registerMode">
            <label class="label">确认密码</label>
            <input v-model="confirm" type="password" class="input" placeholder="再输入一次密码" />
          </div>

          <div v-if="error" class="rounded-lg bg-red-50 px-3.5 py-2.5 text-xs text-red-600">
            {{ error }}
          </div>

          <button type="submit" class="btn-primary w-full py-3 text-[15px]" :disabled="loading">
            {{ loading ? '处理中…' : registerMode ? '注册并登录' : '登录' }}
          </button>
        </form>

        <div class="mt-7 text-center text-xs text-muted">
          {{ registerMode ? '已经有账号了？' : '还没有账号？' }}
          <button class="ml-1 text-coral hover:underline" @click="toggleMode">
            {{ registerMode ? '去登录' : '注册一个' }}
          </button>
        </div>

        <div class="mt-8 rounded-xl border border-line bg-cream/60 px-4 py-3 text-[11px] leading-relaxed text-muted">
          演示账号：<span class="font-mono text-ink">admin</span> /
          <span class="font-mono text-ink">12345678</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const tags = ['从 0 到 1', '多智能体', '热点成文', '公众号排版', '小红书文案']

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const mode = ref<'login' | 'register'>('login')
const registerMode = computed(() => mode.value === 'register')
const account = ref('')
const password = ref('')
const confirm = ref('')
const loading = ref(false)
const error = ref('')

const toggleMode = () => {
  mode.value = mode.value === 'login' ? 'register' : 'login'
  error.value = ''
}

const submit = async () => {
  error.value = ''
  if (!account.value.trim() || !password.value.trim()) {
    error.value = '账号和密码不能为空'
    return
  }
  if (registerMode.value && password.value !== confirm.value) {
    error.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  try {
    if (registerMode.value) {
      const res = await authApi.register({
        userAccount: account.value.trim(),
        userPassword: password.value,
        checkPassword: confirm.value,
      })
      if (res.data.code !== 0) throw new Error(res.data.message || '注册失败')
    }
    await auth.login(account.value.trim(), password.value)
    const redirect = (route.query.redirect as string) || '/'
    router.replace(redirect)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
</script>
