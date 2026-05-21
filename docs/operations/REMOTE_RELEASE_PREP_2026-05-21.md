# Remote Release Preparation - 2026-05-21

Purpose: record non-destructive preparation on the Linux Docker host for the published-image smoke.

## Host

```text
host: 101.34.214.32
user: ubuntu login, remote shell user observed as hailiweiha
Docker: 29.1.3
Docker Compose: 2.40.3
workspace: /home/ubuntu/deepseek-native-agent-alpha-release
```

Existing service was not modified:

```text
container: deepseek-native-agent
port: 127.0.0.1:18642->8642
status: healthy
```

Open/usable isolation port:

```text
127.0.0.1:18643
```

Disk snapshot:

```text
/dev/vda2 40G total, 25G used, 13G available
```

Note: 13G may be tight for a full Hermes image rebuild. If build fails for space, use a larger temporary Docker host or remove only obsolete smoke images after confirming they are no longer needed.

## Local SSH key fix

Windows OpenSSH refused the private key because ACLs were too open. The ACL was tightened to:

```text
HAILI\weiha:(R)
BUILTIN\Administrators:(F)
NT AUTHORITY\SYSTEM:(F)
```

No project files contain the private key.

## Release scripts staged on host

```text
/home/ubuntu/deepseek-native-agent-alpha-release/build_push_published_image.sh
/home/ubuntu/deepseek-native-agent-alpha-release/smoke_published_image.sh
```

Validation:

```text
bash -n build_push_published_image.sh: PASS
bash -n smoke_published_image.sh: PASS
```

## Public alpha source archive

Local archive:

```text
D:/Hermes_save/deepseek-native-agent/tmp/deepseek-native-agent-v0.1.0-alpha.1-source.tar.gz
```

Remote archive:

```text
/home/ubuntu/deepseek-native-agent-alpha-release/deepseek-native-agent-v0.1.0-alpha.1-source.tar.gz
```

Archive size:

```text
28594930 bytes compressed
```

Remote source self-check:

```text
SOURCE_COMMIT=1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c
scripts/whatsapp-bridge absent
.git absent
.venv absent
node_modules absent
deploy/Dockerfile present
root Dockerfile present
agent/routing_policy.py present
deploy/validate_compose.py PASS
```

2026-05-21 update after publishing-state documentation refresh:

```text
public alpha source tar.gz rebuilt locally
remote tar.gz re-uploaded to the same workspace
remote tar.gz size matches local artifact: 28594930 bytes
remote tar.gz re-extracted under source-check/public-alpha-source-v0.1.0-alpha.1
branding decision doc present in release source
published-image build attempt and remote prep docs present in release source
forbidden-path exclusions rechecked
deploy/validate_compose.py PASS
existing deepseek-native-agent container still healthy on 127.0.0.1:18642
```

Do not use the temporary Windows zip artifact for Linux release prep. It used Windows-style path separators and was discarded in favor of tar.gz.

## Current blocker

The host is ready for isolated build/push/smoke work, but registry publication still needs a GHCR token with package push permission for:

```text
ghcr.io/weiha/deepseek-native-agent
```

No published image success is claimed yet.
