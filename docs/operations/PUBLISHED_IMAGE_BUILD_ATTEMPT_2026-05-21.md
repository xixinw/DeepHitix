# Published Image Build Attempt - 2026-05-21

Purpose: record the first real remote build/push attempt for `v0.1.0-alpha.1`.

## Result Summary

```text
remote host: 101.34.214.32
workspace: /home/ubuntu/deepseek-native-agent-alpha-release/source-check/public-alpha-source-v0.1.0-alpha.1
image: ghcr.io/weiha/deepseek-native-agent:v0.1.0-alpha.1
alias: ghcr.io/weiha/deepseek-native-agent:public-alpha
source revision: 1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c
build: PASS
local image import probe: PASS
push: BLOCKED
```

## Build Strategy

The first attempt to build from the full root `Dockerfile` was stopped because the small smoke host has limited free disk and the legacy Docker builder was slow during large base-layer retrieval.

The successful build used:

```text
scripts/release/Dockerfile.public-alpha
```

This overlays clean branch 5 source onto `nousresearch/hermes-agent:latest`, reinstalls the project into the existing Hermes venv, and installs Feishu optional dependencies. This preserves the DeepSeek-native code under test without rebuilding the full upstream production image from scratch.

## Successful Local Image Evidence

```text
Successfully built 539ce7663191
Successfully tagged ghcr.io/weiha/deepseek-native-agent:v0.1.0-alpha.1
Successfully tagged ghcr.io/weiha/deepseek-native-agent:public-alpha
```

Image label check:

```text
IMAGE_ID=sha256:539ce76631917f7e00eebc72d26cd471d66068aeae85f4c5ba25f42d55abcf21
REV=1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c
TITLE=DeepSeek Native Agent
```

Import probe:

```text
LOCAL_IMAGE_IMPORT_PROBE_PASS
```

Local image inventory:

```text
ghcr.io/weiha/deepseek-native-agent   public-alpha     8.7GB
ghcr.io/weiha/deepseek-native-agent   v0.1.0-alpha.1   8.7GB
deepseek-native-agent                 feishu-smoke     8.58GB
nousresearch/hermes-agent             latest           8.51GB
```

Disk after build:

```text
/dev/vda2 40G total, 26G used, 13G available
```

Existing service impact:

```text
No existing healthy Hermes/Docker service was modified.
```

## Push Failure

Push failed with:

```text
error from registry: permission_denied: The token provided does not match expected scopes.
```

Interpretation:

- Docker/GHCR login exists, but the token used for login does not have the package push scope GHCR expects, or it is not authorized for this namespace/package.
- The image is built locally on the remote host, but it is not published to GHCR.
- Published-image smoke cannot proceed until push succeeds.

## Second Token Check

A newly supplied GitHub classic PAT was tested on 2026-05-21 without writing it to disk.

Observed:

```text
GitHub API identity check: PASS
GHCR docker login: FAIL
reported token scopes: repo
required package scopes present: NO
```

The token is valid for GitHub API access, but it does not include `read:packages` or `write:packages`, so GHCR rejects Docker login before image push begins.

The token identity also differs from the originally documented `weiha` registry namespace. If publishing under that token's user namespace, update image coordinates before release; otherwise generate a PAT from the account or organization that owns `ghcr.io/weiha`.

## Third Token Check

A third GitHub classic PAT was tested on 2026-05-21 for the `xixinw` namespace without writing it to disk.

Observed:

```text
GitHub API identity check: PASS
token owner: xixinw
reported token scopes include write:packages: YES
reported token scopes include read:packages: NO
GHCR docker login as xixinw: FAIL
```

The token is valid and has broad GitHub scopes, but GHCR still rejects Docker login because the token does not expose `read:packages`.

If publishing under `xixinw`, regenerate a classic PAT that explicitly includes:

```text
read:packages
write:packages
```

Keep `repo` only if the package is tied to a private repository.

## Fourth Token Check

A fourth GitHub classic PAT was tested on 2026-05-21 for the `xixinw` namespace without writing it to disk.

Observed:

```text
GitHub API identity check: PASS
token owner: xixinw
reported token scopes include write:packages: YES
reported token scopes include read:packages: NO
GHCR docker login as xixinw: FAIL
```

Although the token creation UI appeared to show `read:packages` selected under `write:packages`, the GitHub API scope header did not expose `read:packages`, and GHCR rejected Docker login.

## Required Fix

Regenerate or authorize a GitHub token for `ghcr.io/weiha/deepseek-native-agent` with at least:

```text
write:packages
read:packages
```

If the package is tied to a private repository, also include:

```text
repo
```

Then re-login on the host:

```bash
docker logout ghcr.io
export GHCR_OWNER=weiha
export GHCR_TOKEN='<new token with write:packages>'
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin
unset GHCR_TOKEN
```

After that, rerun:

```bash
cd /home/ubuntu/deepseek-native-agent-alpha-release/source-check/public-alpha-source-v0.1.0-alpha.1
GHCR_OWNER=weiha IMAGE_TAG=v0.1.0-alpha.1 IMAGE_ALIAS=public-alpha PIP_INDEX_URL=https://mirrors.tencent.com/pypi/simple scripts/release/build_push_published_image.sh
```

No published image success is claimed yet.
