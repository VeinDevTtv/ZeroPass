# CommonPasswords Library — Rules & Guidelines

## Purpose
Provide a vetted, high-performance, language-agnostic library and dataset of common/compromised passwords that developers and security tools can use to:
- enforce password policy (denylist),
- check passwords client- or server-side,
- run password auditing and metrics,
- integrate into CI or account-creation flows.

This project is explicitly defensive: it helps developers block weak or compromised passwords and improve user security.

## Security & Privacy Principles
1. No storage of user passwords: This repo contains only aggregated common-password data and test artifacts. Never log or store real user credentials.
2. Do not ship sensitive PII: All datasets must be scrubbed and derived from public or consented sources. Avoid including any data that could be traced to a real person.
3. Hash-aware: Libraries must not attempt to reverse hashed passwords. Provide guidance for comparing hashed inputs (e.g., hash the candidate with same salt/algorithm, then check).
4. Client vs Server behavior:
   - Clients may perform offline checks (e.g., Bloom filter or compact trie).
   - Server checks may use larger datasets with higher assurance and can consult remote APIs.
5. Rate-limited & privacy-preserving remote checks: If the library offers a remote “have I seen this” API, it must support k-anonymity, hashing, or partial-information protocols to avoid exposing raw passwords.
6. Compatibility with regulations: Users integrating this library must ensure compliance with local laws and privacy rules (e.g., GDPR). This library does not provide legal advice.

## Dataset rules
1. Canonicalization / Normalization:
   - Normalize Unicode to NFC.
   - Trim leading/trailing whitespace.
   - Normalize different dash characters to ASCII '-' where appropriate.
   - Do not silently drop characters unless requested by a normalization option.
2. Unicode, accents, and homoglyphs:
   - Provide optional normalization policies: `strict` (ASCII-only), `preserve_unicode`, `normalize_homoglyphs` (opt-in).
3. Leetspeak & substitutions:
   - Provide optional generators/expanded sets for common substitutions (e.g., `0->o`, `3->e`, `@->a`) but keep them separate from the canonical denylist.
4. Locales:
   - Segment lists by language/locale (e.g., `en`, `es`, `fr`, `pt-BR`), plus a `global` list. Consumers choose which locales to load.
5. Versioned datasets:
   - Each dataset release must be semantic-versioned and timestamped (YYYY-MM-DD).
   - Maintain provenance metadata: source(s), count, processing pipeline, checksum (SHA256).
6. Formats:
   - Provide datasets in multiple formats:
     - Plain newline-separated text (`.txt`)
     - Compressed JSON (`.json.gz`) with metadata
     - Bloom filter serialization (`.bf`) with version and parameters
     - Minimal trie / prefix map binary (`.trie`) for fast lookups (optional)
7. Size tiers:
   - `tiny` — top 1k (client usage)
   - `small` — top 10k
   - `medium` — top 100k
   - `full` — complete curated list (server audits)
   - Each tier packaged separately.

## API design rules (across languages)
1. Consistent API surface (same semantics across bindings):
   - `initialize(options)` — load dataset/tier & options
   - `is_common(password)` -> `{common: bool, reason: string?, score?: int}`
   - `closest_matches(password, n=5)` -> `[passwords]` (optional)
   - `suggest_alternatives(password, n=3)` -> `[suggestions]` (optional; must not suggest insecure variations)
   - `version()` -> dataset version + checksum
2. Minimal dependencies: Keep core libs dependency-light; use standard libraries where possible.
3. Safe defaults:
   - Default to `tiny` or `small` for client libs to avoid large downloads.
   - Default normalization= `NFC + trim`.
   - Default locale = `global`.
4. Performance & memory:
   - Client libs: prioritized small memory usage (Bloom filter or compact trie).
   - Server libs: allow larger structures; provide streaming checks for huge datasets.
5. Non-blocking / async:
   - Provide asynchronous or streaming interfaces in languages that support concurrency.
6. Deterministic behavior:
   - Given the same input/options, results must be deterministic across language bindings.

## Packaging & Distribution
1. Repos & modules:
   - Monorepo root with language-specific packages in `packages/<language>` (e.g., `packages/python`, `packages/js`, `packages/go`, `packages/java`, `packages/rust`, `packages/dotnet`).
2. Build artifacts:
   - Package datasets as versioned assets and publish to package registries and artifact storage.
3. CI:
   - Each language package must have tests, linting, and a lightweight benchmark.
4. Licensing:
   - Use a permissive license (e.g., MIT) unless contributors require otherwise. Include `NOTICE` file for provenance.
5. Security audit:
   - Before major release, run a security checklist and document in release notes.

## Contribution rules
1. PRs must include:
   - Reason for change, dataset provenance, unit tests, performance impact (if any).
2. Reviewers:
   - At least two approvals, one of which is a maintainer with security experience.
3. Data additions:
   - Data must be public or properly licensed. Add provenance metadata in `/datasets/metadata/<version>.json`.
4. Dataset curation:
   - Automated scripts to dedupe, normalize, and compute checksums.
   - Manual spot-check review before merge for `full` tier.

## Testing & QA
1. Unit tests for correctness of normalization, lookups, and API surface.
2. Fuzz tests to test Unicode edge cases and long input handling.
3. Performance tests:
   - Lookup latency (per password) for each tier and binding.
   - Memory usage for client and server scenarios.
4. Compatibility tests:
   - Ensure bindings return the same `is_common` result for canonical inputs.

## Release & Versioning
1. Semantic versioning for code packages: MAJOR.MINOR.PATCH.
2. Dataset versioning independent from tooling version: `vYYYYMMDD.N` (e.g., `20251016.1`).
3. Changelog: include dataset changes, new sources, and breaking normalization changes.

## Examples & Integrations
- Small example code for each language demonstrating initialization and `is_common` check.
- Guidance for integration into registration flows: check password and if `common` -> show specific UX text advising stronger password or passphrase.

## Governance & Maintenance
- Define maintainers and a documented process for handling security reports.
- Publish a responsible disclosure policy and contact method.

## Quick Do-and-Don’t summary
- Do: Provide small client-friendly artifacts (Bloom), document provenance, version datasets, normalize inputs.
- Don’t: Ship raw leaked credentials containing PII, perform server-side password collection without consent, suggest insecure password transformations.


