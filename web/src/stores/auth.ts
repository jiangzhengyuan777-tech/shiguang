import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi, type LoginUser } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<LoginUser | null>(null)
  const loaded = ref(false)

  const isLogin = computed(() => !!user.value?.id)
  const isAdmin = computed(() => user.value?.userRole === 'admin')
  const isVip = computed(
    () => isAdmin.value || user.value?.userRole === 'vip' || !!user.value?.vipTime,
  )
  const quota = computed(() => user.value?.quota ?? 0)
  const hasQuota = computed(() => isAdmin.value || isVip.value || quota.value > 0)

  async function fetchMe() {
    try {
      const res = await authApi.me()
      user.value = res.data.code === 0 ? res.data.data : null
    } catch {
      user.value = null
    } finally {
      loaded.value = true
    }
  }

  async function login(account: string, password: string) {
    const res = await authApi.login({ userAccount: account, userPassword: password })
    if (res.data.code !== 0) throw new Error(res.data.message || '登录失败')
    user.value = res.data.data
    return user.value
  }

  async function logout() {
    await authApi.logout().catch(() => {})
    user.value = null
    location.href = '/login'
  }

  return { user, loaded, isLogin, isAdmin, isVip, quota, hasQuota, fetchMe, login, logout }
})
