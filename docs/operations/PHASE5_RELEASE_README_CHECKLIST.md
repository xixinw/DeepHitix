# Phase 5 Release / README Checklist

Purpose: turn the current engineering proof into a public-alpha package without reopening the core telemetry/routing patch series.

Status as of 2026-05-20: Phase 5 kickoff. M4 is complete; Docker-enabled Linux + Feishu end-to-end smoke has passed. This checklist is the release wrapper, not a new product scope.

## Release objective

Ship a public-alpha quality DeepHitix source repository that a technical user can evaluate in about 30 minutes on a Linux server or Docker host, with clear DeepSeek cost visibility, safe defaults, and no official-affiliation confusion.

## Non-goals for this phase

- Do not implement automatic Flash -> Pro escalation.
- Do not redesign telemetry/routing/context internals.
- Do not expand platform matrix before README/deploy packaging is stable.
- Do not promise Windows native installer yet.
- Do not publish a large prebuilt Docker image for this alpha. Users can build locally from source if they want Docker.

## Current evidence baseline

| Area | Status | Evidence |
|---|---:|---|
| M2 + P0 + M3 regression gate | PASS | `139 passed` on 2026-05-20 |
| Docker Compose static validation | PASS | `python deploy/validate_compose.py` |
| Linux installer syntax | PASS | `bash -n deploy/install.sh` |
| Docker-enabled Linux install/up | PASS | `docs/operations/DOCKER_FEISHU_SMOKE_2026-05-19.md` |
| API `/health` | PASS | same smoke report |
| API chat | PASS | same smoke report |
| Feishu WebSocket | PASS | same smoke report |
| Feishu human-origin inbound reply | PASS | same smoke report |
| Feishu optional deps in project image layer | PASS | `deploy/Dockerfile` + remote import probe |
| Real DeepSeek API smoke | PASS | `docs/operations/REAL_DEEPSEEK_API_SMOKE_2026-05-21.md` |
| Remote release host prep | PASS | `docs/operations/REMOTE_RELEASE_PREP_2026-05-21.md` |
| Public alpha source archive | PASS | `docs/operations/PUBLIC_ALPHA_SOURCE_MANIFEST_2026-05-21.md` |
| Release candidate image local build | PASS | `docs/operations/PUBLISHED_IMAGE_BUILD_ATTEMPT_2026-05-21.md` |
| Release candidate image import probe | PASS | `docs/operations/PUBLISHED_IMAGE_BUILD_ATTEMPT_2026-05-21.md` |
| Public source repository | IN PROGRESS | Source-first release replaces unsuitable large prebuilt image path |
| Published registry tag | DROPPED FOR ALPHA | 8GB-class upstream-runtime image is not acceptable for v0.1.0-alpha.1 |
| Published-image smoke plan | SUPERSEDED | Source repository + local build instructions are the alpha path |

## README acceptance criteria

The root README is release-ready only when it answers these in the first screen or first two sections:

- What this is: DeepSeek-native, cost-visible, self-hosted Agent assistant.
- What this is not: not official Hermes / DeepSeek / Reasonix.
- Who it is for: personal developers, small teams, domestic-cloud users.
- Fastest path: Docker Compose quick start.
- Verified path: Linux systemd + Feishu guide.
- Required secrets: `DEEPSEEK_API_KEY`, `API_SERVER_KEY`, optional `FEISHU_*`.
- Safety defaults: API bound to localhost, Telegram/Weixin disabled, Feishu opt-in.
- Cost/privacy contract: telemetry records token/cost/cache/model metadata, not prompt/response/tool content.
- Current alpha limitations: no Windows native installer, no platform matrix beyond Feishu, registry tag pending until tested.

## Release artifact checklist

### Documentation

- [x] Root README refreshed from initiation-stage text to public-alpha orientation.
- [x] Docker deployment README exists: `deploy/README.md`.
- [x] Linux deployment guide exists: `docs/operations/LINUX_DEPLOYMENT.md`.
- [x] Feishu guide exists: `docs/operations/FEISHU_DEPLOYMENT.md`.
- [x] Windows feasibility doc exists: `docs/operations/WINDOWS_PACKAGING_FEASIBILITY.md`.
- [x] Docker + Feishu smoke report exists: `docs/operations/DOCKER_FEISHU_SMOKE_2026-05-19.md`.
- [x] Add release notes for first alpha tag after tag name is chosen: `docs/operations/RELEASE_NOTES_v0.1.0-alpha.1.md`.
- [x] Record short-name branding recommendation: `docs/operations/BRANDING_DECISION_2026-05-21.md`.
- [ ] Add final 30-minute README walkthrough evidence after running against the release tag, not just local build.

### Packaging

