import React, { useState } from 'react'
import { useTransfers, useSummary, useQuadrants } from './hooks/useApi'
import StatCard from './components/StatCard'
import ScatterQuadrant from './components/ScatterQuadrant'
import CostPer90Chart from './components/CostPer90Chart'
import SpendBySeasonChart from './components/SpendBySeasonChart'
import PlayerTable from './components/PlayerTable'
import FilterBar from './components/FilterBar'

const TABS = ['Overview', 'Quadrant analysis', 'Cost efficiency', 'All signings']

function formatMoney(millions) {
  if (millions === null || millions === undefined) return '—'
  const abs = Math.abs(millions)
  const sign = millions < 0 ? '-' : ''
  if (abs >= 1000) {
    return `${sign}£${(abs / 1000).toFixed(1)}b`
  }
  return `${sign}£${Math.round(abs)}m`
}

function LoadingSpinner() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200, color: 'var(--text-muted)', fontSize: 14 }}>
      Loading...
    </div>
  )
}

export default function App() {
  const [activeTab, setActiveTab] = useState('Overview')
  const [filters, setFilters] = useState({})

  const { data: transfers, loading: tLoading } = useTransfers(filters)
  const { data: summary, loading: sLoading } = useSummary()
  const { data: quadrants, loading: qLoading } = useQuadrants()

  const totalSpend = summary?.total_spend_million
  const totalValue = summary?.total_current_value_million
  const profitLoss = summary?.total_profit_loss_million

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Header */}
      <header style={{
        background: 'var(--chelsea-blue)',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        height: 56,
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%',
            background: 'rgba(255,255,255,0.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16,
          }}>
            ⚽
          </div>
          <div>
            <div style={{ color: '#fff', fontWeight: 700, fontSize: 15, lineHeight: 1.2 }}>
              Chelsea FC
            </div>
            <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: 11 }}>
              Transfer dashboard · BlueCo era
            </div>
          </div>
        </div>

        <nav style={{ marginLeft: 32, display: 'flex', gap: 4 }}>
          {TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '6px 14px',
                borderRadius: 6,
                border: 'none',
                background: activeTab === tab ? 'rgba(255,255,255,0.2)' : 'transparent',
                color: activeTab === tab ? '#fff' : 'rgba(255,255,255,0.6)',
                fontSize: 13,
                fontWeight: activeTab === tab ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {tab}
            </button>
          ))}
        </nav>
      </header>

      <main style={{ maxWidth: 1280, margin: '0 auto', padding: '24px 24px 48px' }}>

        {/* OVERVIEW TAB */}
        {activeTab === 'Overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {sLoading ? <LoadingSpinner /> : (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14 }}>
                  <StatCard
                    label="Total spend"
                    value={formatMoney(totalSpend)}
                    sub="Since BlueCo takeover 2022"
                    color="var(--chelsea-blue)"
                  />
                  <StatCard
                    label="Current squad value"
                    value={formatMoney(totalValue)}
                    sub="Combined market value"
                    color="var(--chelsea-blue)"
                  />
                  <StatCard
                    label="Net value change"
                    value={formatMoney(profitLoss)}
                    sub="vs fees paid"
                    color={profitLoss >= 0 ? 'var(--green)' : 'var(--red)'}
                  />
                  <StatCard
                    label="Signings"
                    value={summary?.signings_count}
                    sub="Paid + free transfers"
                    color="var(--chelsea-blue)"
                  />
                  <StatCard
                    label="Injury/underuse flags"
                    value={summary?.injured_underutilised_count}
                    sub="Below 40% utilisation"
                    color="var(--red)"
                  />
                  <StatCard
                    label="Avg cost per 90"
                    value={summary?.avg_cost_per_90_thousand ? formatMoney(summary.avg_cost_per_90_thousand / 1000) : '—'}
                    sub="Among paid signings"
                    color="var(--amber)"
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <SpendBySeasonChart bySeasonData={summary?.by_season} />
                  <div style={{
                    background: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius)',
                    padding: '20px 24px',
                    boxShadow: 'var(--shadow)',
                  }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 14 }}>Spend by position</h3>
                    {summary?.by_position && Object.entries(summary.by_position).map(([group, d]) => (
                      <div key={group} style={{ marginBottom: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 13 }}>
                          <span style={{ fontWeight: 600 }}>{group}</span>
                          <span style={{ color: 'var(--text-secondary)' }}>{formatMoney(d.total_spend)} · {d.count} players</span>
                        </div>
                        <div style={{ height: 8, background: 'var(--surface-2)', borderRadius: 4, overflow: 'hidden' }}>
                          <div style={{
                            width: `${Math.min((d.total_spend / totalSpend) * 100, 100)}%`,
                            height: '100%',
                            background: 'var(--chelsea-blue)',
                            borderRadius: 4,
                            opacity: 0.7,
                          }} />
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                          Avg utilisation: {d.avg_minutes_util}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* QUADRANT TAB */}
        {activeTab === 'Quadrant analysis' && (
          qLoading ? <LoadingSpinner /> : quadrants ? (
            <ScatterQuadrant
              data={quadrants.players}
              avgFee={quadrants.avg_fee_benchmark}
              avgUtil={quadrants.avg_util_benchmark}
            />
          ) : null
        )}

        {/* COST EFFICIENCY TAB */}
        {activeTab === 'Cost efficiency' && (
          tLoading ? <LoadingSpinner /> : (
            <CostPer90Chart data={transfers} />
          )
        )}

        {/* ALL SIGNINGS TAB */}
        {activeTab === 'All signings' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <FilterBar filters={filters} onChange={setFilters} />
            {tLoading ? <LoadingSpinner /> : <PlayerTable data={transfers} />}
          </div>
        )}
      </main>
      <footer style={{
  borderTop: '1px solid var(--border)',
  padding: '12px 24px',
  textAlign: 'center',
  fontSize: 11,
  color: 'var(--text-muted)',
}}>
  Performance stats via API-Football · 2025-26 season data updates weekly · Historical stats reflect Premier League appearances only · Transfer fees sourced from public records
</footer>
    </div>
  )
}