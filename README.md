# CommonPasswords (monorepo)

Secure, portable, and well-tested datasets and libraries to detect common/compromised passwords.

- Datasets: versioned, normalized, multi-format (txt, json.gz, Bloom .bf, optional .trie).
- Language bindings: JavaScript (Node/Browser) and Python initially, others planned.
- Consistent API across languages: `initialize`, `is_common`, `version`.

## Quickstart

### Build dataset (sample sources)
```bash
python datasets/pipeline/build.py --version vYYYYMMDD.1 --sources datasets/raw/*.txt --out datasets
```

### JavaScript (Node)
```bash
pnpm -C packages/javascript install
pnpm -C packages/javascript test
```

### Python
```bash
pip install -e packages/python
pytest packages/python
```

See `SECURITY.md` for responsible disclosure. See `rules.md` for detailed governance and design rules.

## Repository layout
- `datasets/` — raw sources, pipeline, versioned outputs
- `packages/` — language bindings
- `ci/` — GitHub Actions
- `release/` — release scripts

## License
MIT
