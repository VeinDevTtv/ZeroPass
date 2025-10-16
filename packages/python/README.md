# commonpasswords (Python)

Minimal Python binding to load CommonPasswords Bloom filter and check passwords.

## Usage
```python
import commonpasswords as cp
cp.initialize(tier="tiny", version="vYYYYMMDD.1")
print(cp.is_common("password"))
```
