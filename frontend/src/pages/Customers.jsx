/**
 * src/pages/Customers.jsx - Customer list with create/edit/delete functionality.
 * Renders a table of all customers and an inline modal form for add/edit.
 */

import { useEffect, useState } from 'react'
import { Plus, Pencil, Trash2, X } from 'lucide-react'
import api from '../api'
import toast from 'react-hot-toast'

const EMPTY = { name: '', address: '', customer_type: '', email: '', phone: '' }

export default function Customers() {
  const [customers, setCustomers] = useState([])
  const [modal, setModal]   = useState(false)   // true = show form
  const [editing, setEditing] = useState(null)  // null = create, else customer obj
  const [form, setForm]     = useState(EMPTY)

  /** Fetch customers from the API */
  async function load() {
    const { data } = await api.get('/customers')
    setCustomers(data)
  }

  useEffect(() => { load() }, [])

  /** Open the modal pre-filled for editing */
  function openEdit(c) {
    setEditing(c)
    setForm({ name: c.name, address: c.address || '', customer_type: c.customer_type || '', email: c.email || '', phone: c.phone || '' })
    setModal(true)
  }

  /** Open the modal blank for creating */
  function openCreate() {
    setEditing(null)
    setForm(EMPTY)
    setModal(true)
  }

  /** Save – either create or update */
  async function handleSave(e) {
    e.preventDefault()
    try {
      if (editing) {
        await api.put(`/customers/${editing.id}`, form)
        toast.success('Customer updated')
      } else {
        await api.post('/customers', form)
        toast.success('Customer created')
      }
      setModal(false)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error saving customer')
    }
  }

  /** Soft-delete a customer after confirmation */
  async function handleDelete(c) {
    if (!confirm(`Delete ${c.name}?`)) return
    await api.delete(`/customers/${c.id}`)
    toast.success('Customer deleted')
    load()
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Customers</h1>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> Add Customer
        </button>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {['Name','Type','Address','Email','Phone',''].map(h => (
                <th key={h} className="text-left px-4 py-3 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {customers.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-10 text-center text-gray-400">No customers yet</td></tr>
            )}
            {customers.map(c => (
              <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-800">{c.name}</td>
                <td className="px-4 py-3 text-gray-500">{c.customer_type || '—'}</td>
                <td className="px-4 py-3 text-gray-500 whitespace-pre-line">{c.address || '—'}</td>
                <td className="px-4 py-3 text-gray-500">{c.email || '—'}</td>
                <td className="px-4 py-3 text-gray-500">{c.phone || '—'}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2 justify-end">
                    <button onClick={() => openEdit(c)} className="p-1.5 rounded hover:bg-brand-50 text-brand-600"><Pencil size={15} /></button>
                    <button onClick={() => handleDelete(c)} className="p-1.5 rounded hover:bg-red-50 text-red-500"><Trash2 size={15} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {modal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-800">{editing ? 'Edit Customer' : 'New Customer'}</h2>
              <button onClick={() => setModal(false)}><X size={18} className="text-gray-400" /></button>
            </div>
            <form onSubmit={handleSave} className="space-y-3">
              <div>
                <label className="label">Name *</label>
                <input className="input" required value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
              </div>
              <div>
                <label className="label">Type (e.g. EXPORT)</label>
                <input className="input" value={form.customer_type} onChange={e => setForm({...form, customer_type: e.target.value})} />
              </div>
              <div>
                <label className="label">Address</label>
                <textarea className="input" rows={3} value={form.address} onChange={e => setForm({...form, address: e.target.value})} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Email</label>
                  <input className="input" type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
                </div>
                <div>
                  <label className="label">Phone</label>
                  <input className="input" value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" className="btn-primary flex-1">{editing ? 'Save Changes' : 'Create Customer'}</button>
                <button type="button" onClick={() => setModal(false)} className="btn-secondary">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
