# Provider Probe

Black-box audit tooling for OpenAI-compatible model providers and API gateways.

Provider Probe helps you compare a candidate API endpoint against a trusted baseline and answer practical questions:

- Is the claimed model behaving close to the baseline on hard deterministic tasks?
- Does the provider inject hidden prompt/wrapper tokens?
- Is there evidence of mixed routing or weaker model substitution?
- Are expected capabilities missing, such as `gpt-image-2` or snapshot model IDs?
- How different are reported token usage and estimated cost?

It is designed for testing third-party "OpenAI-compatible" gateways, proxy providers, and model resellers. It does **not** prove the upstream account type, and it cannot definitively prove Free / Plus / Pro / Team usage. It reports observable evidence and risk scores.

## What It Tests

The built-in hard suite includes deterministic prompts for:

- Python and JavaScript execution reasoning
- Critical path scheduling
- Weighted graph shortest path with tie-breaking
- Decoy retrieval
- SQL-style aggregation
- Conditional probability
- Mini DSL interpretation
- Calendar arithmetic
- Instruction-injection resistance
- Strict JSON output
- Bug localization
- Impossible-constraint detection
- Nested JSON extraction
- Base conversion
- Stable repetition formatting

See [model_substitution_hard_suite.md](model_substitution_hard_suite.md) for the full prompt suite.

## Install

Requires Python 3.10+. Python 3.11+ is recommended if you want `--current-codex` baseline generation from `~/.codex/config.toml`.

Run directly:

```bash
python3 provider_probe.py --help
```

Or install as a local CLI:

```bash
python3 -m pip install -e .
provider-probe --help
```

## 1. Build A Trusted Baseline

If you use Codex locally and trust its configured provider:

```bash
python3 provider_probe.py baseline \
  --current-codex \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output baselines/current-codex-gpt-5.5-xhigh.json
```

`--image-probe` calls `gpt-image-2` and may consume image credits if enabled.

You can also build a baseline from explicit endpoint credentials:

```bash
export PROVIDER_BASE_URL="https://trusted.example.com/v1"
export PROVIDER_API_KEY="sk-..."

python3 provider_probe.py baseline \
  --base-url "$PROVIDER_BASE_URL" \
  --api-key "$PROVIDER_API_KEY" \
  --label trusted \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --output baselines/trusted-gpt-5.5-xhigh.json
```

## 2. Audit A Candidate Provider

```bash
export PROVIDER_BASE_URL="https://candidate.example.com/v1"
export PROVIDER_API_KEY="sk-..."

python3 provider_probe.py audit \
  --baseline baselines/current-codex-gpt-5.5-xhigh.json \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-gpt-5.5-xhigh-audit.json
```

The saved report is redacted. API keys are not written to output files.

## Scores

Reports include:

- `quality_score`: correctness on the hard deterministic suite.
- `wrapper_or_routing_suspicion`: fixed input-token overhead tiers, likely hidden wrappers or different adapters.
- `model_substitution_suspicion`: risk of weaker/mixed model routing based on quality drops or one token tier failing more often.
- `billing_overhead_suspicion`: candidate uses much more input/total token budget than baseline.
- `feature_gap_suspicion`: missing or different features compared with baseline.
- `overall_risk`: weighted summary of routing, substitution, billing, and feature issues.

Example:

```text
quality_score: 100/100
wrapper_or_routing_suspicion: 70/100
model_substitution_suspicion: 0/100
billing_overhead_suspicion: 100/100
feature_gap_suspicion: 55/100
overall_risk: 54.25/100
```

## Reading Token Clusters

A clean provider should usually have input token counts close to the baseline for the same prompt.

If the candidate forms stable clusters like:

```text
+0 input tokens
+335 input tokens
```

that is strong evidence of hidden wrapper/routing differences. If both clusters pass the hard suite, this points more toward adapter/wrapper overhead than weaker model substitution. If one cluster fails more often, mixed or weaker upstream routing becomes more suspicious.

## Limitations

- This is a black-box heuristic audit, not cryptographic proof.
- Providers can spoof returned model names.
- API behavior cannot reliably identify ChatGPT Free / Plus / Pro / Team account type.
- Image generation success or failure reflects API/project/group permission, not necessarily ChatGPT subscription.
- Token counts are provider-reported and may include hidden prompt, adapter, or billing-layer overhead.

## Repository Hygiene

Generated baselines, audit reports, local images, and Python caches are ignored by default. Do not commit real API keys or private provider reports unless you have reviewed and redacted them.
