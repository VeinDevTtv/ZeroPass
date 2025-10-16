#!/usr/bin/env python3
import argparse
import gzip
import hashlib
import io
import json
import os
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone


def normalize(s: str) -> str:
    # NFC + trim; do not drop characters silently
    return unicodedata.normalize("NFC", s).strip()


def load_sources(paths):
    counts = Counter()
    sources = []
    for p in paths:
        sources.append(os.path.basename(p))
        with open(p, "r", encoding="utf-8", errors="strict") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                if "," in line:
                    # format: password,count
                    try:
                        pw, cnt = line.split(",", 1)
                        pw_n = normalize(pw)
                        cnt_i = int(cnt.strip())
                        if pw_n:
                            counts[pw_n] += max(0, cnt_i)
                    except Exception:
                        continue
                else:
                    pw_n = normalize(line)
                    if pw_n:
                        counts[pw_n] += 1
    return counts, sources


def deterministic_sorted_items(counts: Counter):
    # sort by frequency desc, then lexicographically for determinism
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def split_tiers(items):
    pw_list = [pw for pw, _ in items]
    tiers = {
        "tiny": pw_list[:1000],
        "small": pw_list[:10000],
        "medium": pw_list[:100000],
        "full": pw_list,
    }
    return tiers


def compute_sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_txt(path, entries):
    data = ("\n".join(entries) + "\n").encode("utf-8") if entries else b""
    with open(path, "wb") as f:
        f.write(data)
    return compute_sha256_bytes(data), len(data)


def write_json_gz(path, version, tier, entries, bloom_sha, bloom_params):
    payload = {
        "meta": {
            "version": version,
            "tier": tier,
            "count": len(entries),
            "bloom_params": bloom_params,
            "sha256_bf": bloom_sha,
        },
        "data": entries,
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(raw)
    with open(path, "wb") as f:
        f.write(gz)
    return compute_sha256_bytes(gz), len(gz)


class Bloom:
    # Simple portable Bloom filter with double hashing
    def __init__(self, bit_size: int, hash_count: int):
        self.bit_size = bit_size
        self.hash_count = hash_count
        self.bits = bytearray((bit_size + 7) // 8)

    def _hashes(self, s: str):
        b = s.encode("utf-8")
        h1 = int.from_bytes(hashlib.sha256(b).digest()[:8], "big")
        h2 = int.from_bytes(hashlib.blake2b(b, digest_size=8).digest(), "big")
        for i in range(self.hash_count):
            yield (h1 + i * h2) % self.bit_size

    def add(self, s: str):
        for idx in self._hashes(s):
            self.bits[idx // 8] |= (1 << (idx % 8))

    def serialize(self, params_meta: dict) -> bytes:
        header = {
            "format": "commonpass-bloom-v1",
            "bit_size": self.bit_size,
            "hash_count": self.hash_count,
            **params_meta,
        }
        header_bytes = (json.dumps(header, separators=(",", ":")) + "\n").encode("utf-8")
        return header_bytes + bytes(self.bits)


def optimal_bloom_params(n: int, fpr: float):
    # m = -(n * ln(p)) / (ln 2)^2 ; k = (m/n) * ln 2
    import math
    if n <= 0:
        return 8 * 1024, 3
    m = int(-(n * math.log(fpr)) / (math.log(2) ** 2))
    k = max(1, int((m / max(1, n)) * math.log(2)))
    # round bit size to multiple of 8
    m = (m + 7) // 8 * 8
    return max(8 * 1024, m), k


def write_bloom(path, entries, expected_n, fpr, version, tier):
    bit_size, hash_count = optimal_bloom_params(expected_n, fpr)
    bloom = Bloom(bit_size, hash_count)
    for pw in entries:
        bloom.add(pw)
    blob = bloom.serialize({"expected_n": expected_n, "fpr": fpr, "version": version, "tier": tier})
    with open(path, "wb") as f:
        f.write(blob)
    return compute_sha256_bytes(blob), len(blob), {"expected_n": expected_n, "fpr": fpr, "hash_count": hash_count, "bit_size": bit_size}


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=False, help="dataset version like vYYYYMMDD.1")
    ap.add_argument("--sources", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fpr", type=float, default=0.01)
    args = ap.parse_args()

    version = args.version or ("v" + datetime.now(timezone.utc).strftime("%Y%m%d") + ".1")
    counts, sources = load_sources(args.sources)
    items = deterministic_sorted_items(counts)
    tiers = split_tiers(items)

    out_dir = os.path.join(args.out, version)
    ensure_dir(out_dir)

    meta = {
        "version": version,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "sources": sources,
        "counts": {k: len(v) for k, v in tiers.items()},
        "files": [],
        "bloom": {},
    }

    for tier, entries in tiers.items():
        txt_path = os.path.join(out_dir, f"common_{tier}.txt")
        bf_path = os.path.join(out_dir, f"common_{tier}.bf")
        json_path = os.path.join(out_dir, f"common_{tier}.json.gz")

        sha_txt, size_txt = write_txt(txt_path, entries)
        sha_bf, size_bf, bloom_params = write_bloom(bf_path, entries, expected_n=max(1, len(entries)), fpr=args.fpr, version=version, tier=tier)
        sha_json, size_json = write_json_gz(json_path, version, tier, entries, sha_bf, bloom_params)

        meta["files"].extend([
            {"name": f"common_{tier}.txt", "sha256": sha_txt, "size": size_txt},
            {"name": f"common_{tier}.bf", "sha256": sha_bf, "size": size_bf},
            {"name": f"common_{tier}.json.gz", "sha256": sha_json, "size": size_json},
        ])
        if tier == "tiny":
            meta["bloom"] = bloom_params

    with open(os.path.join(out_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(json.dumps({"version": version, "out": out_dir, "counts": meta["counts"]}))


if __name__ == "__main__":
    sys.exit(main())


