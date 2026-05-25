#!/usr/bin/env bash
set -euo pipefail

# Fill these in or export them before running.
: "${PROVIDER_BASE_URL:?Set PROVIDER_BASE_URL, e.g. https://candidate.example.com/v1}"
: "${PROVIDER_API_KEY:?Set PROVIDER_API_KEY}"

python3 provider_probe.py audit \
  --baseline baselines/current-codex-gpt-5.5-xhigh.json \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-gpt-5.5-xhigh-audit.json
