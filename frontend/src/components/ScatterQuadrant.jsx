import React, { useState } from 'react'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Cell, Label
} from 'recharts'

const QUADRANT_COLORS = {
  star: '#1d7a46',
  bargain: '#1a5fa8',
  wasted_spend: '#c0392b',
  deadweight: '#9aa0b4',
}

const QUADRANT_LABELS = {
  star: 'Star signing',
  bargain: 'Bargain',
  wasted_spend: 'Wasted spend',
  deadweight: 'Underperformer',
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '10px 14px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
      minWidth: 180,
    }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{d.name}</div>
      <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 6 }}>
        {d.position} · {d.season}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px 12px', fontSize: 12 }}>
        <span style={{ color: 'var(--text-muted)' }}>Fee</span>
        <span style={{ fontWeight: 600 }}>£{d.fee_million}m</span>
        <span style={{ color: 'var(--text-muted)' }}>Minutes</span>
        <span style={{ fontWeight: 600 }}>{d.minutes_played?.toLocaleString()}</span>
        {/* <span style={{ color: 'var(--text-muted)' }}>xG+xA / 90</span> */}
        {/* <span style={{ fontWeight: 600 }}>{d.xg_xa_per_90}</span> */}
        <span style={{ color: 'var(--text-muted)' }}>Value now</span>
        <span style={{ fontWeight: 600 }}>£{d.market_value_now}m</span>
      </div>
      <div style={{
        marginTop: 8,
        padding: '3px 8px',
        borderRadius: 4,
        background: QUADRANT_COLORS[d.quadrant] + '18',
        color: QUADRANT_COLORS[d.quadrant],
        fontSize: 11,
        fontWeight: 600,
        display: 'inline-block',
      }}>
        {QUADRANT_LABELS[d.quadrant]}
      </div>
    </div>
  )
}

export default function ScatterQuadrant({ data, avgFee, avgUtil }) {
  const [hovered, setHovered] = useState(null)

  const plotData = data.filter(d => d.fee_million > 0)

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
          Fee vs. minutes utilisation
        </h3>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          Each bubble is a paid signing. Dashed lines mark the squad average. Top-left = expensive but unused.
        </p>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 12, flexWrap: 'wrap' }}>
        {Object.entries(QUADRANT_LABELS).map(([key, label]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            <span style={{
              width: 10, height: 10, borderRadius: '50%',
              background: QUADRANT_COLORS[key], flexShrink: 0
            }} />
            <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
          </div>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={360}>
        <ScatterChart margin={{ top: 10, right: 30, bottom: 30, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="minutes_util"
            type="number"
            domain={[0, 100]}
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            label={{ value: 'Minutes utilisation (%)', position: 'insideBottom', offset: -18, fontSize: 12, fill: 'var(--text-secondary)' }}
          />
          <YAxis
            dataKey="fee_million"
            type="number"
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            label={{ value: 'Fee (£m)', angle: -90, position: 'insideLeft', offset: 10, fontSize: 12, fill: 'var(--text-secondary)' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            x={avgUtil}
            stroke="var(--chelsea-gold)"
            strokeDasharray="5 5"
            strokeWidth={1.5}
          />
          <ReferenceLine
            y={avgFee}
            stroke="var(--chelsea-gold)"
            strokeDasharray="5 5"
            strokeWidth={1.5}
          />
          <Scatter data={plotData} isAnimationActive={false}>
            {plotData.map((entry, i) => (
              <Cell
                key={i}
                fill={QUADRANT_COLORS[entry.quadrant] || '#888'}
                fillOpacity={0.85}
                stroke={QUADRANT_COLORS[entry.quadrant] || '#888'}
                strokeWidth={1}
                r={Math.max(5, Math.sqrt(entry.fee_million) * 1.4)}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Player name overlay — shown on hover via separate label pass */}
      <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: -8 }}>
        Bubble size proportional to transfer fee
      </div>
    </div>
  )
}
