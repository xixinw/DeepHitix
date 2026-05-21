# Linux deployment with Docker Compose + systemd user service

This guide turns the Docker Compose validation base into a persistent Linux deployment.

## Scope

This is the v0.1 deployment path for a Linux VM:

- Docker Compose runs the agent gateway container.
- The gateway exposes the API server on localhost by default.
- systemd user service controls lifecycle.
- Telegram and Weixin stay disabled.
- Feishu is documented separately after this base is stable.

## Prerequisites

On the target server:

```bash
docker --version
docker compose version
systemctl --user --version
python3 --version
```

If Docker is not installed, install Docker Engine using the official Docker documentation for your distribution. This project installer intentionally does not install Docker automatically.

For headless cloud VMs, enable user-service persistence:

```bash
sudo loginctl enable-linger "$USER"
```

## Install

From the project root:

```bash
DEEPSEEK_API_KEY=sk-... deploy/install.sh
```

Optional custom install directory:

```bash
INSTALL_DIR=/opt/deepseek-native-agent DEEPSEEK_API_KEY=sk-... deploy/install.sh
```

The installer will:

1. check `docker`, `docker compose`, `systemctl`, and `python3`;
2. create `deploy/.env` from `deploy/.env.example` if missing;
3. generate `API_SERVER_KEY` if not provided;
4. write `~/.config/systemd/user/deepseek-native-agent.service`;
5. run static compose validation;
6. run `docker compose config`;
7. enable and restart the systemd user service.

## Service commands

```bash
systemctl --user status deepseek-native-agent
systemctl --user restart deepseek-native-agent
systemctl --user stop deepseek-native-agent
journalctl --user -u deepseek-native-agent -f
```

Container logs:

```bash
cd deploy
docker compose --env-file .env logs -f deepseek-native-agent
```

## Health check

Default API server bind:

```text
127.0.0.1:8642
```

Smoke check:

```bash
curl http://127.0.0.1:8642/health
```

If an endpoint requires auth:

```bash
source deploy/.env
TOKEN="$""{API_SERVER_KEY}"
curl -H "Authorization: Bearer ${TOKEN}" http://127.0.0.1:8642/health
```

## Security defaults

- `API_SERVER_BIND=127.0.0.1`
- `TELEGRAM_ENABLED=false`
- `WEIXIN_ENABLED=false`
- `FEISHU_ENABLED=false`
- `deploy/.env` mode is set to `600` where supported.

Do not expose `8642` directly to the internet. Use SSH tunnel or a reverse proxy with auth/TLS.

## Files

```text
deploy/docker-compose.yml
deploy/.env.example
deploy/install.sh
deploy/systemd/deepseek-native-agent.service
deploy/validate_compose.py
```

## Current validation status

On the current Windows development host:

```text
python deploy/validate_compose.py -> PASS
docker --version -> command not found
```

So this guide is statically validated, but real container smoke must run on a Docker-enabled Linux host.
