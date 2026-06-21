#!/usr/bin/env bash
# Build the proxcli website with Remotion animated demos.
# Run from: docs/website/

set -euo pipefail

echo "=== Building Remotion demos ==="
cd remotion-demos

# Render all 5 demos as GIFs (15fps, single loop)
compositions=("vm-list" "vm-show" "node-list" "cluster" "yaml-spec")
for comp in "${compositions[@]}"; do
  echo "  Rendering $comp..."
  npx remotion render "$comp" \
    --codec=gif \
    --every-nth-frame=2 \
    --number-of-gif-loops=0 \
    "../public/demos/${comp}.gif"
done

cd ..

echo ""
echo "=== Building website ==="
npm run build

echo ""
echo "=== Done ==="
echo "Website output: docs/"
echo "Open: docs/index.html"
