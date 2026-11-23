import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 180000,
  withCredentials: true,
})

client.interceptors.response.use(
  (res) => {
    const data = res.data
    if (data && data.code === 40100) {
      if (!location.pathname.startsWith('/login')) {
        location.href = '/login'
      }
    }
    return res
  },
  (err) => {
    // 后端异常统一包装（FastAPI 非业务异常会走这里）
    const msg =
      err?.response?.data?.message ||
      err?.response?.data?.detail?.[0]?.msg ||
      err?.message ||
      '网络异常'
    return Promise.reject(new Error(msg))
  },
)

export default client
