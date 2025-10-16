#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


def run_js(passwords, version):
    # Build dataset as needed
    subprocess.check_call([
        "python",
        "datasets/pipeline/build.py",
        "--version",
        version,
        "--sources",
        "datasets/raw/sample_global.txt",
        "--out",
        "datasets",
    ])
    # Use a Node one-liner to check passwords
    script = (
        "const { initialize, is_common } = require('./packages/javascript/dist/index.cjs');"
        f"initialize({{ tier: 'tiny', version: '{version}' }});"
        "const fs=require('fs'); const lines=fs.readFileSync('tools/integration/canonical_inputs.txt','utf8').trim().split(/\r?\n/);"
        "const out = lines.map(s => ({ s, c: is_common(s).common }));"
        "console.log(JSON.stringify(out));"
    )
    res = subprocess.check_output(["node", "-e", script])
    return json.loads(res)


def run_py(passwords, version):
    code = (
        "import json; "
        "import commonpass as cp; "
        f"cp.initialize(tier='tiny', version='{version}'); "
        "lines=open('tools/integration/canonical_inputs.txt','r',encoding='utf-8').read().strip().splitlines(); "
        "print(json.dumps([{ 's': s, 'c': cp.is_common(s)['common']} for s in lines]))"
    )
    res = subprocess.check_output([sys.executable, "-c", code])
    return json.loads(res)


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "20250101.1"
    passwords = Path("tools/integration/canonical_inputs.txt").read_text(encoding="utf-8").splitlines()
    js = run_js(passwords, version)
    py = run_py(passwords, version)
    mismatches = [(a['s'], a['c'], b['c']) for a, b in zip(js, py) if a['c'] != b['c']]
    if mismatches:
        print("MISMATCH:", mismatches)
        sys.exit(1)
    print("OK: JS and Python matched", len(passwords), "inputs")


if __name__ == "__main__":
    main()


