/**
 * src/pages/Login.jsx - Login page.
 * Simple username + password form. On success, stores the JWT and redirects to dashboard.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileCheck } from 'lucide-react'
import api from '../api'
import toast from 'react-hot-toast'

export default function Login() {
  const [form, setForm] = useState({ username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  /** Submit credentials and store token on success */
  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', form)
      localStorage.setItem('token', data.access_token)
      navigate('/')
    } catch {
      toast.error('Invalid username or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-brand-900">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-sm">
        {/* Logo / brand */}
        <div className="flex flex-col items-center mb-8">
          <div className="bg-brand-600 text-white rounded-xl p-3 mb-3">
            <FileCheck size={28} />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">BLS Invoice</h1>
          <p className="text-gray-500 text-sm mt-1">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Username</label>
            <input
              className="input"
              type="text"
              value={form.username}
              onChange={e => setForm({ ...form, username: e.target.value })}
              placeholder="admin"
              required
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder="••••••••"
              required
            />
          </div>
          <button
            type="submit"
            className="btn-primary w-full mt-2"
            disabled={loading}
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          Default: admin / admin123
        </p>
      </div>
    </div>
  )
}
