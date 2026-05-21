# Public Alpha Source Manifest - 2026-05-21

Purpose: define what belongs in the v0.1.0-alpha.1 public source/release package.

## Decision

The public alpha package should focus on a source-first DeepHitix release with documented local runtime setup. Docker remains an optional local deployment path, not the primary public artifact.

Default source repository:

```text
https://github.com/xixinw/DeepHitix
```

Do not publish or advertise a large prebuilt Docker image for v0.1.0-alpha.1. The earlier GHCR image attempt used the full upstream Hermes runtime image and produced an unsuitable 8GB-class artifact. The alpha release should publish project source and installation instructions instead.

## Include

```text
README.md
LICENSE
NOTICE.md
THIRD_PARTY_NOTICES.md
ATTRIBUTION.md
TRADEMARKS.md
SECURITY.md
PRIVACY.md
CONTRIBUTING.md
CODE_OF_CONDUCT.md
deploy/
docs/operations/PHASE5_RELEASE_README_CHECKLIST.md
docs/operations/RELEASE_NOTES_v0.1.0-alpha.1.md
docs/operations/REAL_DEEPSEEK_API_SMOKE_2026-05-21.md
docs/operations/DEPENDENCY_LICENSE_SCAN_2026-05-21.md
docs/operations/DOCKER_FEISHU_SMOKE_2026-05-19.md
docs/operations/BRANDING_DECISION_2026-05-21.md
patches/hermes-agent-upstream-series/
```

The actual code source should be clean branch 5:

```text
deepseek-native/0005-cache-observability-hash-prefix-drift-clean
1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c
```

## Exclude from v0.1.0-alpha.1 public package

```text
scripts/whatsapp-bridge/
tmp/
GitHubClone/
deploy/.env
deploy/data/
**/logs/
**/.venv/
**/node_modules/
```

## Why WhatsApp bridge is excluded

The alpha path does not advertise or verify WhatsApp bridge. The dependency license scan found GPL/LGPL entries in `scripts/whatsapp-bridge/package-lock.json`, including `libsignal` and sharp/libvips packages.

Decision for v0.1.0-alpha.1:

```text
Exclude WhatsApp bridge from the public alpha package.
Do not advertise WhatsApp support in the alpha README.
Revisit as a separately reviewed optional component after Docker/API/Feishu release is stable.
```

## Release gate

Do not mark this source manifest complete until the final public repository or source archive is checked against the exclude list.
