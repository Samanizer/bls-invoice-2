/**
 * src/pages/InvoiceView.jsx - Invoice detail view.
 * Displays an on-screen preview of the invoice matching the PDF layout.
 * Provides buttons to edit, download PDF, change status, and delete.
 */

import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Pencil, Download, Trash2, ArrowLeft, CheckCircle } from 'lucide-react'
import api from '../api'
import toast from 'react-hot-toast'

function Badge({ status }) {
  const cls = { draft: 'badge-draft', sent: 'badge-sent', paid: 'badge-paid' }
  return <span className={cls[status] || 'badge-draft'}>{status}</span>
}

export default function InvoiceView() {
  const { id }  = useParams()
  const navigate = useNavigate()
  const [inv, setInv]       = useState(null)
  const [settings, setSettings] = useState({})

  useEffect(() => {
    Promise.all([
      api.get(`/invoices/${id}`),
      api.get('/settings'),
    ]).then(([invRes, setRes]) => {
      setInv(invRes.data)
      setSettings(setRes.data.settings || {})
    })
  }, [id])

  async function downloadPdf() {
    try {
      const res = await api.get(`/invoices/${id}/pdf`, { responseType: 'blob' })
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

  async function handleDelete() {
    if (!confirm(`Delete invoice ${inv.invoice_number}?`)) return
    await api.delete(`/invoices/${id}`)
    toast.success('Invoice deleted')
    navigate('/invoices')
  }

  async function markPaid() {
    await api.put(`/invoices/${id}`, { ...inv, line_items: inv.line_items, status: 'paid' })
    toast.success('Marked as paid')
    setInv(prev => ({ ...prev, status: 'paid' }))
  }

  if (!inv) return <div className="text-gray-400 text-center py-20">Loading…</div>

  const s = settings

  return (
    <div className="space-y-4">
      {/* Action bar */}
      <div className="flex items-center justify-between">
        <Link to="/invoices" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft size={15} /> Back to Invoices
        </Link>
        <div className="flex gap-2">
          {inv.status !== 'paid' && (
            <button onClick={markPaid} className="btn-secondary flex items-center gap-2 text-sm text-green-600">
              <CheckCircle size={15} /> Mark Paid
            </button>
          )}
          <Link to={`/invoices/${id}/edit`} className="btn-secondary flex items-center gap-2 text-sm">
            <Pencil size={15} /> Edit
          </Link>
          <button onClick={downloadPdf} className="btn-primary flex items-center gap-2 text-sm">
            <Download size={15} /> Download PDF
          </button>
          <button onClick={handleDelete} className="btn-danger flex items-center gap-2 text-sm">
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      {/* ── Invoice Preview — styled to mirror the PDF layout ── */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-8 max-w-3xl mx-auto font-mono text-sm" id="invoice-preview">

        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="text-2xl font-bold text-brand-700 tracking-wide">
            {s.company_name || 'BLUELIGHT FZCO'}
          </div>
          <div className="text-right text-xs text-gray-600 space-y-0.5">
            <div className="font-bold">{s.company_name || 'BLUELIGHT FZCO'}</div>
            <div>{s.company_address_1}</div>
            <div>{s.company_address_2}</div>
            {s.company_license && <div>License No: {s.company_license}</div>}
            {s.company_tel     && <div>Tel: {s.company_tel}</div>}
            {s.company_email   && <div>{s.company_email}</div>}
          </div>
        </div>

        {/* Invoice bar */}
        <div className="flex justify-between items-center bg-gray-100 border border-gray-300 px-4 py-2 mb-5 text-xs">
          <span className="font-bold text-base">INVOICE</span>
          <span><strong>No:</strong> {inv.invoice_number}</span>
          <span><strong>Date:</strong> {inv.invoice_date}</span>
        </div>

        {/* Customer block */}
        <div className="flex justify-between mb-4">
          <div>
            <div className="font-bold text-xs mb-1">Customer:</div>
            <div className="font-bold text-sm">{inv.customer?.name?.toUpperCase()}</div>
            <div className="text-xs text-gray-600 whitespace-pre-line">{inv.customer?.address}</div>
          </div>
          <div className="text-xs text-gray-600 font-bold">{inv.customer_type}</div>
        </div>

        {/* Details grid */}
        <div className="grid grid-cols-3 gap-2 mb-4 text-xs">
          <div>
            <div className="font-bold">Destination:</div>
            <div>{inv.destination || 'N/A'}</div>
            <div className="font-bold mt-1">Shipping Method:</div>
            <div>{inv.shipping_method || 'N/A'}</div>
          </div>
          <div>
            <div className="font-bold">Invoice Currency:</div>
            <div>{inv.currency}</div>
            <div className="font-bold mt-1">Ref / Proforma:</div>
            <div>{inv.reference || '—'}</div>
          </div>
          <div className="border border-gray-300 p-2">
            <div className="font-bold">Payment:</div>
            <div>{inv.payment_method}</div>
          </div>
        </div>

        {/* Items table */}
        <table className="w-full text-xs border-collapse mb-4">
          <thead>
            <tr className="border-t-2 border-b-2 border-gray-400">
              <th className="text-left py-1 w-28">Item</th>
              <th className="text-left py-1">Description</th>
              <th className="text-right py-1 w-20">Quantity</th>
              <th className="text-right py-1 w-24">Amount ({inv.currency})</th>
            </tr>
          </thead>
          <tbody>
            {inv.line_items.map((li, idx) => (
              <tr key={idx} className="border-b border-gray-100">
                <td className="py-1.5 align-top">{li.item_code}</td>
                <td className="py-1.5 whitespace-pre-wrap">{li.description}</td>
                <td className="py-1.5 text-right align-top">{li.quantity}</td>
                <td className="py-1.5 text-right align-top font-mono">{li.amount.toLocaleString('en',{minimumFractionDigits:2})}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Notes */}
        {inv.notes && <p className="text-xs text-gray-500 mb-6">{inv.notes}</p>}

        {/* Footer: bank details + totals */}
        <div className="flex gap-4 mt-8">
          {/* Bank details */}
          <div className="border border-gray-300 p-3 text-xs flex-1">
            <div className="font-bold mb-1">Bank Details:</div>
            {s.bank_ac_name   && <div>A/C Name: {s.bank_ac_name}</div>}
            {s.bank_ac_number && <div>A/C Number: {s.bank_ac_number}</div>}
            {s.bank_iban      && <div><strong>IBAN: {s.bank_iban}</strong></div>}
            {s.bank_name      && <div>Bank: {s.bank_name}</div>}
            {s.bank_swift     && <div>Swift: {s.bank_swift}</div>}
          </div>

          {/* Totals */}
          <div className="w-56 text-xs">
            <div className="flex justify-between border border-gray-300 px-3 py-2">
              <span className="font-bold">Goods Total</span>
              <span className="font-mono">{inv.goods_total.toLocaleString('en',{minimumFractionDigits:2})}</span>
            </div>
            <div className="flex justify-between border border-gray-300 border-t-0 px-3 py-2">
              <span className="font-bold">Freight</span>
              <span className="font-mono">{(inv.freight||0).toLocaleString('en',{minimumFractionDigits:2})}</span>
            </div>
            <div className="flex justify-between bg-brand-900 text-white border border-brand-900 px-3 py-2">
              <div>
                <div className="font-bold">Invoice Total {inv.currency}</div>
                {inv.delivery_note && <div className="text-gray-300 text-xs">({inv.delivery_note})</div>}
              </div>
              <span className="font-mono font-bold text-sm">
                {inv.invoice_total.toLocaleString('en',{minimumFractionDigits:2})}
              </span>
            </div>
          </div>
        </div>

        {/* Status badge */}
        <div className="flex justify-between items-center mt-4 text-xs text-gray-400">
          <Badge status={inv.status} />
          <span>Page: 1/1</span>
        </div>
      </div>
    </div>
  )
}
