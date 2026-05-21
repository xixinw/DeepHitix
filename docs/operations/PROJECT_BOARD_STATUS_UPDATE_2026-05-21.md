# Project Board Status Update - 2026-05-21

Purpose: correct stale Phase 5 status text that remains in `PROJECT_BOARD.md` from the 2026-05-20 branch-building phase.

## Current Phase

Phase 5: Public Alpha Packaging / Upstream PR Branches.

Current M5 progress: approximately 86%.
Overall project progress: approximately 94%.

## Corrected Status

The upstream PR branch stack is complete in the fresh upstream checkout:

```text
branch 1: deepseek-native/0001-usage-normalization
commit:   ac472ba8f

branch 2: deepseek-native/0002-cost-telemetry-display
commit:   5f562e8a3

branch 3: deepseek-native/0003-flash-pro-routing
commit:   d8fec4b61

branch 4: deepseek-native/0004-context-continuity-extractive-checkpoint-clean
commit:   1725964e6

branch 5: deepseek-native/0005-cache-observability-hash-prefix-drift-clean
commit:   1a8d29bd7
```

Do not use stale refs:

```text
deepseek-native/0004-context-continuity-extractive-checkpoint
deepseek-native/0005-cache-observability-hash-prefix-drift
```

## Latest Verification

Clean branch 5 local verification:

```text
170 passed in 16.05s
```

Docker Compose static validation:

```text
PASS: Docker Compose validation base is structurally sound
```

## Release Packaging Status

Default image coordinates:

```text
ghcr.io/weiha/deepseek-native-agent:v0.1.0-alpha.1
ghcr.io/weiha/deepseek-native-agent:public-alpha
```

Release notes draft:

```text
docs/operations/RELEASE_NOTES_v0.1.0-alpha.1.md
```

Published-image smoke plan:

```text
docs/operations/PUBLISHED_IMAGE_SMOKE_2026-05-21.md
```

Published-image build attempt:

```text
docs/operations/PUBLISHED_IMAGE_BUILD_ATTEMPT_2026-05-21.md
```

Real DeepSeek API smoke:

```text
docs/operations/REAL_DEEPSEEK_API_SMOKE_2026-05-21.md
```

Public alpha source manifest:

```text
docs/operations/PUBLIC_ALPHA_SOURCE_MANIFEST_2026-05-21.md
```

Decision: exclude `scripts/whatsapp-bridge` from v0.1.0-alpha.1 public package until its GPL/LGPL dependency obligations are reviewed.

## Current Blocker

The published-image smoke is ready but not executed. The release candidate image has been built locally on the Linux Docker host and the import probe passed, but push to GHCR failed with a token scope mismatch.

It is now blocked on:

```text
GHCR token with write:packages/read:packages permission for ghcr.io/weiha/deepseek-native-agent
optional Feishu credentials + human tester for Feishu smoke
```

2026-05-21 second token check:

```text
GitHub API identity check: PASS
GHCR docker login: FAIL
reported token scopes: repo
missing scopes: read:packages, write:packages
```

If the final registry owner is the token owner's GitHub account instead of `weiha`, update the image namespace before the next push attempt.

2026-05-21 third token check for `xixinw`:

```text
GitHub API identity check: PASS
reported token scopes include write:packages: YES
reported token scopes include read:packages: NO
GHCR docker login: FAIL
```

No published image success should be claimed until a Linux host has pulled the registry tag and run compose with `--no-build`.
