#!/bin/bash
set -e

echo "🚀 Setting up RobotCEM..."

# Backend setup
echo "📦 Installing backend dependencies..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Frontend setup
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Clone submodules
echo "📦 Cloning LEAP71 submodules..."
cd csharp_runtime/submodules

if [ ! -d "PicoGK" ]; then
  git clone https://github.com/leap71/PicoGK.git
fi

if [ ! -d "LEAP71_ShapeKernel" ]; then
  git clone https://github.com/leap71/LEAP71_ShapeKernel.git
fi

if [ ! -d "LEAP71_LatticeLibrary" ]; then
  git clone https://github.com/leap71/LEAP71_LatticeLibrary.git
fi

cd ../..

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your API keys"
echo "2. Run: cd backend && source venv/bin/activate && uvicorn api.main:app --reload"
echo "3. In another terminal: cd frontend && npm run dev"
