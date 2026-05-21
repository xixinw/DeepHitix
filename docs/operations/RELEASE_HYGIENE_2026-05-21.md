# Release Hygiene Check - 2026-05-21

Purpose: capture the local pre-publication checks that can be completed without registry credentials or a Docker host.

## Scope

Checked local project materials under:

```text
D:/Hermes_save/deepseek-native-agent
```

Excluded from secret scanning:

```text
tmp/**
GitHubClone/**
**/.git/**
**/.env
**/data/**
**/logs/**
```

Reason: these areas may contain generated worktrees, runtime state, or intentionally untracked secret-bearing env files.

## Compliance files

Present:

```text
ATTRIBUTION.md
TRADEMARKS.md
SECURITY.md
PRIVACY.md
CONTRIBUTING.md
CODE_OF_CONDUCT.md
LICENSE
NOTICE.md
THIRD_PARTY_NOTICES.md
docs/compliance/OPEN_SOURCE_COMPLIANCE_PLAN.md
```

Assessment:

- The required public-release compliance stubs exist.
- `TRADEMARKS.md` and README both state that the project is not official Hermes, DeepSeek, or Reasonix.
- `SECURITY.md` and `PRIVACY.md` are sufficient for a self-hosted alpha, but should be expanded before any hosted service or remote telemetry feature.
- Dependency license scan completed separately in `docs/operations/DEPENDENCY_LICENSE_SCAN_2026-05-21.md`.

## Secret scan

Command used:

```powershell
rg -n "DEEPSEEK_API_KEY=.+|API_SERVER_KEY=.+|FEISHU_APP_SECRET=.+|FEISHU_APP_ID=cli_|sk-[A-Za-z0-9_-]{12,}|xox[baprs]-[A-Za-z0-9-]+|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|Bearer [A-Za-z0-9._-]{20,}" . --glob "!tmp/**" --glob "!GitHubClone/**" --glob "!**/.git/**" --glob "!**/.env" --glob "!**/data/**" --glob "!**/logs/**"
```

Result:

```text
No real secrets found.
Matches were placeholders, examples, documentation snippets, or code that writes env values supplied at runtime.
```

Notable benign matches:

```text
DEEPSEEK_API_KEY=...
API_SERVER_KEY=...
FEISHU_APP_SECRET=<app-secret>
DEEPSEEK_API_KEY=sk-... deploy/install.sh
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
```

## README / release wording scan

Command used:

```powershell
rg -n -i "official|lowest cost|guarantee|guaranteed|benchmark|secret|token|api[_-]?key|password|bearer|sk-[A-Za-z0-9]" README.md docs deploy --glob "!**/.env" --glob "!**/data/**" --glob "!**/logs/**"
```

Assessment:

- README uses "official" only to disclaim official status.
- README explicitly avoids an absolute lowest-cost promise.
- Benchmark references are tied to documented smoke/baseline evidence, not unsupported performance claims.
- Required secret examples are placeholders, not values.

## Verification completed

```text
deploy/validate_compose.py: PASS
clean branch 5 gate: 170 passed in 16.05s
```

## Remaining release blockers

```text
registry owner/namespace
registry token with push permission
Linux Docker host access
published-image pull/run smoke with --no-build
Node dependency license findings: unknown license entries and scripts/whatsapp-bridge GPL/LGPL review
```

## Recommendation

The project is acceptable to continue toward a public alpha registry smoke, provided the Node license findings are resolved or explicitly excluded and the published-image Docker smoke is completed before any public success announcement.
