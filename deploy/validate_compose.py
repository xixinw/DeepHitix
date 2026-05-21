#!/usr/bin/env python3
"""Static validation for the Docker Compose smoke base.

This script intentionally avoids requiring Docker. It is meant for machines where
Docker Desktop / Docker Engine is not installed yet.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMPOSE = ROOT / "docker-compose.yml"
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
ENV_EXAMPLE = ROOT / ".env.example"
README = ROOT / "README.md"

FORBIDDEN_PATH_PATTERNS = [
    # Windows drive paths, but not URL schemes such as http://.
    r"(?<![A-Za-z])[A-Za-z]:/",
    r"(?<![A-Za-z])[A-Za-z]:\\\\",
    r"/c/Users/",
    r"/d/Hermes_save/",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"WARN: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path.name}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    compose = read(COMPOSE)
    dockerfile = read(DOCKERFILE)
    dockerignore = read(DOCKERIGNORE)
    env_example = read(ENV_EXAMPLE)
    readme = read(README)

    if "deepseek-native-agent:" not in compose:
        fail("compose service deepseek-native-agent missing")
    if "build:" not in compose or "Dockerfile" not in compose:
        fail("compose does not build the project image layer")
    ok("compose service present")

    if "lark-oapi==1.5.3" not in dockerfile or "qrcode==7.4.2" not in dockerfile:
        fail("Dockerfile does not install Feishu optional dependencies")
    if "uv pip install" not in dockerfile or "/opt/hermes/.venv/bin/python3" not in dockerfile:
        fail("Dockerfile does not install into the Hermes runtime venv")
    ok("Feishu optional dependencies are productized in Dockerfile")

    for required_ignore in (".env", "data/", "*.pem"):
        if required_ignore not in dockerignore:
            fail(f".dockerignore does not exclude {required_ignore}")
    ok("Docker build context excludes secrets and runtime data")

    if "${DEEPSEEK_API_KEY:?" not in compose:
        fail("DEEPSEEK_API_KEY is not required by compose")
    if "${API_SERVER_KEY:?" not in compose:
        fail("API_SERVER_KEY is not required by compose")
    ok("required secrets are enforced")

    if "127.0.0.1" not in compose:
        fail("API server does not default to localhost binding")
    ok("API server defaults to localhost binding")

    if re.search(r"TELEGRAM_ENABLED:\s*[\"']?true", compose, re.IGNORECASE):
        fail("Telegram is enabled in the smoke base")
    if "TELEGRAM_ENABLED: \"false\"" not in compose:
        fail("Telegram is not explicitly disabled")
    ok("Telegram explicitly disabled")

    if re.search(r"WEIXIN_ENABLED:\s*[\"']?true", compose, re.IGNORECASE):
        fail("Weixin is enabled in the smoke base")
    ok("Weixin not enabled")

    for label, text in [("compose", compose), ("dockerfile", dockerfile), ("dockerignore", dockerignore), ("env_example", env_example), ("readme", readme)]:
        for pattern in FORBIDDEN_PATH_PATTERNS:
            if re.search(pattern, text):
                fail(f"{label} contains local absolute path pattern {pattern}")
    ok("no local absolute paths")

    if "DEEPSEEK_API_KEY=" not in env_example or "API_SERVER_KEY=" not in env_example:
        fail(".env.example missing required key placeholders")
    if "HERMES_BASE_IMAGE=" not in env_example or "PIP_INDEX_URL=" not in env_example:
        fail(".env.example missing image build controls")
    ok(".env.example placeholders present")

    try:
        import yaml  # type: ignore
    except Exception:
        warn("PyYAML not installed; skipped YAML parser validation")
    else:
        data = yaml.safe_load(compose)
        if not isinstance(data, dict):
            fail("compose YAML did not parse to mapping")
        services = data.get("services")
        if not isinstance(services, dict) or "deepseek-native-agent" not in services:
            fail("parsed compose missing deepseek-native-agent service")
        ok("compose parses as YAML")

    print("PASS: Docker Compose validation base is structurally sound")
    return 0


if __name__ == "__main__":
    sys.exit(main())
