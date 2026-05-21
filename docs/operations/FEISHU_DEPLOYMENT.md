# Feishu deployment guide

This guide enables Feishu/Lark on top of the Docker/Linux/systemd packaging base.

## Scope

Use this after the base deployment is in place:

- `deploy/docker-compose.yml`
- `deploy/.env`
- `deploy/install.sh`
- `~/.config/systemd/user/deepseek-native-agent.service`

The default packaging keeps Telegram and Weixin disabled. Do not enable them while validating Feishu; isolate one messaging platform at a time.

## Feishu app prerequisites

In Feishu Open Platform:

1. Create or open an app.
2. Copy credentials:
   - App ID, for example `cli_xxxxxxxxxxxxxxxx`
   - App Secret
3. Enable bot capability.
4. Add the bot to the target chat or group.
5. Use WebSocket connection mode first unless your network requires webhook mode.

Recommended mode:

```text
FEISHU_DOMAIN=feishu
FEISHU_CONNECTION_MODE=websocket
```

Use `FEISHU_DOMAIN=lark` only for international Lark tenants.

## Environment variables

Edit `deploy/.env` on the server:

```bash
cd ~/deepseek-native-agent
nano deploy/.env
```

Set:

```text
DEEPSEEK_NATIVE_IMAGE=deepseek-native-agent:latest
HERMES_BASE_IMAGE=nousresearch/hermes-agent:latest
FEISHU_ENABLED=true
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=<app-secret>
FEISHU_DOMAIN=feishu
FEISHU_CONNECTION_MODE=websocket
```

If the server cannot reach the default Python package index, set a mirror before building:

```text
PIP_INDEX_URL=https://mirror.example/simple
PIP_EXTRA_INDEX_URL=
```

The compose base builds a thin DeepSeek-native image layer from `deploy/Dockerfile`. That layer installs the Feishu optional dependencies (`lark-oapi==1.5.3`, `qrcode==7.4.2`) into the Hermes runtime venv. Do not rely on manual `docker exec` package installs; those were only a smoke workaround.

Optional but recommended access control:

```text
FEISHU_ALLOWED_USERS=ou_xxx,ou_yyy
FEISHU_HOME_CHANNEL=oc_xxxxx
FEISHU_HOME_CHANNEL_NAME=Home
```

Optional webhook-mode fields:

```text
FEISHU_ENCRYPT_KEY=
FEISHU_VERIFICATION_TOKEN=
```

## Access-control rule

For first test there are two choices:

1. safer: set `FEISHU_ALLOWED_USERS=ou_xxx`
2. broad test access: set `GATEWAY_ALLOW_ALL_USERS=true`

Prefer the safer path. If the bot receives messages but does not answer, check allowlist denial in gateway logs before blaming model/API credentials.

## Credential probe

Before restarting the service, validate the app credentials from the Hermes environment if the installed image/source exposes `gateway.platforms.feishu.probe_bot`:

```bash
cd ~/deepseek-native-agent
source deploy/.env
python3 - <<'PY'
import os
from gateway.platforms.feishu import probe_bot
print(probe_bot(
    app_id=os.environ['FEISHU_APP_ID'],
    app_secret=os.environ['FEISHU_APP_SECRET'],
    domain=os.getenv('FEISHU_DOMAIN', 'feishu'),
))
PY
```

Expected shape:

```text
{'bot_name': '...', 'bot_open_id': 'ou_...'}
```

If the deployment only has the Docker image and not source modules on the host, skip this host-side probe and validate by container logs after restart.

## Restart

```bash
systemctl --user restart deepseek-native-agent
systemctl --user status deepseek-native-agent --no-pager
journalctl --user -u deepseek-native-agent -f
```

Or directly with compose:

```bash
cd ~/deepseek-native-agent/deploy
docker compose --env-file .env build deepseek-native-agent
docker compose --env-file .env up -d
docker compose --env-file .env logs -f deepseek-native-agent
```

## Success logs

Look for:

```text
Connecting to feishu...
[Feishu] Connected in websocket mode (feishu)
✓ feishu connected
Gateway running with ... platform(s)
```

Then send a direct message to the bot or mention it in the target group.

## Troubleshooting

### Bot connected but silent

Check:

```bash
journalctl --user -u deepseek-native-agent -n 200 --no-pager
```

Common causes:

- Image was not rebuilt after enabling Feishu; run `docker compose --env-file .env build deepseek-native-agent` and restart.
- `FEISHU_ALLOWED_USERS` does not include the sender `ou_...`.
- `GATEWAY_ALLOW_ALL_USERS` is false and no allowlist is configured.
- The bot is not added to the chat/group.
- The app lacks event/message permissions in Feishu Open Platform.
- The model provider credentials are wrong even though Feishu is connected.

### WebSocket already using this app_id

Only one gateway instance may hold the Feishu WebSocket for an app ID.

Fix:

```bash
systemctl --user stop deepseek-native-agent
pkill -f 'hermes gateway' || true
pkill -f 'docker compose.*deepseek-native-agent' || true
cd ~/deepseek-native-agent/deploy
docker compose --env-file .env down
systemctl --user restart deepseek-native-agent
```

Do not run local Windows Feishu gateway and cloud Feishu gateway with the same app ID at the same time.

### Telegram errors appear during Feishu validation

Stop and remove the Telegram path. The DeepSeek Native deployment should keep:

```text
TELEGRAM_ENABLED=false
WEIXIN_ENABLED=false
```

Feishu validation should not be mixed with Telegram polling/proxy issues.

### Webhook mode

Use webhook mode only when WebSocket is not viable:

```text
FEISHU_CONNECTION_MODE=webhook
FEISHU_VERIFICATION_TOKEN=<token>
FEISHU_ENCRYPT_KEY=<encrypt-key-if-configured>
```

Webhook mode requires a public HTTPS endpoint routed to the gateway. The Docker/systemd base does not expose this publicly by default; add reverse proxy/TLS deliberately.

## Rollback

Disable Feishu without touching the rest of the deployment:

```bash
cd ~/deepseek-native-agent
python3 - <<'PY'
from pathlib import Path
p = Path('deploy/.env')
s = p.read_text(encoding='utf-8')
s = s.replace('FEISHU_ENABLED=true', 'FEISHU_ENABLED=false')
p.write_text(s, encoding='utf-8')
PY
systemctl --user restart deepseek-native-agent
```

## Validation status

This guide is source-checked against Hermes gateway config fields:

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_DOMAIN`
- `FEISHU_CONNECTION_MODE`
- `FEISHU_ENCRYPT_KEY`
- `FEISHU_VERIFICATION_TOKEN`
- `FEISHU_ALLOWED_USERS`
- `FEISHU_HOME_CHANNEL`
- `FEISHU_HOME_CHANNEL_NAME`
- `FEISHU_HOME_CHANNEL_THREAD_ID`

Real Feishu smoke requires a Linux host with Docker and a Feishu app credential pair.
