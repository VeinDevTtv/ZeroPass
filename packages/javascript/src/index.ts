import { readFileSync } from 'node:fs';

type InitOptions = {
  tier?: 'tiny' | 'small' | 'medium' | 'full';
  normalization?: 'nfc_trim' | 'preserve_unicode';
  load_mode?: 'inline' | 'stream' | 'remote';
  bfPath?: string; // for Node inline mode
  version?: string;
};

export type CheckResult = { common: boolean; reason?: string; version?: string };

function normalize(input: string, mode: InitOptions['normalization']): string {
  if (mode === 'nfc_trim' || !mode) {
    return input.normalize('NFC').trim();
  }
  return input.trim();
}

function parseBloom(buffer: Uint8Array) {
  const newline = buffer.indexOf(10); // '\n'
  const headerJson = new TextDecoder().decode(buffer.slice(0, newline));
  const header = JSON.parse(headerJson);
  const bits = buffer.slice(newline + 1);
  return { header, bits };
}

function* hashes(s: string, bitSize: number, hashCount: number): Generator<number> {
  const enc = new TextEncoder();
  const b = enc.encode(s);
  const h1 = BigInt.asUintN(64, BigInt('0x' + require('crypto').createHash('sha256').update(b).digest('hex').slice(0,16)));
  const h2 = BigInt.asUintN(64, BigInt('0x' + require('crypto').createHash('blake2b512').update(b).digest('hex').slice(0,16)));
  const m = BigInt(bitSize);
  for (let i = 0; i < hashCount; i++) {
    const v = (h1 + BigInt(i) * h2) % m;
    yield Number(v);
  }
}

class Bloom {
  private bitSize: number;
  private hashCount: number;
  private bits: Uint8Array;
  constructor(bitSize: number, hashCount: number, bits: Uint8Array) {
    this.bitSize = bitSize;
    this.hashCount = hashCount;
    this.bits = bits;
  }
  has(s: string): boolean {
    for (const idx of hashes(s, this.bitSize, this.hashCount)) {
      const byte = this.bits[Math.floor(idx / 8)];
      const mask = 1 << (idx % 8);
      if ((byte & mask) === 0) return false;
    }
    return true;
  }
}

let bloom: Bloom | null = null;
let datasetVersion: string | undefined;

export function initialize(options: InitOptions = {}) {
  const tier = options.tier ?? 'tiny';
  const version = options.version ?? 'vYYYYMMDD.1';
  const bfPath = options.bfPath ?? `datasets/${version}/common_${tier}.bf`;
  const buf = readFileSync(bfPath);
  const { header, bits } = parseBloom(new Uint8Array(buf));
  bloom = new Bloom(header.bit_size, header.hash_count, bits);
  datasetVersion = header.version || version;
}

export function is_common(password: string, options: { normalization?: InitOptions['normalization'] } = {}): CheckResult {
  if (!bloom) return { common: false };
  const norm = normalize(password, options.normalization ?? 'nfc_trim');
  return bloom.has(norm) ? { common: true, reason: 'bloom-match', version: datasetVersion } : { common: false };
}

export function version(): { dataset: string | undefined } {
  return { dataset: datasetVersion };
}


