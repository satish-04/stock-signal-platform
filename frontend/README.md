# Stock Signal App - Frontend

A modern React-based dashboard for the Stock Signal App platform.

## Features

- 📊 **Dashboard** - Overview of portfolio, performance metrics, and recent signals
- 📈 **Signal Center** - Browse and filter trading signals with confidence scores
- 📊 **Option Chain** - View options with Greeks and market data
- 🔍 **Market Scanner** - Real-time market scanning with filters
- 💼 **Portfolio** - Track positions and P&L performance

## Technology Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling framework
- **TanStack Query** - Data fetching and caching
- **React Router** - Client-side routing

## Development

### Prerequisites

- Node.js 20+
- npm or yarn
- FastAPI backend running on port 8000

### Installation

```bash
cd frontend
npm install
```

### Running Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The production build will be created in the `dist/` directory.

### Linting

```bash
npm run lint
```

## Configuration

Environment variables (`.env.local`):

```env
VITE_API_URL=http://localhost:8000/api
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   │   ├── Navbar.tsx
│   │   └── Sidebar.tsx
│   ├── pages/          # Page components
│   │   ├── DashboardPage.tsx
│   │   ├── SignalCenterPage.tsx
│   │   ├── OptionChainPage.tsx
│   │   ├── MarketScannerPage.tsx
│   │   └── PortfolioPage.tsx
│   ├── lib/            # Utilities and API client
│   │   ├── api.ts      # API client with TanStack Query
│   │   └── types.ts    # TypeScript interfaces and mock data
│   ├── assets/         # Static assets
│   └── main.tsx        # Entry point
├── public/             # Public assets
├── index.html          # HTML template
├── package.json        # Dependencies
├── vite.config.ts      # Vite configuration
└── tailwind.config.js  # Tailwind configuration
```

## API Integration

The frontend connects to the FastAPI backend at `/api`. Available endpoints:

- `GET /api/health` - Health check
- `GET /api/signals` - Get all signals
- `GET /api/options` - Get option chain data
- `GET /api/scanner` - Market scanner results
- `GET /api/portfolio` - Portfolio summary
- `GET /api/positions` - Position history

## Styling

The project uses Tailwind CSS for styling. Custom styles are defined in:

- `src/index.css` - Global styles and utility classes
- Component-specific styles within each component file

## Production Deployment

### Docker Build

```bash
cd frontend
docker build -t stock-signal-app-frontend .
```

### Nginx Configuration

The frontend is served using nginx with:
- Static file caching
- Gzip compression
- API proxy to backend
- SPA fallback for client-side routing

## Environment Setup

For production deployment, set these environment variables:

```bash
VITE_API_URL=https://api.stock-signal-app.example.com
```

## Development Best Practices

1. **Component Structure**: Keep components small and focused
2. **Type Safety**: Use TypeScript for all new components
3. **API Calls**: Use TanStack Query for data fetching
4. **Styling**: Use Tailwind utility classes
5. **Responsive Design**: Mobile-first approach with lg: breakpoints

## Troubleshooting

### Port Already in Use
```bash
# Change port in vite.config.ts
```

### API Connection Failed
Check that the backend is running on `http://localhost:8000`

### Build Errors
```bash
npm run clean
npm install
npm run build
```