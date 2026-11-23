import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/AppShell.vue'),
      children: [
        { path: '', name: 'workspace', component: () => import('@/views/WorkspaceView.vue') },
        { path: 'create', name: 'create', component: () => import('@/views/CreateView.vue') },
        { path: 'library', name: 'library', component: () => import('@/views/LibraryView.vue') },
        {
          path: 'article/:taskId',
          name: 'article',
          component: () => import('@/views/ArticleView.vue'),
        },
        { path: 'vip', name: 'vip', component: () => import('@/views/VipView.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.loaded) await auth.fetchMe()

  if (to.meta.public) {
    if (auth.isLogin && to.path === '/login') return '/'
    return true
  }
  if (!auth.isLogin) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
