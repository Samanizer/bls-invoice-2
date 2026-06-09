/**
 * src/pages/Invoices.jsx - Invoice list page.
 * Shows all invoices with number, customer, date, total and status.
 * Links to view/edit and allows deletion.
 */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Eye, Pencil, Trash2, Download } from 'lucide-react'
import api from '../api'
import toast from 'react-hot-toast'

function Badge({ status }) {
  const cls = { draft: 'badge-draft', sent: 'badge-sent', paid: 'badge-paid' }
  return <span className={cls[status] || 'badge-draft'}>{status}</span>
}

export default function Invoices() {
  const [invoices, setInvoices] = useState([])

  async function load() {
    const { data } = await api.get('/invoices')
    setInvoices(data)
  }
  useEffect(() => { load() }, [])

  /** Delete with confirmation */
  async function handleDelete(inv) {
    if (!confirm(`Delete invoice ${inv.invoice_number}?`)) return
    await api.delete(`/invoices/${inv.id}`)
    toast.success('Invoice deleted')
    load()
  }

  /** Trigger PDF download directly in the browser */
  async function downloadPdf(inv) {
    try {
      const res = await api.get(`/invoices/${inv.id}/pdf`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a   = document.createElement('a')
      a.href    = url
      a.download = `invoice_${inv.invoice_number.replace(/\//g, '-')}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Failed to generate PDF')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Invoices</h1>
        <Link to="/invoices/new" className="btn-primary flex items-center gap-2">
          <Plus size={16} /> New Invoice
        </Link>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {['Invoice #','Customer','Date','Currency','Total','Status',''].map(h => (
                <th key={h} className="text-left px-4 py-3 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {invoices.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-10 text-center text-gray-400">No invoices yet — create one to get started</td></tr>
            )}
            {invoices.map(inv => (
              <tr key={inv.id} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="px-4 py-3 font-mono font-medium">
                  <Link to={`/invoices/${inv.id}`} className="text-brand-600 hover:underline">
                    {inv.invoice_number}
                  </Link>
                </td>
                <td className="px-4 py-3 text-gray-700">{inv.customer?.name}</td>
                <td className="px-4 py-3 text-gray-500">{inv.invoice_date}</td>
                <td className="px-4 py-3 text-gray-500">{inv.currency}</td>
                <td className="px-4 py-3 font-mono text-right text-gray-800">
                  {inv.invoice_total.toLocaleString('en', { minimumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-3"><Badge status={inv.status} /></td>
                <td className="px-4 py-3">
                  <div className="flex gap-1 justify-end">
                    <Link to={`/invoices/${inv.id}`}        title="View"   className="p-1.5 rounded hover:bg-gray-100 text-gray-500"><Eye     size={15} /></Link>
                    <Link to={`/invoices/${inv.id}/edit`}   title="Edit"   className="p-1.5 rounded hover:bg-brand-50 text-brand-600"><Pencil  size={15} /></Link>
                    <button onClick={() => downloadPdf(inv)} title="PDF"   className="p-1.5 rounded hover:bg-green-50 text-green-600"><Download size={15} /></button>
                    <button onClick={() => handleDelete(inv)} title="Delete" className="p-1.5 rounded hover:bg-red-50 text-red-500"><Trash2  size={15} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
