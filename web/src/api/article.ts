import client from './client'

export const articleApi = {
  /** 创建文章任务 */
  create: (data: {
    topic: string
    style?: string
    enabledImageMethods?: string[]
    referenceContent?: string
    enableImages?: boolean
  }) => client.post('/article/create', data),

  /** 文章详情 */
  detail: (taskId: string) => client.get(`/article/${taskId}`),

  /** 文章列表 */
  list: (data: { pageNum?: number; pageSize?: number }) =>
    client.post('/article/list', data),

  /** 删除 */
  remove: (id: number) => client.post('/article/delete', { id }),

  /** 确认标题 */
  confirmTitle: (data: {
    taskId: string
    selectedMainTitle: string
    selectedSubTitle: string
    userDescription?: string
  }) => client.post('/article/confirm-title', data),

  /** 确认大纲 */
  confirmOutline: (data: { taskId: string; outline: any[] }) =>
    client.post('/article/confirm-outline', data),

  /** 执行日志 */
  logs: (taskId: string) => client.get(`/article/execution-logs/${taskId}`),

  /** 抓取热点链接 */
  fetchUrl: (url: string) => client.post('/article/fetch-url', { url }),

  /** 按文风推荐选题 */
  suggestTopics: (style?: string, count = 5) =>
    client.post('/article/suggest-topics', { style, count }),

  /** 生成公众号排版 */
  toWechat: (taskId: string) => client.post('/article/format/wechat', { taskId }),

  /** 生成小红书文案 */
  toXiaohongshu: (taskId: string) =>
    client.post('/article/format/xiaohongshu', { taskId }),

  /** SSE 进度地址 */
  progressUrl: (taskId: string) => `/api/article/progress/${taskId}`,
}
