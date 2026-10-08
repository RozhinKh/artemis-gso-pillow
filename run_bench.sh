#!/usr/bin/env bash
# GSO pillow-simd benchmark wrapper for the Artemis runner.
#
# Fetches the bundle (test scripts, base reference fingerprints, fixture
# images), runs all 15 tests with eqcheck against the base references, and
# writes the summed measured execution time to artemis_results.json.
#
# Runs from the project build directory with .venv already built.
set -euo pipefail

BASE_URL="${GSO_BUNDLE_BASE_URL:-https://raw.githubusercontent.com/RozhinKh/artemis-gso-pillow/main}"
BUNDLE="gso-bundle"

mkdir -p "$BUNDLE/tests" "$BUNDLE/refs" "$BUNDLE/images"

fetch() {  # fetch <url> <dest>, skip when already present
  if [ -f "$2" ]; then
    return 0
  fi
  curl -fsSL "$1" -o "$2"
}

fetch "$BASE_URL/sitecustomize.py" "$BUNDLE/sitecustomize.py"
fetch "$BASE_URL/images/lenna.png" "$BUNDLE/images/lenna.png"
fetch "$BASE_URL/images/Fronalpstock_big.jpg" "$BUNDLE/images/Fronalpstock_big.jpg"
for i in $(seq 0 14); do
  fetch "$BASE_URL/tests/gso_test_$i.py" "$BUNDLE/tests/gso_test_$i.py"
  fetch "$BASE_URL/refs/gso_${i}_result.json" "$BUNDLE/refs/gso_${i}_result.json"
done

source .venv/bin/activate

times="$(mktemp)"
for i in $(seq 0 14); do
  PYTHONPATH="$PWD/$BUNDLE" python "$BUNDLE/tests/gso_test_$i.py" "$times" --eqcheck --file_prefix "$BUNDLE/refs/gso_$i"
done

total="$(awk -F'[: s]+' '/Execution time/ {sum += $3} END {printf "%.6f", sum}' "$times")"
rm -f "$times"
printf '{"execution_time_s": %s}\n' "$total" > artemis_results.json
echo "total_execution_time_s=$total"
