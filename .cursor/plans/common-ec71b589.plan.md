<!-- ec71b589-63be-46a9-9453-b9a583338bf8 38738656-72be-469e-9582-cc394b3cf30f -->
# CommonPass Monorepo: Scaffold, Dataset Pipeline, JS + Python v0.1.0

## Overview

CommonPass provides developers with a cross-language dataset and API to detect commonly used passwords for security enforcement, validation, and analysis.
It includes a deterministic dataset build pipeline, portable Bloom filter generation, and lightweight bindings for JavaScript and Python (with Go, Rust, Java, and .NET planned).

## Coordinates

- GitHub org/namespace: `commonpass`
- Responsible disclosure contact: `abdelkarim.contact1@gmail.com`

### Package Coordinates
| Language        | Package / Module                   | Notes           |
| --------------- | ---------------------------------- | --------------- |
| npm             | `@commonpass/core`                 | ESM + UMD build |
| PyPI            | `commonpass`                       | Pure Python     |
| Go (planned)    | `github.com/commonpass/commonpass` | Go module       |
| Rust (planned)  | `commonpass`                       | Crate name      |
| Maven (planned) | `io.commonpass:commonpass`         | Java package    |
| .NET (planned)  | `CommonPass`                       | NuGet           |

## Repository Structure
```
commonpass/
├── README.md
├── LICENSE (MIT)
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CODEOWNERS
├── MAINTAINERS.md
├── NO_LEAKED_DATA.md
├── CHANGELOG.md
├── NOTICE
├── rules.md  ← (this file)
│
├── datasets/
│   ├── raw/                      # SAMPLE_* sources only
│   ├── pipeline/
│   │   ├── build.py              # CLI builder
│   │   ├── bloom.py              # Bloom filter logic
│   │   ├── trie.py               # Optional prefix trie exporter
│   │   ├── utils.py
│   │   └── metadata.py
│   └── 20251016.1/               # Example versioned dataset
│       ├── common_tiny.txt
│       ├── common_small.txt
│       ├── common_medium.txt
│       ├── common_full.txt
│       ├── common_tiny.bf
│       ├── metadata.json
│       └── ...
│
├── packages/
│   ├── javascript/
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── bloom.ts
│   │   │   └── normalize.ts
│   │   ├── test/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── vitest.config.ts
│   │   └── examples/
│   │       ├── node.mjs
│   │       └── browser.html
│   │
│   ├── python/
│   │   ├── src/commonpass/
│   │   │   ├── __init__.py
│   │   │   ├── core.py
│   │   │   ├── bloom.py
│   │   │   ├── normalize.py
│   │   │   └── version.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── go/ (stub)
│   ├── rust/ (stub)
│   ├── java/ (stub)
│   └── csharp/ (stub)
│
├── tools/integration/
│   ├── canonical_inputs.txt
│   ├── check_consistency.py
│   └── run_all.sh
│
├── ci/
│   ├── lint-and-test.yml
│   ├── dataset-build.yml
│   └── release.yml
│
└── release/
    └── release.sh
```

## Dataset Pipeline (Python)

Goal: produce deterministic, normalized password datasets and portable Bloom/trie artifacts.

### Input
- Raw text under `datasets/raw/*.txt`
- Optional frequency format: `password,count`
- Must be synthetic or licensed lists, no leaked data.

### Processing
- Normalize: NFC Unicode, trim, optional lowercase.
- Deduplicate: Merge frequency counts.
- Sort: By descending frequency, then lexicographically.
- Split Tiers:
  - tiny: 1K
  - small: 10K
  - medium: 100K
  - full: all

### Output
For each tier:
- `.txt`: newline-separated passwords
- `.json.gz`: `{meta, data}` with SHA256 checksums and Bloom params
- `.bf`: portable Bloom filter with JSON header + bit array
- `.trie`: optional binary prefix map
- `metadata.json`: dataset-level metadata

### Dataset Versioning
- Folder name: `YYYYMMDD.N` (e.g. `20251016.1`)
- `metadata.json` includes:
```
{
  "dataset_version": "20251016.1",
  "code_version": "v0.1.0",
  "counts": {"tiny":1000,"small":10000,"medium":100000,"full":500000},
  "bloom": {"expected_n":10000,"fpr":1e-5,"hash_count":7,"bit_size":8388608},
  "sha256": {"common_small.txt":"..."},
  "sources":["sample_global.txt"]
}

{
  "dataset_version": "20251016.1",
  "code_version": "v0.1.0",
  "counts": {"tiny":1000,"small":10000,"medium":100000,"full":500000},
  "bloom": {"expected_n":10000,"fpr":1e-5,"hash_count":7,"bit_size":8388608},
  "sha256": {"common_small.txt":"..."},
  "sources":["sample_global.txt"]
}
```