- [x] `deploy/docker-compose.yml` exists and defaults to API-only safe mode.
- [x] `deploy/Dockerfile` builds a project-owned thin image layer on top of upstream Hermes.
- [x] `deploy/.dockerignore` excludes `.env`, data, logs, and key material.
- [x] `deploy/install.sh` materializes DeepSeek runtime config and builds before service start.
- [x] systemd user unit exists.
- [x] Decide public product name: DeepHitix.
- [x] Prepare public alpha source tree/archive excluding WhatsApp bridge and runtime artifacts.
- [x] Stage source archive and release scripts on Linux Docker host.
- [x] Build release candidate image from prepared clean branch 5 source package.
- [x] Run release candidate image local import probe.
- [ ] Push public alpha source repository.
- [ ] Verify source repository clone/install instructions.

2026-05-21 correction: the release should not be centered on GHCR image coordinates. The earlier prebuilt image path pulled in the full upstream Hermes runtime and produced an unsuitable 8GB-class artifact.

```text
source repo: https://github.com/xixinw/DeepHitix
```

The alpha release should publish source and environment instructions. Docker remains optional for users who want to build locally.

### Compliance / safety

- [x] `LICENSE` exists.
- [x] `NOTICE.md` exists.
- [x] `THIRD_PARTY_NOTICES.md` exists.
- [x] Confirm `ATTRIBUTION.md`, `TRADEMARKS.md`, `SECURITY.md`, `PRIVACY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` before public repo launch.
- [x] Run local secret pattern scan before publishing: `docs/operations/RELEASE_HYGIENE_2026-05-21.md`.
- [x] Run dependency license scan before publishing: `docs/operations/DEPENDENCY_LICENSE_SCAN_2026-05-21.md`.
- [x] Resolve `scripts/whatsapp-bridge` alpha handling: exclude from v0.1.0-alpha.1 public package via `docs/operations/PUBLIC_ALPHA_SOURCE_MANIFEST_2026-05-21.md`.
- [ ] Resolve or document remaining Node unknown license entries before public source launch.
- [x] Confirm README avoids official-affiliation confusion, absolute lowest-cost claims, and unsupported benchmark claims.

### Upstream PR branches

- [x] Patch series exists under `patches/hermes-agent-upstream-series/`.
- [x] PR drafts exist in `docs/operations/M4_UPSTREAM_PR_DRAFTS.md`.
- [x] Fresh apply evidence exists for 0001 -> 0005.
- [x] Create PR branch 1 from clean Hermes upstream and apply/reconstruct `0001`.
- [x] Create PR branch 2 from branch 1 and apply/port `0002`.
- [x] Create PR branch 3 from branch 2 and apply/port `0003`.
- [x] Create PR branch 4 from branch 3 and apply/port `0004` using clean ref.
- [x] Create PR branch 5 from branch 4 and apply/port `0005` using clean ref.
- [x] Run targeted tests per branch.
- [ ] Only open PRs after branch/test evidence is refreshed.

## 30-minute README walkthrough script

Use this as the release candidate verification path on a clean Linux host:

```bash
git clone <release-repo-url> deepseek-native-agent
cd deepseek-native-agent/deploy
cp .env.example .env
# edit .env:
#   DEEPSEEK_API_KEY=...
#   API_SERVER_KEY=<openssl rand -hex 32>
# optional Feishu fields only if testing Feishu
python3 validate_compose.py
docker compose config
docker compose build deepseek-native-agent
docker compose up -d
curl http://127.0.0.1:8642/health
docker compose logs --tail=120 deepseek-native-agent
```

Expected result:

- Compose config renders without unsafe defaults.
- Container healthcheck becomes healthy.
- `/health` returns successfully.
- Logs show DeepSeek provider/config materialized.
- If Feishu is enabled, logs show WebSocket connected and a human-origin DM can receive a reply.

## Fishbone position

```text
DeepSeek Native Agent Public Alpha
├─ Core Agent
│  ├─ Telemetry first ✅
│  ├─ Flash/Pro routing ✅
│  └─ Context continuity fallback ✅
├─ Observability
│  ├─ Cost/cache JSONL ✅
│  ├─ CLI/Gateway summary ✅
│  └─ Hash-only cache diagnostics ✅
├─ Packaging  ← current Phase 5 focus
│  ├─ Docker Compose ✅
│  ├─ Linux systemd ✅
│  ├─ Feishu guide/smoke ✅
│  ├─ README release wrapper ✅
│  └─ Registry tag smoke ⏳
├─ Upstream Hygiene
│  ├─ Patch series ✅
│  ├─ PR drafts ✅
│  └─ PR branches ⏳
└─ Platform Expansion
   ├─ Feishu ✅
   ├─ WeCom later ⏳
   └─ Weixin/Telegram/Discord/Slack deferred
```

## Next recommended action

Create upstream PR branches from a clean Hermes upstream checkout and apply the curated series one branch at a time. Do not modify core patch content unless a branch test fails.
