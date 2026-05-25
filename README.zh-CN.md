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

先用你信任的 provider 生成 baseline：

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

然后测试候选中转：

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
