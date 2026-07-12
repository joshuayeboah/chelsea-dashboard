import React, { useState } from 'react'

const STATUS_COLORS = {
  active: { bg: '#e8f5ee', text: '#1d7a46' },
  loan: { bg: '#e8f0fb', text: '#034694' },
  suspended: { bg: '#fdecea', text: '#c0392b' },
  sold: { bg: '#f0f2f8', text: '#5a6278' },
}

const SORT_OPTIONS = [
  { value: 'fee_million', label: 'Fee' },
  { value: 'cost_per_90', label: 'Cost/90' },
  { value: 'minutes_util', label: 'Utilisation' },
  // { value: 'xg_xa_per_90', label: 'xG+xA/90' },
  { value: 'value_score', label: 'Value score' },
  { value: 'profit_loss', label: 'Profit/loss' },
]

function ValueBadge({ score }) {
  if (score === null) return <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Free</span>
  const color = score >= 1.2 ? '#1d7a46' : score >= 0.8 ? '#d97706' : '#c0392b'
  return (
    <span style={{
      fontWeight: 700,
      color,
      fontSize: 13,
    }}>
      {score.toFixed(2)}x
    </span>
  )
}

function UtilBar({ value }) {
  const color = value >= 60 ? '#1d7a46' : value >= 35 ? '#d97706' : '#c0392b'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 6, background: 'var(--surface-2)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ width: `${Math.min(value, 100)}%`, height: '100%', background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: 11, color: 'var(--text-secondary)', minWidth: 32 }}>{value}%</span>
    </div>
  )
}

export default function PlayerTable({ data }) {
  const [sortKey, setSortKey] = useState('fee_million')
  const [sortDir, setSortDir] = useState('desc')

  const sorted = [...data].sort((a, b) => {
    const av = a[sortKey] ?? -Infinity
    const bv = b[sortKey] ?? -Infinity
    return sortDir === 'desc' ? bv - av : av - bv
  })

  const toggleSort = (key) => {
    if (key === sortKey) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortKey(key); setSortDir('desc') }
  }

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow)',
      overflow: 'hidden',
    }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div>
          <h3 style={{ fontSize: 15, fontWeight: 700 }}>All signings</h3>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{data.length} players · BlueCo era</p>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {SORT_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => toggleSort(opt.value)}
              style={{
                padding: '4px 10px',
                borderRadius: 6,
                border: '1px solid',
                borderColor: sortKey === opt.value ? 'var(--chelsea-blue)' : 'var(--border)',
                background: sortKey === opt.value ? 'var(--chelsea-blue-faint)' : 'transparent',
                color: sortKey === opt.value ? 'var(--chelsea-blue)' : 'var(--text-secondary)',
                fontSize: 12,
                fontWeight: sortKey === opt.value ? 600 : 400,
                cursor: 'pointer',
              }}
            >
              {opt.label} {sortKey === opt.value ? (sortDir === 'desc' ? '↓' : '↑') : ''}
            </button>
          ))}
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--surface-2)' }}>
              {['Player', 'Pos', 'Season', 'Fee (£m)', 'Mins', 'Goals', 'Ast', 'Utilisation', 'Value score', 'Profit/loss'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap', borderBottom: '1px solid var(--border)' }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((p, i) => {
              const statusStyle = STATUS_COLORS[p.status] || STATUS_COLORS.active
              const pl = p.profit_loss
              return (
                <tr
                  key={p.id}
                  style={{
                    borderBottom: '1px solid var(--border)',
                    background: i % 2 === 0 ? 'var(--surface)' : 'var(--surface-2)',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--chelsea-blue-faint)'}
                  onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'var(--surface)' : 'var(--surface-2)'}
                >
                  <td style={{ padding: '9px 12px', whiteSpace: 'nowrap' }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{p.name}</div>
                    <span style={{
                      fontSize: 10, fontWeight: 600,
                      padding: '1px 6px', borderRadius: 4,
                      background: statusStyle.bg, color: statusStyle.text,
                    }}>
                      {p.status}
                    </span>
                  </td>
                  <td style={{ padding: '9px 12px', color: 'var(--text-secondary)', fontSize: 12 }}>{p.position}</td>
                  <td style={{ padding: '9px 12px', color: 'var(--text-secondary)', fontSize: 12 }}>{p.season}</td>
                  <td style={{ padding: '9px 12px', fontWeight: 600 }}>
                    {p.fee_million > 0 ? `£${p.fee_million}m` : <span style={{ color: 'var(--text-muted)' }}>Free</span>}
                  </td>
                  <td style={{ padding: '9px 12px' }}>{p.minutes_played?.toLocaleString()}</td>
                  <td style={{ padding: '9px 12px' }}>{p.goals}</td>
                  <td style={{ padding: '9px 12px' }}>{p.assists}</td>
                  {/* <td style={{ padding: '9px 12px', fontWeight: 600 }}>{p.xg_xa_per_90}</td> */}
                  <td style={{ padding: '9px 12px', minWidth: 120 }}><UtilBar value={p.minutes_util} /></td>
                  <td style={{ padding: '9px 12px' }}><ValueBadge score={p.value_score} /></td>
                  <td style={{ padding: '9px 12px', fontWeight: 600, color: pl >= 0 ? '#1d7a46' : '#c0392b' }}>
                    {pl >= 0 ? '+' : ''}£{pl}m
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
