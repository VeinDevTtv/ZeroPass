#!/usr/bin/env bash
set -euo pipefail

TAG=${1:?usage: release.sh vX.Y.Z vYYYYMMDD.1}
DATASET_VERSION=${2:?usage: release.sh vX.Y.Z vYYYYMMDD.1}

echo "Building dataset ${DATASET_VERSION}"
python datasets/pipeline/build.py --version ${DATASET_VERSION} --sources datasets/raw/*.txt --out datasets

echo "Building JS package"
corepack enable || true
pnpm -C packages/javascript install
pnpm -C packages/javascript build

echo "Packaging Python"
pip install -e packages/python
pytest packages/python -q

echo "Release ${TAG} prepared. Attach datasets/${DATASET_VERSION} artifacts to GitHub release."


