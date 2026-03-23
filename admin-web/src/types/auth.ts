export interface UserInfo {
  id: number
  username: string
  real_name: string
  avatar?: string
  role?: string
}

export interface AuthState {
  token: string | null
  user: UserInfo | null
}

export interface LoginResponse {
  token: string
  user: UserInfo
  message?: string
}
