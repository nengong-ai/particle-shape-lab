#!/usr/bin/env python3
"""Build an original, NON-RENDERING API stub export for tsc/Vite checks only.

No upstream engine or artwork is used. A successful build is not visual acceptance.
The test-only hash contract is injected in Python; the production CLI cannot use it.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from export import export_project
from shape import convert

# Entire fixture authored for these tests. This API stub never draws anything.
STUB = '''// Original test-only API stub. NOT A RENDERER. No visual validation.
export const ASTRA_SHAPE_SVGS: Record<string, unknown> = {};
type Options = {
  heroElement: HTMLElement;
  contentElement: HTMLElement;
  cues: HTMLElement[];
  data: unknown;
  onError(error: unknown): void;
};
export function createAstraScene(_canvas: HTMLCanvasElement, _options: Options) {
  return { ready: Promise.resolve(), replay() {}, dispose() {} };
}
'''
NOTICE = b'Original test-only API stub; no third-party renderer is included.\n'
SVG = b'<svg viewBox="0 0 12 8"><path d="M1 1H6V7H1Z M9 2H11V4H9Z"/></svg>'


def write_runtime(root):
    """Create only original stub files; return their temporary test contract."""
    files = {
        'src/particles/engine.ts': STUB.encode(),
        'src/particles/core/README.md': NOTICE,
        'src/lib/assets/test-stub.txt': b'Original plain-text asset fixture, not artwork.\n',
        'LICENSE': NOTICE,
    }
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return {'schemaVersion': 1, 'contracts': {'original-test-stub': {'files': {
        name: hashlib.sha256(data).hexdigest() for name, data in files.items()
    }}}}


def build_fixture(out):
    out = Path(out).absolute()
    resolved = out.resolve()
    if resolved == ROOT or ROOT in resolved.parents or resolved in ROOT.parents:
        raise ValueError('Fixture export must be outside the repository.')
    if any(p.is_symlink() for p in [out, *out.parents]):
        raise ValueError('Fixture output cannot use symlinks.')
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError('Fixture output must be new or empty.')
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='api-stub-', dir=out.parent) as scratch:
        scratch = Path(scratch)
        contract = write_runtime(scratch / 'runtime')
        source = scratch / 'own-shape.svg'
        source.write_bytes(SVG)
        convert(source, scratch / 'shape', title='Non-rendering API build fixture')
        result = export_project(scratch / 'runtime', scratch / 'shape/shape.json', out,
                                contracts=contract)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_fixture(args.out)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({'out': str(args.out.resolve()), 'stubOnly': True,
                      'browserVerified': result['browserVerified']}))
