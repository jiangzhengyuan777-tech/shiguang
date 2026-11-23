import client from './client'

export interface LoginUser {
  id?: number
  userAccount?: string
  userName?: string
  userAvatar?: string
  userProfile?: string
  userRole?: string
  quota?: number
  vipTime?: string | null
}

export const authApi = {
  login: (data: { userAccount: string; userPassword: string }) =>
    client.post('/user/login', data),

  register: (data: { userAccount: string; userPassword: string; checkPassword: string }) =>
    client.post('/user/register', data),

  logout: () => client.post('/user/logout'),

  me: () => client.get('/user/get/login'),
}
