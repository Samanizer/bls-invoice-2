/**
 * src/pages/Settings.jsx - Application settings page.
 * Allows editing company info, bank details, and uploading the company logo.
 * Changes are persisted to the Settings table and used in PDF generation.
 */

import { useEffect, useState } from 'react'
import { Save, Upload } from 'lucide-react'
import api from '../api'
import toast from 'react-hot-toast'

const FIELDS = [
  { group: 'Company', key: 'company_name',      label: 'Company Name' },
  { group: 'Company', key: 'company_address_1',  label: 'Address Line 1' },
  { group: 'Company', key: 'company_address_2',  label: 'Address Line 2' },
  { group: 'Company', key: 'company_license',    label: 'License Number' },
  { group: 'Company', key: 'company_tel',        label: 'Telephone' },
  { group: 'Company', key: 'company_email',      label: 'Email' },
  { group: 'Bank',    key: 'bank_ac_name',       label: 'Account Name' },
  { group: 'Bank',    key: 'bank_ac_number',     label: 'Account Number' },
  { group: 'Bank',    key: 'bank_iban',          label: 'IBAN' },
  { group: 'Bank',    key: 'bank_name',          label: 'Bank Name & Branch' },
  { group: 'Bank',    key: 'bank_swift',         label: 'SWIFT Code' },
]

export default function Settings() {
  const [values, setValues] = useState({})
  const [saving, setSaving] = useState(false)

  /** Load current settings from the API */
  useEffect(() => {
    api.get('/settings').then(r => setValues(r.data.settings || {})).catch(() => {})
  }, [])

  /** Save all settings in one request */
  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await api.put('/settings', { settings: values })
      toast.success('Settings saved')
    } catch {
      toast.error('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  /** Upload logo image */
  async function handleLogoUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const form = new FormData()
    form.append('file', file)
    try {
      await api.post('/settings/logo', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      toast.success('Logo uploaded')
    } catch {
      toast.error('Failed to upload logo')
    }
  }

  const groups = [...new Set(FIELDS.map(f => f.group))]

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-800">Settings</h1>

      <form onSubmit={handleSave} className="space-y-6">
        {groups.map(group => (
          <div key={group} className="card">
            <h2 className="font-semibold text-brand-700 text-sm uppercase tracking-wide border-b border-brand-100 pb-1 mb-4">
              {group} Details
            </h2>
            <div className="space-y-3">
              {FIELDS.filter(f => f.group === group).map(f => (
                <div key={f.key}>
                  <label className="label">{f.label}</label>
                  <input
                    className="input"
                    value={values[f.key] || ''}
                    onChange={e => setValues({ ...values, [f.key]: e.target.value })}
                  />
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Logo upload */}
        <div className="card">
          <h2 className="font-semibold text-brand-700 text-sm uppercase tracking-wide border-b border-brand-100 pb-1 mb-4">
            Company Logo
          </h2>
          <p className="text-sm text-gray-500 mb-3">Upload a PNG or JPG logo (will appear top-left on the PDF invoice).</p>
          <label className="flex items-center gap-3 cursor-pointer w-fit">
            <div className="btn-secondary flex items-center gap-2 text-sm">
              <Upload size={15} /> Upload Logo
            </div>
            <input type="file" accept="image/*" className="hidden" onChange={handleLogoUpload} />
          </label>
          {values.logo_path && (
            <p className="text-xs text-gray-400 mt-2">Stored: {values.logo_path}</p>
          )}
        </div>

        <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
          <Save size={15} /> {saving ? 'Saving…' : 'Save Settings'}
        </button>
      </form>
    </div>
  )
}
