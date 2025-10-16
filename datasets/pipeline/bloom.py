import hashlib
import json
from datetime import datetime, timezone


class Bloom:
    """Portable Bloom filter with SHA-256 double-hash and big-endian bit layout."""

    def __init__(self, bit_size: int, hash_count: int):
        self.bit_size = bit_size
        self.hash_count = hash_count
        self.bits = bytearray((bit_size + 7) // 8)

    def _hashes(self, s: str):
        b = s.encode("utf-8")
        h1 = int.from_bytes(hashlib.sha256(b + b"\x00").digest(), "big")
        h2 = int.from_bytes(hashlib.sha256(b + b"\x01").digest(), "big")
        for i in range(self.hash_count):
            yield (h1 + i * h2) % self.bit_size

    def add(self, s: str):
        for idx in self._hashes(s):
            byte_index = idx // 8
            bit_index = 7 - (idx % 8)  # big-endian bit layout
            self.bits[byte_index] |= (1 << bit_index)

    def serialize(self, params_meta: dict) -> bytes:
        header = {
            "format": "commonpass-bloom-v1",
            "bit_size": self.bit_size,
            "hash_count": self.hash_count,
            "hash_algo": "sha256",
            **params_meta,
        }
        header_bytes = (json.dumps(header, separators=(",", ":")) + "\n").encode("utf-8")
        return header_bytes + bytes(self.bits)


def optimal_bloom_params(n: int, fpr: float):
    import math
    if n <= 0:
        return 8 * 1024, 3
    m = int(-(n * math.log(fpr)) / (math.log(2) ** 2))
    k = max(1, int((m / max(1, n)) * math.log(2)))
    m = (m + 7) // 8 * 8
    return max(8 * 1024, m), k


