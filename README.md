# DeepHitix

DeepSeek-native, cache-hit optimized agent runtime built on Hermes-style workflows.

DeepHitix is an independent open-source project. It is not official Hermes, DeepSeek, Reasonix, or Nous Research software. The project combines Reasonix-inspired cache-hit discipline with Hermes-style agent capabilities so personal users and teams can run a richer DeepSeek-first assistant with visible cost, routing, and cache behavior.

## What It Is

- A DeepSeek-first agent assistant for personal and small-team deployment.
- A cache-aware runtime focused on higher prompt-cache hit rates and lower repeated-context cost.
- A Hermes-derived workflow surface with CLI, gateway, API server, tools, memory, and platform adapter foundations.
- A source-first project: clone it, install dependencies, configure your keys, and run it in your own environment.

## What It Is Not

- Not an official DeepSeek, Hermes, Reasonix, or Nous Research release.
- Not a hosted SaaS.
- Not a prebuilt 8GB runtime image distribution.
- Not a lowest-cost claim. It exposes cost/cache telemetry so you can verify behavior yourself.

## Current Alpha Scope

Verified work so far:

- DeepSeek usage/pricing normalization.
- Cost, cache, latency, and routing telemetry.
- Flash-by-default / Pro-by-exception routing policy.
- Context-continuity fallback for long-running agent work.
- Hash-only cache observability and prefix drift diagnostics.
- API server and Feishu-oriented deployment path.
- Clean upstream patch stack through branch 5.

Deferred:

- Windows native installer.
- Full platform matrix beyond Feishu.
- Public hosted service.
- Large prebuilt Docker image publishing.

## Quick Start: Source Install

Prerequisites:

- Python 3.12.
- Git.
- A DeepSeek API key.

```bash
git clone https://github.com/xixinw/DeepHitix.git
cd DeepHitix
python -m venv .venv
source .venv/bin/activate
pip install -U pip uv
uv pip install -e ".[web]"
```

Create your runtime data directory and config:

```bash
mkdir -p .runtime
cat > .runtime/config.yaml <<'YAML'
model:
  provider: "deepseek"
  default: "deepseek-v4-flash"

deepseek_native:
  routing:
    enabled: true
    flash_model: "deepseek-v4-flash"
    pro_model: "deepseek-v4-pro"
  telemetry:
    enabled: true
YAML
```

Set environment variables:

```bash
export DEEPSEEK_API_KEY="your_deepseek_key"
export HERMES_HOME="$PWD/.runtime"
export HERMES_INFERENCE_PROVIDER=deepseek
export HERMES_MODEL=deepseek-v4-flash
```

Run the agent gateway/API surface:

```bash
hermes gateway run
```

## Optional Docker Compose

Docker is optional and should be built locally by the user. The project does not require downloading a large prebuilt image.

```bash
cd deploy
cp .env.example .env
# edit .env: set DEEPSEEK_API_KEY and API_SERVER_KEY
python3 validate_compose.py
docker compose build deepseek-native-agent
docker compose up -d
curl http://127.0.0.1:8642/health
```

Safe defaults:

- API server binds to `127.0.0.1`.
- Telegram and Weixin are disabled by default.
- Feishu is opt-in.
- Runtime data stays under `deploy/data`.
- `.dockerignore` excludes `.env`, runtime data, logs, and key material.

## Feishu

Feishu is the first verified platform path for the alpha.

See:

```text
docs/operations/FEISHU_DEPLOYMENT.md
docs/operations/DOCKER_FEISHU_SMOKE_2026-05-19.md
```

Required only when enabling Feishu:

```text
FEISHU_ENABLED=true
FEISHU_APP_ID=...
FEISHU_APP_SECRET=...
FEISHU_APP_TYPE=self_built
```

## Telemetry And Privacy

DeepHitix telemetry is intended to expose operational behavior without storing conversation content.

Allowed metadata includes:

- model and provider;
- input/output/cache/reasoning token counts;
- estimated cost;
- latency;
- routing decision and escalation reason;
- hash-only tool schema and immutable-prefix diagnostics.

Telemetry must not record:

- prompt text;
- assistant responses;
- tool outputs;
- API keys, bearer tokens, cookies, passwords, or secrets;
- raw system/developer prompt content;
- old/new prefix text.

## Release Notes

Current alpha release draft:

```text
docs/operations/RELEASE_NOTES_v0.1.0-alpha.1.md
```

Important operational records:

```text
docs/operations/PROJECT_BOARD_STATUS_UPDATE_2026-05-21.md
docs/operations/PUBLIC_ALPHA_SOURCE_MANIFEST_2026-05-21.md
docs/operations/PHASE5_UPSTREAM_BRANCH_EVIDENCE.md
docs/operations/REAL_DEEPSEEK_API_SMOKE_2026-05-21.md
docs/operations/DEPENDENCY_LICENSE_SCAN_2026-05-21.md
docs/operations/BRANDING_DECISION_2026-05-21.md
```

## Upstream Patch Series

Curated Hermes upstream patch candidates live under:

```text
patches/hermes-agent-upstream-series/
```

Current split:

1. Usage normalization and DeepSeek pricing.
2. Main-call cost telemetry and CLI/Gateway display.
3. DeepSeek-native Flash/Pro routing.
4. Context continuity extractive checkpoint fallback.
5. Cache observability hash and prefix drift telemetry.

## License

MIT. See:

```text
LICENSE
NOTICE.md
THIRD_PARTY_NOTICES.md
ATTRIBUTION.md
TRADEMARKS.md
SECURITY.md
PRIVACY.md
```
