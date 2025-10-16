import { initialize, is_common } from '../src/index';
import { execSync } from 'node:child_process';

it('initializes and checks', () => {
  execSync('python datasets/pipeline/build.py --version v20250101.1 --sources datasets/raw/sample_global.txt --out datasets', { stdio: 'inherit' });
  initialize({ tier: 'tiny', version: 'v20250101.1' });
  expect(is_common('SAMPLE_password').common).toBe(true);
  expect(is_common('totally_unique_candidate').common).toBe(false);
});


