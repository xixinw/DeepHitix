# Dependency License Scan - 2026-05-21

Purpose: record dependency license checks completed before the public alpha registry smoke.

## Python scan

Source:

```text
D:/Hermes_save/deepseek-native-agent/tmp/phase5-upstream-pr-branches/hermes-agent-upstream-clean
```

Command:

```powershell
uv run --frozen --with pip-licenses pip-licenses --format=json --output-file D:/Hermes_save/deepseek-native-agent/docs/operations/dependency_licenses_python_2026-05-21.json
```

Result:

```text
Python packages scanned: 46
Unknown licenses: 0
GPL/AGPL/LGPL matches: 0
Output: docs/operations/dependency_licenses_python_2026-05-21.json
```

License summary:

```text
MIT License: 13
MIT: 10
BSD-3-Clause: 6
BSD License: 5
Apache Software License: 4
Apache-2.0: 2
Apache Software License; BSD License: 1
Apache Software License; MIT License: 1
Apache-2.0 OR BSD-3-Clause: 1
MPL-2.0 AND MIT: 1
Mozilla Public License 2.0 (MPL 2.0): 1
PSF-2.0: 1
```

Assessment: no Python copyleft blocker found for the clean branch 5 default environment scanned by `uv run`.

## Node/package-lock scan

Command:

```powershell
python -c "<package-lock license summary script>"
```

Package lock files scanned:

```text
package-lock.json
ui-tui/package-lock.json
web/package-lock.json
website/package-lock.json
scripts/whatsapp-bridge/package-lock.json
ui-tui/packages/hermes-ink/package-lock.json
```

Copyleft match summary:

```text
package-lock.json: 0
ui-tui/package-lock.json: 0
web/package-lock.json: 0
website/package-lock.json: 0
ui-tui/packages/hermes-ink/package-lock.json: 0
scripts/whatsapp-bridge/package-lock.json: 15
```

Findings in `scripts/whatsapp-bridge/package-lock.json`:

```text
node_modules/libsignal | GPL-3.0
node_modules/@img/sharp-libvips-* | LGPL-3.0-or-later
node_modules/@img/sharp-wasm32 | Apache-2.0 AND LGPL-3.0-or-later AND MIT
node_modules/@img/sharp-win32-* | Apache-2.0 AND LGPL-3.0-or-later
```

Unknown license counts:

```text
ui-tui/package-lock.json: 3
web/package-lock.json: 1
website/package-lock.json: 5
scripts/whatsapp-bridge/package-lock.json: 2
ui-tui/packages/hermes-ink/package-lock.json: 1
```

## Release interpretation

The current public alpha deployment path is Docker/API/Feishu. It does not enable WhatsApp bridge as a release feature, and the root Dockerfile installs root, web, and ui-tui dependencies, not `scripts/whatsapp-bridge`.

However, if the public repository includes `scripts/whatsapp-bridge`, the GPL/LGPL findings need an explicit decision before launch:

1. Keep WhatsApp bridge in the public repo and document the GPL/LGPL obligations.
2. Remove or exclude WhatsApp bridge from the public-alpha source package.
3. Split WhatsApp bridge into a separately licensed optional component.

Decision for v0.1.0-alpha.1: exclude WhatsApp bridge from the public alpha package and do not advertise WhatsApp support until its license obligations are reviewed. See `docs/operations/PUBLIC_ALPHA_SOURCE_MANIFEST_2026-05-21.md`.

## Remaining license work

- Resolve or document Node `UNKNOWN` license entries.
- Confirm the final public source archive/repository excludes `scripts/whatsapp-bridge` for v0.1.0-alpha.1.
- If building a final release image, inspect the image contents and generated dependency tree from the built image as part of the published-image smoke.
