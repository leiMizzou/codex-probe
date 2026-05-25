# Codex Probe

<p align="right">
  <a href="README.zh-CN.md">简体中文</a> |
  <a href="README.md#english">English</a>
</p>

用于黑盒评估 OpenAI-compatible 中转站 / API 网关 / 模型代理是否“纯净”的命令行工具。推荐把你当前 Codex App 使用的官方/可信 provider 作为 baseline，再拿同一套题和指标去测第三方中转。

它的目标不是证明上游账号到底是 Free、Plus 还是 Pro，而是用同一套复杂题和功能探针，对比一个可信 baseline，判断候选 provider 是否存在：

- 质量明显下降
- 输入 token 被隐藏包装放大
- 多路由 / 多适配器切换
- 疑似混用较弱模型
- `gpt-image-2`、snapshot model 等功能缺失
- 计费或 token 统计异常
- median latency、p90 latency、输出 token/s 明显劣化

## 基本流程

可以直接使用仓库内置的参考基线：

```bash
python3 codex_probe.py list-baselines
```

然后测试候选中转：

```bash
export PROVIDER_BASE_URL="https://candidate.example.com/v1"
export PROVIDER_API_KEY="sk-..."

python3 codex_probe.py audit \
  --baseline-id official-sub2api-20x-fast-16c16g-gpt-5.5-xhigh \
  --base-url "$PROVIDER_BASE_URL" \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-vs-official-sub2api-gpt-5.5-xhigh.json
```

如果你更信任自己的环境，也可以先生成自己的 baseline：

```bash
python3 codex_probe.py baseline \
  --current-codex \
  --profile codex-fast \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output baselines/current-codex-gpt-5.5-xhigh.json
```

再用自己的 baseline 测试候选中转：

```bash
export PROVIDER_BASE_URL="https://candidate.example.com/v1"
export PROVIDER_API_KEY="sk-..."

python3 codex_probe.py audit \
  --baseline baselines/current-codex-gpt-5.5-xhigh.json \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-gpt-5.5-xhigh-audit.json
```

报告会输出这些分数：

```text
quality_score
wrapper_or_routing_suspicion
model_substitution_suspicion
billing_overhead_suspicion
feature_gap_suspicion
speed_suspicion
profile_comparison
overall_risk
```

## 内置参考基线

仓库内置了一份可直接比较的参考基线：

```text
id: official-sub2api-20x-fast-16c16g-gpt-5.5-xhigh
```

这份基线的背景配置：

- 生成时间：2026-05-25 13:54:32 UTC。
- Provider：自建 `sub2api` relay，base URL 为 `https://20x-fast-2.111138.xyz/v1`。
- 服务器：16C16G VPS。
- 模型：`gpt-5.5`。
- 推理强度：`xhigh`。
- 测试设置：`hard-v1` 题库，16 个 case，每题重复 2 次，`temperature=0`，包含 `gpt-image-2` 探针。
- 基线结果：`32/32` 通过，input `2770`，output `4052`，total `6822`，median latency `5.9155s`，p90 latency `8.9552s`。
- 功能结果：`gpt-image-2` 可用并返回 `b64_json`；snapshot `gpt-5.5-2026-04-23` 可用；`/models` 中列出 9 个模型 ID。

这不是 OpenAI 官方发布的标准成绩，也不能证明某个候选服务的上游账号类型。它是一份固定的、已脱敏的黑盒参考样本，方便使用者拿同一套题直接对比 token、功能、速度和输出质量。

## 案例：agnx 对比内置基线

用这份内置基线测试当前 Codex 配置里的 `https://www.agnx.run/v1`、`gpt-5.5`、`xhigh`，结果如下。数字来自 2026-05-25 15:48:14 UTC 的重测报告。

