# Robot CEM Studio

AI-powered Computational Engineering Model system for robot design.

## Quick Start

```bash
# Run complete setup
./scripts/setup.sh

# Start backend
cd backend
source venv/bin/activate
uvicorn api.main:app --reload

# Start frontend (in new terminal)
cd frontend
npm run dev
```

## Structure

- `backend/` - FastAPI server with CEM engine
- `csharp_runtime/` - PicoGK C# geometry generation
- `frontend/` - React UI with 3D viewer

## Requirements

- Python 3.11+
- Node.js 18+
- .NET 7.0+
- Anthropic API key

## Documentation

See artifacts for complete implementation details.
