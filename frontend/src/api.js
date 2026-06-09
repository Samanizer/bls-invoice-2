/**
 * src/api.js - Centralized Axios API client.
 * Automatically attaches the JWT Bearer token from localStorage to every request.
 * On 401 responses it clears the token and redirects to the login page.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

/** Attach token before every request */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/** On 401, clear auth state and redirect to login */
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
