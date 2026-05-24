import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function SpendBySeasonChart({ bySeasonData }) {
  if (!bySeasonData) return null

  const data = Object.entries(bySeasonData).map(([season, d]) => ({
    season,
    spend: d.total_spend,
    signings: d.count,
  }))

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '20px 24px',
      boxShadow: 'var(--shadow)',
    }}>
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>Spend by season (£m)</h3>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Total transfer fee outlay per window.</p>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 0, right: 10, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
          <XAxis dataKey="season" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickFormatter={v => `£${v}m`} />
          <Tooltip
            formatter={(val, name) => [`£${val}m`, 'Spend']}
            contentStyle={{ borderRadius: 8, border: '1px solid var(--border)', fontSize: 12 }}
          />
          <Bar dataKey="spend" radius={[4, 4, 0, 0]} isAnimationActive={false}>
            {data.map((_, i) => (
              <Cell key={i} fill="var(--chelsea-blue)" fillOpacity={0.75 + i * 0.07} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
