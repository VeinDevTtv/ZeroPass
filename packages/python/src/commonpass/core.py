import json
import unicodedata
from typing import Optional, Dict, Any

_BLOOM: Dict[str, Any] = {"bits": None, "bit_size": 0, "hash_count": 0}
_DATASET_VERSION: Optional[str] = None


def _normalize(s: str) -> str:
    return unicodedata.normalize("NFC", s).strip()


def _parse_bloom(buf: bytes):
    nl = buf.find(b"\n")
    header = json.loads(buf[:nl].decode("utf-8"))
    bits = buf[nl + 1 :]
    return header, bits


def _hashes(s: str, bit_size: int, hash_count: int):
    import hashlib
    b = s.encode("utf-8")
    h1 = int.from_bytes(hashlib.sha256(b + b"\x00").digest(), "big")
    h2 = int.from_bytes(hashlib.sha256(b + b"\x01").digest(), "big")
    for i in range(hash_count):
        yield (h1 + i * h2) % bit_size


def initialize(tier: str = "tiny", version: Optional[str] = None, bf_path: Optional[str] = None):
    global _BLOOM, _DATASET_VERSION
    ver = version or "YYYYMMDD.1"
    path = bf_path or f"datasets/{ver}/common_{tier}.bf"
    with open(path, "rb") as f:
        header, bits = _parse_bloom(f.read())
    _BLOOM = {"bits": bits, "bit_size": header["bit_size"], "hash_count": header["hash_count"]}
    _DATASET_VERSION = header.get("version", ver)


def is_common(password: str) -> Dict[str, Any]:
    if not _BLOOM["bits"]:
        return {"common": False}
    s = _normalize(password)
    for idx in _hashes(s, _BLOOM["bit_size"], _BLOOM["hash_count"]):
        byte_index = idx // 8
        bit_index = 7 - (idx % 8)
        byte = _BLOOM["bits"][byte_index]
        mask = 1 << bit_index
        if (byte & mask) == 0:
            return {"common": False}
    return {"common": True, "reason": "bloom-match", "version": _DATASET_VERSION}


def version() -> Dict[str, Optional[str]]:
    return {"dataset": _DATASET_VERSION}


