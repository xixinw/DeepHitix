# Release Notes - v0.1.0-alpha.1 Draft

Status: draft. Do not publish until the registry image tag is pushed and verified by a Linux Docker smoke.

## Release identity

```text
release tag:       v0.1.0-alpha.1
image tag:         ghcr.io/weiha/deepseek-native-agent:v0.1.0-alpha.1
moving alpha tag:  ghcr.io/weiha/deepseek-native-agent:public-alpha
source branch:     deepseek-native/0005-cache-observability-hash-prefix-drift-clean
source commit:     1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c
```

If the final GitHub owner differs from `weiha`, update the image namespace before publishing.

## What this alpha is

DeepSeek Native Agent combines two product directions:

- Reasonix-inspired cache-hit discipline for lower-cost, more stable DeepSeek usage.
- Hermes Agent's broad agent runtime, tools, gateway, and third-party platform connectivity.

The alpha is meant for technical users who want a self-hosted personal or small-team agent that can be deployed on a Linux/Docker host, with cost/cache behavior visible instead of hidden.

## Highlights

- DeepSeek usage normalization and current DeepSeek pricing coverage.
- Main-call JSONL cost telemetry with token, cache, latency, and model metadata.
- Flash-by-default and explicit one-shot `/pro` routing.
- Auxiliary text/compression tasks default back to Flash under DeepSeek-native routing.
- Context compression fallback preserves operational continuity when summary generation fails.
- Cache observability emits hash-only diagnostics for tool schema and immutable prefix drift.
- Docker Compose deployment base with safe defaults.
- Linux systemd install path.
- Feishu gateway deployment guide and verified Docker/Feishu smoke evidence.

## Privacy and safety contract

Telemetry is allow-list based. It may record model/provider, token counts, cache counts, estimated cost, latency, routing decisions, and hash-only cache diagnostics.

Telemetry must not record prompt text, assistant responses, tool outputs, API keys, bearer tokens, cookies, passwords, raw system/developer prompt content, tool schema body, or old/new prefix text.

## Verified before this draft

```text
clean branch 5 regression gate: 170 passed in 16.05s
Docker Compose static validation: PASS
Docker-enabled Linux smoke: PASS
API /health: PASS
API chat: PASS
Feishu WebSocket: PASS
Feishu human-origin inbound reply: PASS
Real DeepSeek API smoke: PASS
```

Evidence:

```text
docs/operations/PHASE5_UPSTREAM_BRANCH_EVIDENCE.md
docs/operations/DOCKER_FEISHU_SMOKE_2026-05-19.md
docs/operations/REAL_DEEPSEEK_API_SMOKE_2026-05-21.md
docs/operations/PUBLISHED_IMAGE_SMOKE_2026-05-21.md
```

## Not verified yet

- Published registry image tag.
- Pulling the published image on a Linux host and running compose with `--no-build`.
- Windows native installer.
- Platform matrix beyond Feishu.

## Known release blocker

Publishing requires:

```text
registry owner/namespace
registry token with package push permission
Linux Docker host for build/push/pull smoke
DeepSeek API key for API chat smoke
optional Feishu credentials + human tester for Feishu smoke
```

Do not call this release complete until the published image tag has been pulled and smoke-tested.