这个候选服务的购买入口：[通过当前 `gpt-5.5` + `xhigh` hard-v1 对比测试的候选服务](https://pay.ldxp.cn/shop/7TD7O3QI)。本轮测试里它文本质量全通过，延迟接近内置基线，作为 `gpt-5.5` xhigh 文本调用可用；但它不是全功能等价 provider，存在明显 input token / 成本开销，且 `gpt-image-2` 与 `gpt-5.5-2026-04-23` snapshot 不可用或失败。实际价格、库存、权限、稳定性、并发限制和售后以商家页面为准。

```text
Pass rate: baseline=1.0, candidate=1.0, delta=0.0
Token ratio candidate/baseline: input=4.0058, output=0.9817, total=2.2096
Estimated cost ratio: 1.291
Speed candidate/baseline: median_latency_ratio=0.9683, p90_latency_ratio=1.0582, output_tokens_per_s_ratio=0.7709
Profile match: verdict=unlikely_match, confidence=49.0
Assessment: verdict=passes_text_quality_but_provider_differs, risk_level=high, quality_gate_passed=True

quality_score: 100/100
wrapper_or_routing_suspicion: 70/100
model_substitution_suspicion: 0/100
billing_overhead_suspicion: 100/100
feature_gap_suspicion: 55/100
speed_suspicion: 0/100
overall_risk: 45.75/100
```

解读：两边质量都满分，没有弱模型替换信号；但候选服务 input token 明显更高，并形成 `+335` 左右的固定档位，说明存在隐藏 wrapper、适配器或路由差异的可能性。候选 `/models` 返回 17 个 ID，并包含若干 `gpt-5.*` / Codex 名称，但本轮只验证了 `gpt-5.5` 文本；`gpt-image-2` 返回 403，snapshot `gpt-5.5-2026-04-23` 返回 503。

## 分数解释

- `quality_score`: 复杂客观题正确率。
- `wrapper_or_routing_suspicion`: 是否出现固定 input token 档位，比如有时多 `+335 tokens`。
- `model_substitution_suspicion`: 是否可能混入弱模型。主要看难题是否掉分，以及不同 token 档位是否正确率不同。
- `billing_overhead_suspicion`: token / 成本是否明显高于 baseline。
- `feature_gap_suspicion`: `gpt-image-2`、snapshot model、JSON schema 等功能是否缺失。
- `speed_suspicion`: median latency、p90 latency、输出 token/s 是否明显差于 baseline。
- `profile_comparison`: 如果 baseline 用 `--profile codex-fast` 标注，会输出候选是否匹配这个 Codex Fast baseline。
- `overall_risk`: 综合风险。

## Codex Fast 判断

这个工具不能从黑盒 API 里证明对方内部真的用了 Codex Fast 模式；它能判断的是：候选中转是否像你信任的 Codex Fast baseline。

生成基线时标注 profile：

```bash
python3 codex_probe.py baseline \
  --current-codex \
  --profile codex-fast \
  --model gpt-5.5 \
  --repeats 3 \
  --reasoning-effort xhigh \
  --output baselines/current-codex-fast-gpt-5.5-xhigh.json
```

之后 audit 报告会输出：

```text
Profile match: verdict=matches_baseline_profile, confidence=...
```

如果你要区分 Fast 和更慢/更深的模式，就分别生成两个 baseline，例如 `--profile codex-fast` 和 `--profile codex-deep`，同一个候选中转分别 audit 两次，看它更接近哪一个。

## 速度测试

工具会为每次 chat completion 记录总耗时，并在 baseline 和 audit 报告中汇总：

- median latency
- p90 latency
- median output tokens/s
- candidate/baseline 速度比

速度本身不是“掺水”的直接证据，但它有辅助鉴别力。一个中转如果明显慢于当前 Codex App baseline，可能是链路更长、上游拥塞、额外 wrapper、或者路由到了不同的上游；如果速度很快，也不能单独说明有问题，需要结合正确率、功能、token 和输出稳定性一起看。

## 重要限制

- 这是黑盒启发式评估，不是密码学证明。
- 中转站可以伪造返回的 model 名。
- API 行为无法可靠证明上游是 ChatGPT Free / Plus / Pro / Team。
- `gpt-image-2` 能不能用，更多说明 API/project/group 权限，不直接说明 ChatGPT 订阅等级。
- token 数是 provider 返回的，可能包含隐藏 prompt、适配器包装或计费层开销。
- 本项目是非官方工具，不隶属于 OpenAI。
