#!/bin/sh
# Downloads the pinned BRouter release ZIP into infra/brouter/.cache/ for the image build.
# Idempotent: an existing archive with the expected SHA-256 is kept. Keep the version and checksum
# in sync with the Dockerfile ARG defaults (enforced by backend/tests/unit/test_brouter_compose.py).
set -eu

BROUTER_VERSION=1.7.10
BROUTER_ZIP_SHA256=023fec3ba997758e8cd7ab9e1bae52e962af3f00b57683e3de86b84ffad01532

HERE=$(cd "$(dirname "$0")" && pwd)
CACHE="$HERE/.cache"
ZIP="$CACHE/brouter-${BROUTER_VERSION}.zip"
URL="https://github.com/abrensch/brouter/releases/download/v${BROUTER_VERSION}/brouter-${BROUTER_VERSION}.zip"

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

mkdir -p "$CACHE"

if [ -f "$ZIP" ] && [ "$(sha256_of "$ZIP")" = "$BROUTER_ZIP_SHA256" ]; then
  echo "BRouter ${BROUTER_VERSION} release already present and verified."
  exit 0
fi

echo "Downloading BRouter ${BROUTER_VERSION} from ${URL}"
curl -fsSL -o "$ZIP.part" "$URL"
if [ "$(sha256_of "$ZIP.part")" != "$BROUTER_ZIP_SHA256" ]; then
  rm -f "$ZIP.part"
  echo "SHA-256 mismatch for BRouter ${BROUTER_VERSION} release; refusing to use it." >&2
  exit 1
fi
mv "$ZIP.part" "$ZIP"
echo "BRouter ${BROUTER_VERSION} release verified."
