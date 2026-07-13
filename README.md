# CFC Pocket Watching

**Live dashboard:** https://brave-coast-0e982570f.7.azurestaticapps.net  
**API:** https://chelsea-dashboard-api.onrender.com/docs

A full-stack data dashboard analysing Chelsea FC's transfer efficiency since the BlueCo takeover in 2022. Built to answer a simple question: where has the money actually gone, and has it been worth it?

---

## What it shows

Chelsea have spent over £1.5 billion on transfers since 2022 — more than any club in football history over the same period. This dashboard cuts through the noise and evaluates each signing on the metrics that matter:

- **Fee vs. minutes utilisation** — a quadrant chart separating stars and bargains from wasted spend and underperformers
- **Cost per 90 minutes** — how much each signing has cost per 90 minutes of football, adjusted for fee and playing time
- **Value score** — current market value relative to fee paid, showing which signings have appreciated or depreciated
- **Spend breakdown** — total outlay by season and by position, revealing where recruitment has been concentrated
- **Full signing table** — all 41 BlueCo-era signings with sortable metrics and filters by position, season, and status

---

## Tech stack

- **Frontend** — React (Vite), Recharts · Deployed on Azure Static Web Apps
- **Backend** — FastAPI (Python), Uvicorn, SQLite · Deployed on Render
- **Data** — API-Football for live performance stats · Curated transfer data from public records
- **Scheduler** — APScheduler, weekly automated scrape every Sunday at 3am

---

## Architecture

The project uses a hybrid data architecture:

- `transfers.json` — curated source of truth for all 41 permanent BlueCo signings (fees, statuses, contract details), manually verified against public records
- **API-Football** — live performance stats (minutes, goals, assists) pulled via REST API and stored in SQLite, updated weekly
- **FastAPI** — computes derived metrics (cost per 90, value score, minutes utilisation, profit/loss) on every request

This approach separates concerns cleanly: transfer metadata is stable and curated, performance data is dynamic and automated.

---

## Running locally

You'll need Python 3.11+ and Node.js 18+.

**1. Backend**
```bash
cd backend
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```
API runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

**2. Frontend**
```bash
cd frontend
npm install
npm run dev
```
Dashboard runs at `http://localhost:5173`.

**3. Trigger a scrape**

Hit `POST /scrape` from the docs page to populate live performance stats.

---

## Project structure

```
chelsea-dashboard/
├── backend/
│   ├── main.py           # FastAPI app, endpoints, metric calculations
│   ├── database.py       # SQLite schema and query layer
│   ├── scrapers.py       # API-Football performance scraper + scheduler
│   ├── seed.py           # Seeds transfers.json into the database
│   ├── transfers.json    # Curated BlueCo-era signing data
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx                      # Root component and tab routing
    │   ├── hooks/useApi.js              # Data fetching hooks
    │   └── components/
    │       ├── StatCard.jsx             # Summary metric cards
    │       ├── ScatterQuadrant.jsx      # Fee vs utilisation quadrant chart
    │       ├── CostPer90Chart.jsx       # Cost per 90 bar chart
    │       ├── SpendBySeasonChart.jsx   # Seasonal spend breakdown
    │       ├── PlayerTable.jsx          # Sortable player table
    │       └── FilterBar.jsx            # Position/season/status filters
    └── vite.config.js
```

---

## Key metrics

| Metric | Formula |
|---|---|
| **Cost per 90** | `fee / (minutes / 90)` — lower is more efficient |
| **Value score** | `market_value_now / fee_paid` — >1 means appreciated |
| **Minutes utilisation** | `minutes / (seasons × 3,800)` — proxy for availability |
| **Profit/loss** | `sale_price or market_value − fee_paid` |

---

## Roadmap

- [ ] Custom domain (cfcpocketwatching.com)
- [ ] Swap API-Football for StatsBomb/Opta for full xG and xA data
- [ ] Migrate SQLite to Azure SQL Database for persistent storage
- [ ] Add Azure OpenAI natural language query — ask questions about the data in plain English
- [ ] Individual player radar chart deep-dive
- [ ] Chelsea vs top-six spend efficiency comparison