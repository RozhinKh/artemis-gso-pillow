#!/usr/bin/env bash
# GSO pillow-simd benchmark wrapper for the Artemis runner.
#
# Runs all 15 tests with eqcheck against the base reference fingerprints and
# writes the summed measured execution time to artemis_results.json.
#
# The bundle (tests/, refs/, images/, sitecustomize.py) is normally baked into
# the runner image at /opt/gso-bundle. When run from a checkout without it,
# falls back to fetching from the GitHub bundle repo.
#
# Runs from the project build directory with .venv already built.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_URL="${GSO_BUNDLE_BASE_URL:-https://raw.githubusercontent.com/RozhinKh/artemis-gso-pillow/main}"
BUNDLE="${GSO_BUNDLE:-$SCRIPT_DIR}"

if [ ! -f "$BUNDLE/refs/gso_0_result.json" ] || [ ! -f "$BUNDLE/sitecustomize.py" ]; then
  BUNDLE="$PWD/gso-bundle"
  mkdir -p "$BUNDLE/tests" "$BUNDLE/refs" "$BUNDLE/images"
  fetch() {  # fetch <url> <dest>, skip when already present
    if [ -f "$2" ]; then
      return 0
    fi
    curl -fsSL "$1?v=1" -o "$2"
  }
  fetch "$BASE_URL/sitecustomize.py" "$BUNDLE/sitecustomize.py"
  fetch "$BASE_URL/images/lenna.png" "$BUNDLE/images/lenna.png"
  fetch "$BASE_URL/images/Fronalpstock_big.jpg" "$BUNDLE/images/Fronalpstock_big.jpg"
  # Reference filenames vary per test script; keep the manifest explicit.
  REFS=(
    gso_0_result.json gso_1_result.json gso_2_result.json gso_3_result.json
    gso_4_reduce_corner_cases.json gso_5_result.json gso_6_reduce_ref.json
    gso_7_reduce_test.json gso_8_result.json gso_9_result.json
    gso_10_reduce_reference.json gso_11_result.json gso_12_reduce_results.json
    gso_13_special_result.json gso_14_reduce_special.json
  )
  for ref in "${REFS[@]}"; do
    fetch "$BASE_URL/refs/$ref" "$BUNDLE/refs/$ref"
  done
  for i in $(seq 0 14); do
    fetch "$BASE_URL/tests/gso_test_$i.py" "$BUNDLE/tests/gso_test_$i.py"
  done
fi

source .venv/bin/activate

times="$(mktemp)"
for i in $(seq 0 14); do
  PYTHONPATH="$BUNDLE" python "$BUNDLE/tests/gso_test_$i.py" "$times" --eqcheck --file_prefix "$BUNDLE/refs/gso_$i"
done

total="$(awk -F'[: s]+' '/Execution time/ {sum += $3} END {printf "%.6f", sum}' "$times")"
rm -f "$times"
printf '{"execution_time_s": %s}\n' "$total" > artemis_results.json
echo "total_execution_time_s=$total"
