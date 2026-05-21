# Branding Decision - 2026-05-21

Purpose: shorten the public-facing project name without hiding the technical lineage or implying official affiliation.

## Recommended Public Name

```text
DeepHitix
```

Working tagline:

```text
Cache-hit native agent for DeepSeek workflows.
```

Long descriptor for README/SEO:

```text
DeepHitix is a DeepSeek-native, cache-aware, one-click deployable personal and team agent assistant.
```

## Rationale

- Short enough to remember and say while still signaling the DeepSeek focus.
- Connects to the project thesis: higher cache-hit discipline plus richer Hermes-style agent capability.
- The `-ix` ending nods lightly toward Reasonix without copying the name.
- Avoids long literal names such as `DeepSeek Native Agent` as the primary brand.
- Keeps `DeepSeek Native Agent` available as a technical descriptor during alpha packaging.

## Naming Risk Notes

Preliminary web search showed that generic cache-agent names are crowded:

```text
CacheCore
AgentCache
ContextCache
```

`DeepHitix` did not show an obvious active AI-agent/cache product collision in the quick web search, but it is not a formal trademark clearance. Before a public launch, run a real trademark/domain/package-name review.

## Alpha Decision

For `v0.1.0-alpha.1`, keep package/image coordinates stable until GHCR publishing and smoke are complete:

```text
ghcr.io/weiha/deepseek-native-agent:v0.1.0-alpha.1
ghcr.io/weiha/deepseek-native-agent:public-alpha
```

Use `Hitix` as the public product name in README/release copy after the current image publishing path is unblocked, then consider renaming image/repository coordinates in a later alpha if desired.
