<template>
  <div class="mx-auto max-w-3xl px-10 py-14">
    <div class="text-center">
      <span class="tag bg-coral-soft text-coral">会员专属</span>
      <h1 class="mt-4 font-serif text-[2.1rem] font-bold text-ink">
        {{ auth.isVip ? '你已是永久会员' : '升级永久会员' }}
      </h1>
      <p class="mt-3 text-sm text-muted">解锁全部高级功能，无限创作配额，终身有效</p>
    </div>

    <div class="card animate-fade-up mt-10 overflow-hidden">
      <div class="bg-gradient-to-br from-coral to-amber px-8 py-7 text-white">
        <div class="flex items-end justify-between">
          <div>
            <div class="text-sm text-white/80">永久会员</div>
            <div class="mt-1 font-serif text-4xl font-bold">
              ¥199<span class="ml-1 text-sm font-normal text-white/80">/ 永久</span>
            </div>
          </div>
          <div class="text-xs text-white/70 line-through">原价 ¥299</div>
        </div>
      </div>

      <div class="grid gap-4 px-8 py-8 sm:grid-cols-2">
        <div v-for="b in benefits" :key="b.t" class="flex gap-3">
          <span class="mt-0.5 text-coral">✓</span>
          <div>
            <div class="text-sm font-medium text-ink">{{ b.t }}</div>
            <div class="mt-0.5 text-xs text-muted">{{ b.d }}</div>
          </div>
        </div>
      </div>

      <div class="border-t border-line px-8 py-6">
        <button
          class="btn-primary w-full py-3"
          :disabled="auth.isVip || paying"
          @click="buy"
        >
          {{ auth.isVip ? '你已开通永久会员' : paying ? '跳转支付中…' : '立即升级' }}
        </button>
        <p class="mt-3 text-center text-[11px] text-muted">
          演示环境未接入真实支付，点击只取接口返回的支付链接状态
        </p>
      </div>
    </div>

    <div class="mt-8 text-center text-xs text-muted">
      <router-link to="/" class="hover:text-coral">返回工作台</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import client from '@/api/client'

const auth = useAuthStore()
const paying = ref(false)

const benefits = [
  { t: '无限创作配额', d: '不再受次数限制' },
  { t: '全部高级配图', d: 'AI 生图与 SVG 概念图' },
  { t: '大纲 AI 优化', d: '一键重排文章结构' },
  { t: '优先队列', d: '更快的生成速度' },
]

const buy = async () => {
  paying.value = true
  try {
    const res = await client.post('/payment/create-vip-session')
    const url = res.data?.data
    if (url) location.href = url
    else alert('支付通道未配置（需要 Stripe Key），演示环境跳过')
  } catch (e) {
    alert('支付未配置：' + (e as Error).message)
  } finally {
    paying.value = false
  }
}
</script>
