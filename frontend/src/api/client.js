import axios from 'axios'

// Em desenvolvimento: baseURL vazio → proxy do Vite redireciona /api/* para localhost:8000
// Em produção (Vercel+Render): baseURL aponta para a URL do backend no Render
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
})

// Injeta o token JWT em todas as requisições automaticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redireciona para login em caso de 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_name')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
