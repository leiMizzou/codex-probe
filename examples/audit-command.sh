#!/usr/bin/env bash
set -euo pipefail

# Fill these in or export them before running.
: "${PROVIDER_BASE_URL:?Set PROVIDER_BASE_URL, e.g. https://candidate.example.com/v1}"
: "${PROVIDER_API_KEY:?Set PROVIDER_API_KEY}"

python3 codex_probe.py audit \
  --baseline-id official-sub2api-20x-fast-16c16g-gpt-5.5-xhigh \
  --base-url "$PROVIDER_BASE_URL" \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-vs-official-sub2api-gpt-5.5-xhigh.json
