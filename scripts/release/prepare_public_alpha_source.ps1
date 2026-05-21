param(
    [string]$ProjectRoot = "D:/Hermes_save/deepseek-native-agent",
    [string]$CleanSource = "D:/Hermes_save/deepseek-native-agent/tmp/phase5-upstream-pr-branches/hermes-agent-upstream-clean",
    [string]$OutputDir = "D:/Hermes_save/deepseek-native-agent/tmp/public-alpha-source-v0.1.0-alpha.1"
)

$ErrorActionPreference = "Stop"

$expectedRev = "1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c"
$actualRev = (git -C $CleanSource rev-parse HEAD).Trim()
if ($actualRev -ne $expectedRev) {
    throw "Unexpected clean source revision: $actualRev (expected $expectedRev)"
}

if (Test-Path $OutputDir) {
    Remove-Item -LiteralPath $OutputDir -Recurse -Force
}
New-Item -ItemType Directory -Path $OutputDir | Out-Null

function Invoke-RobocopyChecked {
    param([string[]]$RoboArgs)
    & robocopy @RoboArgs | Out-Host
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed with exit code $LASTEXITCODE"
    }
}

Invoke-RobocopyChecked -RoboArgs @(
    $CleanSource, $OutputDir,
    "/MIR",
    "/XD", ".git", ".venv", "node_modules", "tmp", "data", "logs", "whatsapp-bridge", ".pytest_cache", "__pycache__", "hermes_agent.egg-info", ".github\workflows", ".github\actions",
    "/XF", ".env",
    "/NFL", "/NDL", "/NJH", "/NJS", "/NP"
)

$copyItems = @(
    "README.md",
    "ATTRIBUTION.md",
    "TRADEMARKS.md",
    "SECURITY.md",
    "PRIVACY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "NOTICE.md",
    "THIRD_PARTY_NOTICES.md",
    "deploy",
    "docs/compliance",
    "docs/operations/PHASE5_RELEASE_README_CHECKLIST.md",
    "docs/operations/PROJECT_BOARD_STATUS_UPDATE_2026-05-21.md",
    "docs/operations/RELEASE_NOTES_v0.1.0-alpha.1.md",
    "docs/operations/PUBLISHED_IMAGE_SMOKE_2026-05-21.md",
    "docs/operations/PUBLISHED_IMAGE_BUILD_ATTEMPT_2026-05-21.md",
    "docs/operations/REAL_DEEPSEEK_API_SMOKE_2026-05-21.md",
    "docs/operations/PUBLIC_ALPHA_SOURCE_MANIFEST_2026-05-21.md",
    "docs/operations/REMOTE_RELEASE_PREP_2026-05-21.md",
    "docs/operations/BRANDING_DECISION_2026-05-21.md",
    "docs/operations/RELEASE_HYGIENE_2026-05-21.md",
    "docs/operations/DEPENDENCY_LICENSE_SCAN_2026-05-21.md",
    "docs/operations/dependency_licenses_python_2026-05-21.json",
    "docs/operations/DOCKER_FEISHU_SMOKE_2026-05-19.md",
    "docs/operations/FEISHU_DEPLOYMENT.md",
    "docs/operations/LINUX_DEPLOYMENT.md",
    "docs/operations/M4_UPSTREAM_PR_DRAFTS.md",
    "docs/operations/PHASE5_UPSTREAM_BRANCH_EVIDENCE.md",
    "scripts/release"
)

foreach ($item in $copyItems) {
    $src = Join-Path $ProjectRoot $item
    $dst = Join-Path $OutputDir $item
    if (!(Test-Path $src)) {
        throw "Missing release overlay item: $src"
    }
    $parent = Split-Path $dst -Parent
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    if ((Get-Item $src).PSIsContainer) {
        Invoke-RobocopyChecked -RoboArgs @($src, $dst, "/MIR", "/XD", ".git", ".venv", "node_modules", "data", "logs", ".pytest_cache", "__pycache__", "hermes_agent.egg-info", "/XF", ".env", "/NFL", "/NDL", "/NJH", "/NJS", "/NP")
    } else {
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
}

$generatedGithubPaths = @(
    ".github/workflows",
    ".github/actions"
)

foreach ($rel in $generatedGithubPaths) {
    $candidate = Join-Path $OutputDir $rel
    if (Test-Path $candidate) {
        Remove-Item -LiteralPath $candidate -Recurse -Force
    }
}

$forbidden = @(
    "scripts/whatsapp-bridge",
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "hermes_agent.egg-info",
    "node_modules",
    ".github/workflows",
    ".github/actions",
    "deploy/.env",
    "deploy/data"
)

foreach ($rel in $forbidden) {
    $candidate = Join-Path $OutputDir $rel
    if (Test-Path $candidate) {
        throw "Forbidden release path exists: $candidate"
    }
}

git -C $CleanSource rev-parse HEAD | Set-Content -Path (Join-Path $OutputDir "SOURCE_COMMIT.txt") -NoNewline

Write-Host "Prepared public alpha source tree:"
Write-Host $OutputDir
