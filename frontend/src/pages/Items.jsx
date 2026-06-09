/**
 * src/pages/Items.jsx - Item catalog management.
 * Lists all catalog items and provides a modal form to create/edit/delete them.
 */

import { useEffect, useState } from 'react'
import { Plus, Pencil, Trash2, X } from 'lucide-react'
import api from '../api'
import toast from 'react-hot-toast'

const EMPTY = { code: '', description: '', unit_price: '' }

export default function Items() {
  const [items, setItems]   = useState([])
  const [modal, setModal]   = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm]     = useState(EMPTY)

  async function load() {
    const { data } = await api.get('/items')
    setItems(data)
  }
  useEffect(() => { load() }, [])

  function openEdit(item) {
    setEditing(item)
    setForm({ code: item.code, description: item.description, unit_price: item.unit_price })
    setModal(true)
  }

  function openCreate() {
    setEditing(null)
    setForm(EMPTY)
    setModal(true)
  }

  async function handleSave(e) {
    e.preventDefault()
    const payload = { ...form, unit_price: parseFloat(form.unit_price) || 0 }
    try {
      if (editing) {
        await api.put(`/items/${editing.id}`, payload)
        toast.success('Item updated')
      } else {
        await api.post('/items', payload)
        toast.success('Item created')
      }
      setModal(false)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error saving item')
    }
  }

  async function handleDelete(item) {
    if (!confirm(`Delete ${item.code}?`)) return
    await api.delete(`/items/${item.id}`)
    toast.success('Item deleted')
    load()
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Item Catalog</h1>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> Add Item
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {['Code','Description','Default Price (USD)',''].map(h => (
                <th key={h} className="text-left px-4 py-3 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-10 text-center text-gray-400">No items yet</td></tr>
            )}
            {items.map(item => (
              <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="px-4 py-3 font-mono font-medium text-gray-800">{item.code}</td>
                <td className="px-4 py-3 text-gray-600">{item.description}</td>
                <td className="px-4 py-3 font-mono text-gray-700">{item.unit_price.toLocaleString('en', {minimumFractionDigits: 2})}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2 justify-end">
                    <button onClick={() => openEdit(item)} className="p-1.5 rounded hover:bg-brand-50 text-brand-600"><Pencil size={15} /></button>
                    <button onClick={() => handleDelete(item)} className="p-1.5 rounded hover:bg-red-50 text-red-500"><Trash2 size={15} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-800">{editing ? 'Edit Item' : 'New Item'}</h2>
              <button onClick={() => setModal(false)}><X size={18} className="text-gray-400" /></button>
            </div>
            <form onSubmit={handleSave} className="space-y-3">
              <div>
                <label className="label">Item Code *</label>
                <input className="input font-mono" required value={form.code} onChange={e => setForm({...form, code: e.target.value})} placeholder="BLUEBOX-KEC" />
              </div>
              <div>
                <label className="label">Description *</label>
                <textarea className="input" rows={3} required value={form.description} onChange={e => setForm({...form, description: e.target.value})} />
              </div>
              <div>
                <label className="label">Default Unit Price (USD)</label>
                <input className="input font-mono" type="number" step="0.01" min="0" value={form.unit_price} onChange={e => setForm({...form, unit_price: e.target.value})} />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" className="btn-primary flex-1">{editing ? 'Save Changes' : 'Create Item'}</button>
                <button type="button" onClick={() => setModal(false)} className="btn-secondary">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
