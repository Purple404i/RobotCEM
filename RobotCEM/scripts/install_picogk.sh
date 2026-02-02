#!/bin/bash
set -e

echo "🔧 Building PicoGK..."

cd csharp_runtime/submodules/PicoGK
dotnet build -c Release

cd ../../..

echo "✅ PicoGK built successfully!"