### Bloom Filter Specification
#### Algorithm
- Hash algorithm: SHA-256
- Double-hash derivation:
  - `h1 = sha256(data || 0x00)`
  - `h2 = sha256(data || 0x01)`
  - For i in [0..k-1]: `hash_i = (h1 + i * h2) mod m`
- Endianness: big-endian bit layout

#### Default Parameters
| Tier   | Target FPR | Hash Count | Bit Size (example) |
| ------ | ---------- | ---------- | ------------------ |
| tiny   | 1e-4       | 7          | ~1 MB              |
| small  | 1e-5       | 7          | ~2 MB              |
| medium | 1e-6       | 7          | ~8 MB              |
| full   | 1e-8       | 7          | variable           |

#### .bf Header Example
```
{
  "version": "20251016.1",
  "tier": "tiny",
  "locale": "global",
  "expected_n": 1000,
  "fpr": 1e-4,
  "bit_size": 8388608,
  "hash_count": 7,
  "hash_algo": "sha256",
  "created_at": "2025-10-16T12:00:00Z"
}
```

Followed by a single newline (\n) and then raw bit-array bytes.

## Shared API (for all languages)
```
initialize(options?: {
  tier?: "tiny" | "small" | "medium" | "full",
  locale?: string,
  normalization?: "nfc" | "lower" | "trim",
  load_mode?: "inline" | "stream" | "remote"
})

is_common(password: string): {
  common: boolean,
  version: string,
  tier: string
}

version(): {
  dataset: string,
  checksum: string
}
```

## Cross-Language Integration Test
Purpose: ensure all bindings (JS/Python/others) yield identical results.

Inputs: `tools/integration/canonical_inputs.txt`

Process:
- Run both implementations with same dataset and normalization.
- Compare boolean results for each password.
- Fail CI if any mismatch.

## CI (GitHub Actions)
### lint-and-test.yml
- Matrix: Node LTS, Python 3.10–3.12
- Steps:
  - Lint (eslint, ruff)
  - Run unit tests (vitest, pytest)
  - Run `tools/integration/check_consistency.py`

### dataset-build.yml
- Build dataset from samples
- Emit artifacts under `datasets/YYYYMMDD.N/`
- Compute SHA256 for all outputs
- Upload artifacts for `release.yml`

### release.yml
- Trigger: tag `v*`
- Download dataset artifacts
- Package JS and Python releases
- Attach datasets to GitHub Release
- Optional: GPG-sign the release

## Governance & Security
### Added Files
- CODEOWNERS: assign maintainers per directory
- MAINTAINERS.md: list contact, rotation policy, and PGP key (optional)
- NO_LEAKED_DATA.md: contributor notice – only synthetic or licensed password data allowed.
- SECURITY.md
  - Vulnerability reporting: `abdelkarim.contact1@gmail.com`
  - Response SLA: 7 business days
  - No public issue tracker disclosures
- CODE_OF_CONDUCT.md
  - Contributor and maintainer behavior expectations

### Default Safety Behavior
- Client libraries never send plaintext passwords.
- Remote checks (if implemented later) must use k-anonymity or partial hash lookup.
- Default tier = tiny, load local `.bf` file offline.
- All examples emphasize privacy-preserving usage.

## To-Do Summary
✅ Done:
- Monorepo scaffold
- Dataset pipeline + sample data
- JS + Python packages
- CI setup + docs + release script

🚧 Next:
- Replace all legacy commonpasswords names → commonpass.
- Add CODEOWNERS, MAINTAINERS.md, and NO_LEAKED_DATA.md.
- Implement deterministic Bloom header parsing in both JS and Python (SHA-256 double-hash).
- Add parity tests (`tools/integration/check_consistency.py` + CI step).
- Update pipeline to write new Bloom metadata schema and metadata.json layout.
- Verify all tests pass and parity checks are 100%.
- Generate initial dataset `20251016.1` and tag release `v0.1.0`.
- Publish `@commonpass/core` (npm) and `commonpass` (PyPI).
- Add stubs and READMEs for Go, Rust, Java, .NET bindings.
- Write short developer docs explaining how to integrate CommonPass for password strength checks.