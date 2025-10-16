<!-- ec71b589-63be-46a9-9453-b9a583338bf8 38738656-72be-469e-9582-cc394b3cf30f -->
# CommonPasswords Monorepo: Scaffold, Dataset Pipeline, JS + Python v0.1.0

## Coordinates

- GitHub org/namespace: `commonpass`
- Contact (responsible disclosure): `abdelkarim.contact1@gmail.com`
- Package coordinates:
- npm: `@commonpass/commonpasswords`
- PyPI: `commonpasswords`
- Go (planned): `github.com/commonpass/commonpasswords`
- Rust (planned): `commonpasswords`
- Maven (planned): `org.commonpass:commonpasswords`
- .NET (planned): `CommonPass.CommonPasswords`

## Repo Structure to Create

- Root:
- `rules.md` (provided content)
- `README.md`, `CHANGELOG.md`, `LICENSE` (MIT), `SECURITY.md`, `CONTRIBUTING.md`, `NOTICE`
- `release/` with `release.sh`
- `datasets/`
- `raw/` small SAMPLE sources (e.g., `sample_en.txt`, `sample_global.txt` with clearly marked `SAMPLE_` entries)
- `pipeline/` Python build tooling:
  - `build.py` (CLI) — normalize (NFC, trim), dedupe, sort by frequency; split tiers (1k/10k/100k/full); emit artifacts
  - `bloom.py` — portable Bloom filter (parameterizable, serialize/deserialize)
  - `trie.py` — minimal compact prefix-map exporter (binary `.trie`)
  - `utils.py`, `metadata.py`, `__init__.py`
  - `requirements.txt` (stdlib preferred; only `orjson` optional for speed)
- `vYYYYMMDD.1/` generated release with:
  - `common_{tier}.txt`, `common_{tier}.json.gz`, `common_{tier}.bf`, optional `common_{tier}.trie`
  - `metadata.json` (includes version, date, counts, sha256 per file, provenance, Bloom params)
- `packages/`
- `javascript/` (TypeScript, ESM + tiny UMD)
  - `src/index.ts` (`initialize`, `is_common`, `version`); `src/bloom.ts`
  - `package.json`, `tsconfig.json`, `vitest.config.ts`
  - `test/` unit tests; `examples/node.mjs`, `examples/browser.html`
  - bundling via `tsup` (min deps), asset loader for `.bf`
- `python/`
  - `src/commonpasswords/__init__.py`, `core.py`, `bloom.py`, `normalize.py`, `version.py`
  - `pyproject.toml` (PEP 621), `README.md`
  - `tests/` with pytest
- Skeletons for `go/`, `rust/`, `java/`, `csharp/` (readme + stubs)
- `ci/`
- GitHub Actions: `lint-and-test.yml`, `dataset-build.yml`, `release.yml`

## Dataset Pipeline (Python)

- Input: newline-separated raw lists under `datasets/raw/` with synthetic `SAMPLE_*` entries; optional `freq` format `password, count`.
- Processing:
- NFC normalize; trim; optional locale segmentation; no silent char drops unless configured.
- Deduplicate merging counts; sort by frequency desc; deterministic tie-breaking by lexicographic order.
- Split tiers: `tiny` (1k), `small` (10k), `medium` (100k), `full` (all)
- Outputs per tier:
- `.txt`: newline list
- `.json.gz`: `{ meta: {version, locale:"global", count, sha256_txt, sha256_bf, bloom_params }, data: [ ... ] }`
- `.bf`: header (JSON with params + 1 newline) + raw bit-array bytes
- `.trie` (optional): compact prefix map for server use
- Metadata `metadata.json`:
- `{ version, date, sources: [...], counts: {tiny, small, medium, full}, files: {name, sha256, size}, bloom: {expected_n, fpr, hash_count, bit_size} }`
- Reproducibility:
- Version `vYYYYMMDD.1` derived from current UTC date; deterministic sorting, seeds fixed.

## Language Bindings

- Shared API:
- `initialize(options)` with `{ tier, locale, normalization, load_mode: "inline"|"stream"|"remote" }`
- `is_common(password)` -> `{ common: boolean, reason?: string, version?: string }`
- `version()` -> `{ dataset: string, checksum: string }`

### JavaScript (Node/Browser)

- Default: client loads `tiny` Bloom over HTTP (browser) or from fs (Node); `preserve_unicode` normalization + trim.
- Implement portable Bloom load from `.bf` (parse JSON header, map bit-array into typed array) with double-hash strategy.
- Tests: normalization, Bloom positive/negative checks, deterministic results from canonical inputs.
- Example: Node script reading local `.bf`; browser demo fetching `.bf` from `datasets/<ver>/`.

### Python

- Pure-Python Bloom + normalization; load `.bf` header and bit-array; same hashing and parameters as JS.
- `import commonpasswords as cp`; `cp.initialize(...)`, `cp.is_common("password")`.
- Tests with pytest: same canonical inputs as JS to ensure identical results.

## Cross-language Integration Test

- Canonical inputs: handful present/absent strings from `common_tiny.txt`.
- Script `tools/integration/check_consistency.py` runs JS (node) and Python and compares booleans for each input; used in CI.

## CI (GitHub Actions)

- `lint-and-test.yml`: matrix for Node LTS + Py 3.10–3.12; runs unit tests and integration test.
- `dataset-build.yml`: builds dataset from samples, uploads artifacts, verifies checksums in `metadata.json`.
- `release.yml`: on tag `v*`, packages JS/Python and attaches dataset artifacts; generates release notes from `CHANGELOG.md`.

## Docs & Governance

- Root `README.md`: quickstart for JS/Python, dataset tiers, normalization policy.
- `SECURITY.md`: policy + contact `abdelkarim.contact1@gmail.com`.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `NOTICE` with dataset provenance.

## Runbook (after implementation)

- Build dataset: `python datasets/pipeline/build.py --version vYYYYMMDD.1 --sources datasets/raw/*.txt --out datasets`
- JS tests: `pnpm i && pnpm -C packages/javascript test`
- Py tests: `pipx run poetry install && poetry -C packages/python run pytest` (or `pip install -e . && pytest`)
- Integration: `python tools/integration/check_consistency.py --version vYYYYMMDD.1`
- Release: `bash release/release.sh v0.1.0 vYYYYMMDD.1`

### To-dos

- [ ] Create monorepo scaffold, root docs, licenses, ci directory
- [ ] Implement Python dataset pipeline and Bloom/trie exporters
- [ ] Add SAMPLE raw sources and generate vYYYYMMDD.1 artifacts
- [ ] Implement JS package (@commonpass/commonpasswords) with Bloom loader
- [ ] Add JS tests and Node/browser examples
- [ ] Implement Python package (commonpasswords) with Bloom loader
- [ ] Add Python tests and examples
- [ ] Implement cross-language consistency test script
- [ ] Add GitHub Actions for lint, tests, dataset build, release
- [ ] Write README, SECURITY, CONTRIBUTING, CHANGELOG, NOTICE
- [ ] Create release script to package artifacts and tag v0.1.0