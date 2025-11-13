# Vocabulator Dashboard

Teacher/student vocabulary dashboard built with SvelteKit, Bootstrap 5, and Chart.js.

**Note**: This is a P1 feature implementation per `_docs/task-list-p1.md`. This dashboard extends the Vocabulator MVP with an interactive teacher interface, separate from the static HTML reports (Phase 5) hosted on S3.

## Technology Stack

- **Frontend Framework**: SvelteKit with TypeScript
- **UI Framework**: Bootstrap 5
- **Charts**: Chart.js
- **Deployment**: Vercel (via @sveltejs/adapter-vercel)
- **Backend**: FastAPI (existing backend, no changes required)

## Prerequisites

- Node.js 18+
- npm or pnpm
- Access to Vocabulator FastAPI backend (running on localhost:8000 or configured endpoint)

## Environment Variables

Create a `.env` file in the dashboard directory:

```bash
# API Backend URL (required in production)
# For local development, defaults to http://localhost:8000/api/v1 if not set
VITE_API_BASE=http://localhost:8000/api/v1
```

**Important**: In production, `VITE_API_BASE` must be set. The application will fail to start if this variable is missing in production builds.

## Local Development Setup

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables (create `.env` file):
```bash
echo "VITE_API_BASE=http://localhost:8000/api/v1" > .env
```

3. Start the development server:
```bash
npm run dev

# Or open in browser automatically
npm run dev -- --open
```

4. Ensure the FastAPI backend is running and CORS is configured to allow requests from the dashboard origin.

## Building for Production

```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## Deployment to Vercel

1. Push the dashboard directory to your repository
2. Import the project in Vercel
3. Configure environment variables in Vercel dashboard:
   - `VITE_API_BASE`: Your production API URL (e.g., `https://api.vocabulator.com/api/v1`)
4. Deploy

The `@sveltejs/adapter-vercel` adapter automatically configures Vercel deployment settings.

## Backend CORS Configuration

The FastAPI backend must allow CORS requests from the dashboard origin. Ensure your backend CORS configuration includes the dashboard URL:

```python
# In src/api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-dashboard.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # Must include "X-Request-ID" for request correlation
)
```

**Note**: The dashboard sends `X-Request-ID` headers for request correlation. The backend should accept this header in CORS preflight requests.

## Authentication

**Current Status**: Authentication is not implemented in this demo/mock version. This is intentional for the P1 dashboard feature demonstration.

**Production Requirements**: 
- Add authentication mechanism (API keys, JWT tokens, or session cookies)
- Include authentication headers in all API requests
- Backend must require authentication for all endpoints
- CORS configuration must allow authentication headers (e.g., `Authorization`)

## Project Structure

```
dashboard/
├── src/
│   ├── routes/          # SvelteKit routes
│   │   └── +page.svelte # Main dashboard page
│   ├── lib/
│   │   ├── components/  # Reusable Svelte components
│   │   ├── stores.js    # Svelte stores for state management
│   │   ├── api.js       # API utility functions
│   │   └── utils.js     # Helper functions
│   └── data/            # Mock data files (for demo)
├── static/              # Static assets
└── vercel.json          # Vercel deployment config
```

## Mock Data

The `src/data/` directory contains mock data files for demonstration:
- `mockEducator.json`: Teacher/educator information
- `mockClasses.json`: Class information
- `mockAssignments.json`: Sample assignments for testing

These are used to demonstrate functionality without requiring full backend integration.

## Development Status

This dashboard is currently under development. See `_docs/task-list-p1.md` for implementation progress.

**Current Status**: Phase 1 (Project Setup) complete. Components and pages implementation in progress.

## Troubleshooting

### "VITE_API_BASE environment variable is required"
- Ensure `.env` file exists with `VITE_API_BASE` set
- In production, set the environment variable in your deployment platform (Vercel)

### CORS errors when calling API
- Verify backend CORS configuration includes dashboard origin
- Check that backend is running and accessible

### Build fails
- Ensure all dependencies are installed: `npm install`
- Check Node.js version (requires 18+)
- Verify TypeScript configuration is correct
