/**
 * src/pages/InvoiceCreate.jsx - Invoice create/edit form.
 * Used for both creating a new invoice (route: /invoices/new)
 * and editing an existing one (route: /invoices/:id/edit).
 *
 * Features:
 * - Auto-suggest next invoice number for new invoices
 * - Customer selector with dropdown
 * - Line items with catalog auto-fill (description + price editable per line)
 * - Totals auto-calculated live
 * - All invoice header fields (destination, currency, payment, shipping, ref, notes, delivery note)
 */

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Plus, Trash2, ChevronDown } from 'lucide-react'
import api from '../api'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

/** Format a Date as "dd/Mon/yyyy" matching the invoice sample */
function fmtDate(d) {
  return format(d, 'dd/MMM/yyyy')
}

/** Empty line item template */
const EMPTY_LINE = { item_code: '', description: '', quantity: 1, unit_price: 0 }

export default function InvoiceCreate() {
  const { id } = useParams()           // set when editing
  const isEdit  = Boolean(id)
  const navigate = useNavigate()

  const [customers, setCustomers] = useState([])
  const [catalog,   setCatalog]   = useState([])   // item catalog for autocomplete

  // Invoice header fields
  const [header, setHeader] = useState({
    invoice_number: '',
    invoice_date:   fmtDate(new Date()),
    customer_id:    '',
    customer_type:  '',
    destination:    '',
    currency:       'USD',
    payment_method: 'TT',
    shipping_method:'N/A',
    reference:      '',
    freight:        0,
    notes:          '(Any Applicable Tax should be born by the Customer)',
    delivery_note:  '',
    status:         'draft',
  })

  // Line items array
  const [lines, setLines] = useState([{ ...EMPTY_LINE }])

  // ── Load initial data ──────────────────────────────────────────────────────
  useEffect(() => {
    async function init() {
      const [custRes, itemRes] = await Promise.all([
        api.get('/customers'),
        api.get('/items'),
      ])
      setCustomers(custRes.data)
      setCatalog(itemRes.data)

      if (isEdit) {
        // Load existing invoice for editing
        const { data } = await api.get(`/invoices/${id}`)
        setHeader({
          invoice_number:  data.invoice_number,
          invoice_date:    data.invoice_date,
          customer_id:     data.customer_id,
          customer_type:   data.customer_type || '',
          destination:     data.destination || '',
          currency:        data.currency || 'USD',
          payment_method:  data.payment_method || 'TT',
          shipping_method: data.shipping_method || 'N/A',
          reference:       data.reference || '',
          freight:         data.freight || 0,
          notes:           data.notes || '',
          delivery_note:   data.delivery_note || '',
          status:          data.status || 'draft',
        })
        setLines(data.line_items.map(li => ({
          item_code:   li.item_code,
          description: li.description,
          quantity:    li.quantity,
          unit_price:  li.unit_price,
        })))
      } else {
        // Suggest next invoice number for new invoice
        const { data: numData } = await api.get('/invoices/next-number')
        setHeader(h => ({ ...h, invoice_number: numData.invoice_number }))
      }
    }
    init()
  }, [id])

  // ── Line item helpers ──────────────────────────────────────────────────────

  /** Add a blank line item */
  function addLine() {
    setLines(prev => [...prev, { ...EMPTY_LINE }])
  }

  /** Remove a line item by index */
  function removeLine(idx) {
    setLines(prev => prev.filter((_, i) => i !== idx))
  }

  /** Update a field on a specific line */
  function updateLine(idx, field, value) {
    setLines(prev => {
      const next = [...prev]
      next[idx] = { ...next[idx], [field]: value }
      return next
    })
  }

  /**
   * When the user types/selects an item code, auto-fill description and price
   * from the catalog if an exact match is found.
   */
  function handleCodeChange(idx, code) {
    updateLine(idx, 'item_code', code)
    const match = catalog.find(c => c.code === code)
    if (match) {
      setLines(prev => {
        const next = [...prev]
        next[idx] = {
          ...next[idx],
          item_code:   match.code,
          description: match.description,
          unit_price:  match.unit_price,
        }
        return next
      })
    }
  }

  // ── Totals ────────────────────────────────────────────────────────────────

  const goodsTotal   = lines.reduce((sum, l) => sum + (parseFloat(l.quantity) || 0) * (parseFloat(l.unit_price) || 0), 0)
  const invoiceTotal = goodsTotal + (parseFloat(header.freight) || 0)

  // ── Submit ────────────────────────────────────────────────────────────────

  async function handleSubmit(e) {
    e.preventDefault()
    if (lines.length === 0) { toast.error('Add at least one line item'); return }

    const payload = {
      ...header,
      customer_id: parseInt(header.customer_id),
      freight:     parseFloat(header.freight) || 0,
      line_items:  lines.map(l => ({
        ...l,
        quantity:   parseFloat(l.quantity)   || 0,
        unit_price: parseFloat(l.unit_price) || 0,
      })),
    }

    try {
      if (isEdit) {
        await api.put(`/invoices/${id}`, payload)
        toast.success('Invoice updated')
        navigate(`/invoices/${id}`)
      } else {
        const { data } = await api.post('/invoices', payload)
        toast.success('Invoice created')
        navigate(`/invoices/${data.id}`)
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error saving invoice')
    }
  }

  // ── Section header helper ─────────────────────────────────────────────────
  function SectionTitle({ title }) {
    return <h2 className="text-sm font-semibold text-brand-700 uppercase tracking-wide border-b border-brand-100 pb-1 mb-3">{title}</h2>
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">{isEdit ? 'Edit Invoice' : 'New Invoice'}</h1>
        <button onClick={() => navigate(-1)} className="btn-secondary text-sm">Cancel</button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* ── Invoice identity ──────────────────────────────────────── */}
        <div className="card">
          <SectionTitle title="Invoice Details" />
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Invoice Number *</label>
              <input className="input font-mono" required value={header.invoice_number}
                onChange={e => setHeader({...header, invoice_number: e.target.value})} />
            </div>
            <div>
              <label className="label">Invoice Date *</label>
              <input className="input" required value={header.invoice_date}
                onChange={e => setHeader({...header, invoice_date: e.target.value})}
                placeholder="26/Feb/2026" />
            </div>
            <div>
              <label className="label">Status</label>
              <select className="input" value={header.status} onChange={e => setHeader({...header, status: e.target.value})}>
                <option value="draft">Draft</option>
                <option value="sent">Sent</option>
                <option value="paid">Paid</option>
              </select>
            </div>
          </div>
        </div>

        {/* ── Customer ─────────────────────────────────────────────── */}
        <div className="card">
          <SectionTitle title="Customer" />
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Customer *</label>
              <select className="input" required value={header.customer_id}
                onChange={e => {
                  const cid = e.target.value
                  const c   = customers.find(c => c.id == cid)
                  setHeader({...header, customer_id: cid, customer_type: c?.customer_type || ''})
                }}>
                <option value="">— Select customer —</option>
                {customers.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Customer Type (e.g. EXPORT)</label>
              <input className="input" value={header.customer_type}
                onChange={e => setHeader({...header, customer_type: e.target.value})} />
            </div>
          </div>
        </div>

        {/* ── Shipping / Payment details ────────────────────────────── */}
        <div className="card">
          <SectionTitle title="Shipping & Payment" />
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Destination</label>
              <input className="input" value={header.destination}
                onChange={e => setHeader({...header, destination: e.target.value})} />
            </div>
            <div>
              <label className="label">Currency</label>
              <input className="input" value={header.currency}
                onChange={e => setHeader({...header, currency: e.target.value})} />
            </div>
            <div>
              <label className="label">Payment Method</label>
              <input className="input" value={header.payment_method}
                onChange={e => setHeader({...header, payment_method: e.target.value})} />
            </div>
            <div>
              <label className="label">Shipping Method</label>
              <input className="input" value={header.shipping_method}
                onChange={e => setHeader({...header, shipping_method: e.target.value})} />
            </div>
            <div className="col-span-2">
              <label className="label">Ref / Proforma</label>
              <input className="input" value={header.reference}
                onChange={e => setHeader({...header, reference: e.target.value})} />
            </div>
          </div>
        </div>

        {/* ── Line Items ────────────────────────────────────────────── */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <SectionTitle title="Line Items" />
            <button type="button" onClick={addLine} className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700">
              <Plus size={15} /> Add Line
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-gray-500">
                  <th className="text-left pb-2 font-medium w-36">Item Code</th>
                  <th className="text-left pb-2 font-medium">Description</th>
                  <th className="text-right pb-2 font-medium w-24">Qty</th>
                  <th className="text-right pb-2 font-medium w-28">Unit Price</th>
                  <th className="text-right pb-2 font-medium w-28">Amount</th>
                  <th className="w-8"></th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line, idx) => (
                  <tr key={idx} className="border-b border-gray-50">
                    {/* Item code with datalist for catalog autocomplete */}
                    <td className="py-1 pr-2">
                      <input
                        list={`catalog-list-${idx}`}
                        className="input font-mono text-xs"
                        value={line.item_code}
                        onChange={e => handleCodeChange(idx, e.target.value)}
                        placeholder="CODE"
                      />
                      <datalist id={`catalog-list-${idx}`}>
                        {catalog.map(c => <option key={c.id} value={c.code}>{c.description}</option>)}
                      </datalist>
                    </td>
                    {/* Description — multi-line textarea */}
                    <td className="py-1 pr-2">
                      <textarea
                        className="input text-xs resize-none"
                        rows={2}
                        value={line.description}
                        onChange={e => updateLine(idx, 'description', e.target.value)}
                      />
                    </td>
                    <td className="py-1 pr-2">
                      <input
                        className="input text-right font-mono text-xs"
                        type="number" step="0.001" min="0"
                        value={line.quantity}
                        onChange={e => updateLine(idx, 'quantity', e.target.value)}
                      />
                    </td>
                    <td className="py-1 pr-2">
                      <input
                        className="input text-right font-mono text-xs"
                        type="number" step="0.01" min="0"
                        value={line.unit_price}
                        onChange={e => updateLine(idx, 'unit_price', e.target.value)}
                      />
                    </td>
                    <td className="py-1 text-right font-mono text-gray-700 pr-2">
                      {((parseFloat(line.quantity)||0) * (parseFloat(line.unit_price)||0)).toLocaleString('en',{minimumFractionDigits:2})}
                    </td>
                    <td className="py-1">
                      <button type="button" onClick={() => removeLine(idx)} className="p-1 hover:bg-red-50 text-red-400 rounded">
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Totals summary */}
          <div className="mt-4 flex justify-end">
            <div className="w-64 space-y-1 text-sm">
              <div className="flex justify-between text-gray-600">
                <span>Goods Total</span>
                <span className="font-mono">{goodsTotal.toLocaleString('en', {minimumFractionDigits:2})}</span>
              </div>
              <div className="flex justify-between items-center text-gray-600">
                <span>Freight</span>
                <input
                  className="input text-right font-mono text-xs w-28"
                  type="number" step="0.01" min="0"
                  value={header.freight}
                  onChange={e => setHeader({...header, freight: e.target.value})}
                />
              </div>
              <div className="flex justify-between font-semibold text-gray-800 pt-1 border-t border-gray-100">
                <span>Invoice Total {header.currency}</span>
                <span className="font-mono">{invoiceTotal.toLocaleString('en', {minimumFractionDigits:2})}</span>
              </div>
            </div>
          </div>
        </div>

        {/* ── Notes ────────────────────────────────────────────────── */}
        <div className="card">
          <SectionTitle title="Notes & Footer" />
          <div className="grid gap-4">
            <div>
              <label className="label">Notes / Disclaimer</label>
              <input className="input" value={header.notes}
                onChange={e => setHeader({...header, notes: e.target.value})} />
            </div>
            <div>
              <label className="label">Delivery Note (shown in Invoice Total row, e.g. "Delivered in Nairobi")</label>
              <input className="input" value={header.delivery_note}
                onChange={e => setHeader({...header, delivery_note: e.target.value})} />
            </div>
          </div>
        </div>

        {/* ── Submit ────────────────────────────────────────────────── */}
        <div className="flex gap-3">
          <button type="submit" className="btn-primary px-8">
            {isEdit ? 'Save Changes' : 'Create Invoice'}
          </button>
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
