# Chelsea Transfer Dashboard

A full-stack data dashboard analysing Chelsea FC's transfer efficiency during the BlueCo era (2022–present).
Built to answer a simple question: where has all the money gone and why are we still so mediocre?





## Project structure

```
chelsea-dashboard/
├── backend/
│   ├── main.py           # FastAPI app — all endpoints + metric logic which can be improved
│   ├── transfers.json    # Seeded transfer data (20 Boehly-era signings) because I wanted to see it was running before connecting live data
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx                      # Root component, tab routing
    │   ├── hooks/useApi.js              # Custom hooks for all API calls
    │   └── components/
    │       ├── StatCard.jsx             # Summary metric card
    │       ├── ScatterQuadrant.jsx      # Fee vs utilisation quadrant chart
    │       ├── CostPer90Chart.jsx       # Horizontal bar chart
    │       ├── SpendBySeasonChart.jsx   # Season spend bar chart
    │       ├── PlayerTable.jsx          # Sortable player table
    │       └── FilterBar.jsx            # Position / season / status filters
    ├── vite.config.js    # Proxies /api → FastAPI on :8000
    └── package.json
```


## Setup

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

API runs at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard runs at `http://localhost:5173`.


## Key metrics explained

| Metric | Formula |

| **Cost per 90** | `fee / (minutes / 90)` — lower is more efficient |
| **Value score** | `market_value_now / fee_paid` — >1 means appreciated |
| **Minutes utilisation** | `minutes / (seasons × 3800)` — proxy for availability |
| **xG+xA per 90** | Combined expected goal contributions per 90 minutes |
| **Profit/loss** | `market_value_now − fee_paid` |



## Quadrant classification

Players are bucketed relative to squad averages:

| Quadrant | Fee | Utilisation |
|---|---|---|
| Star | Above avg | Above avg |
| Wasted spend | Above avg | Below avg |
| Bargain | Below avg | Above avg |
| Deadweight | Below avg | Below avg |



## Next steps / extensions

- [ ] Add FBref scraper to pull live performance stats
- [ ] Add Transfermarkt scraper for current market values
- [ ] Persist data in some database
- [ ] Add radar chart for individual player deep-dive
- [ ] Deploy on Render and  Vercel
- [ ] Add comparison mode: Chelsea vs Arsenal/Man City spend efficiency
