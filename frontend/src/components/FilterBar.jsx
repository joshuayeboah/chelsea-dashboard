import React from 'react'

const POSITION_GROUPS = ['', 'GK', 'DEF', 'MID', 'FWD']
const SEASONS = ['', '2022-23', '2023-24', '2024-25', '2025-26']

const selectStyle = {
  padding: '6px 10px',
  borderRadius: 7,
  border: '1px solid var(--border)',
  background: 'var(--surface)',
  color: 'var(--text-primary)',
  fontSize: 13,
  cursor: 'pointer',
  outline: 'none',
}

export default function FilterBar({ filters, onChange }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '14px 20px',
      boxShadow: 'var(--shadow)',
      display: 'flex',
      gap: 12,
      alignItems: 'center',
      flexWrap: 'wrap',
    }}>
      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        Filter
      </span>

      <select
        style={selectStyle}
        value={filters.position_group || ''}
        onChange={e => onChange({ ...filters, position_group: e.target.value })}
      >
        {POSITION_GROUPS.map(p => (
          <option key={p} value={p}>{p || 'All positions'}</option>
        ))}
      </select>

      <select
        style={selectStyle}
        value={filters.season || ''}
        onChange={e => onChange({ ...filters, season: e.target.value })}
      >
        {SEASONS.map(s => (
          <option key={s} value={s}>{s || 'All seasons'}</option>
        ))}
      </select>

      <select
        style={selectStyle}
        value={filters.status || ''}
        onChange={e => onChange({ ...filters, status: e.target.value })}
      >
        <option value="">All statuses</option>
        <option value="active">Active</option>
        <option value="loan">Loan</option>
        <option value="suspended">Suspended</option>
        <option value="sold">Sold</option>
      </select>

      {(filters.position_group || filters.season || filters.status) && (
        <button
          onClick={() => onChange({})}
          style={{
            padding: '5px 12px',
            borderRadius: 6,
            border: '1px solid var(--border)',
            background: 'transparent',
            color: 'var(--text-secondary)',
            fontSize: 12,
            cursor: 'pointer',
          }}
        >
          Clear
        </button>
      )}
    </div>
  )
}
