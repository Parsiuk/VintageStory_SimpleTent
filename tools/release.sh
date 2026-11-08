#!/usr/bin/env bash
# Tag the latest master with the version from modinfo.json.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Working tree is not clean, commit or stash changes first." >&2
    exit 1
fi

git checkout master
git pull --ff-only

VERSION=$(jq -r .version modinfo.json)
TAG="v${VERSION}"

if git rev-parse -q --verify "refs/tags/${TAG}" > /dev/null \
    || git ls-remote --exit-code --tags origin "refs/tags/${TAG}" > /dev/null; then
    echo "Tag ${TAG} already exists, bump version in modinfo.json first." >&2
    exit 1
fi

git tag -a "${TAG}" -m "Release ${TAG}"
echo "Created tag ${TAG}. Push it to trigger the release workflow:"
echo "  git push origin ${TAG}"
