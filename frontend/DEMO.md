# Teski Demo Mode

Demo mode lets the frontend run entirely offline with illustrative data for a kiosk-style walkthrough.

## Enable locally
```bash
cd frontend
VITE_DEMO_MODE=true npm run dev
```

## Build a static demo bundle
```bash
cd frontend
VITE_DEMO_MODE=true npm run build
npm run preview   # optional smoke check
```

## Disable after demo day
- Remove `VITE_DEMO_MODE=true` from your environment or `.env` file.
- Rebuild or restart dev server to return to normal backend-connected behavior.
