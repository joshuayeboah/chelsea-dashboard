import React from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '10px 14px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
    }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{d.name}</div>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>
        {d.position} · {d.season}
      </div>
      <div style={{ fontSize: 13 }}>
        <span style={{ color: 'var(--text-muted)' }}>Cost / 90 min: </span>
        <span style={{ fontWeight: 700, color: 'var(--chelsea-blue)' }}>
          £{d.cost_per_90?.toFixed(2)}m
        </span>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
        £{d.fee_million}m fee · {d.minutes_played?.toLocaleString()} mins
      </div>
    </div>
  )
}

export default function CostPer90Chart({ data }) {
  const sorted = [...data]
    .filter(d => d.cost_per_90 !== null && d.fee_million > 0 && d.minutes_played > 0)
    .sort((a, b) => b.cost_per_90 - a.cost_per_90)
    .slice(0, 15)

  const getColor = (val) => {
    if (val > 2) return '#c0392b'
    if (val > 1) return '#d97706'
    return '#1d7a46'
  }

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '20px 24px',
      boxShadow: 'var(--shadow)',
    }}>
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>
          Cost per 90 minutes (£m)
        </h3>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          Fee divided by 90s played. Red = poor value, green = efficient spend.
        </p>
      </div>

      <ResponsiveContainer width="100%" height={340}>
        <BarChart
          data={sorted}
          layout="vertical"
          margin={{ top: 0, right: 30, bottom: 10, left: 90 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            tickFormatter={v => `£${v}m`}
          />
          <YAxis
            dataKey="name"
            type="category"
            tick={{ fontSize: 11, fill: 'var(--text-primary)' }}
            width={88}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="cost_per_90" radius={[0, 4, 4, 0]} isAnimationActive={false}>
            {sorted.map((entry, i) => (
              <Cell key={i} fill={getColor(entry.cost_per_90)} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
