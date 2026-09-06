# Particle Showcase Public

Small SVG/PNG input tools, plus an **optional bridge to a separately supplied particle renderer**.

This repository does not contain a particle engine or official brand assets. SVG/PNG conversion works independently. Interactive rendering additionally requires a compatible external runtime that you are entitled to use. This public version does not include the private renderer patches or brand-specific animations.

![Original two-window beacon input](examples/beacon.svg)

## Convert an input

Use Python 3.12. SVG conversion uses only the standard library; PNG conversion needs the separately installed Pillow and NumPy versions in `requirements.txt`.

```sh
python -m venv .venv
# Activate the environment using your platform's normal command.
python -m pip install -r requirements.txt
python scripts/shape.py --input examples/beacon.svg --out ../beacon-shape
```

For a transparent or black/white PNG:

```sh
python scripts/shape.py --input /path/to/logo.png --out ../logo-shape
```

The output contains `shape.json`, `normalized.svg`, the original input, and a manifest. PNG adds a traced SVG and threshold/crop/topology information. Conversion never reports browser acceptance automatically.

### Supported inputs

- SVG: explicit positive `viewBox`, monochrome closed paths, nonzero/evenodd holes, separate parts, and groups without transforms.
- PNG: static transparent silhouettes or opaque grayscale; automatic alpha/dark/light selection. Use `--foreground alpha|dark|light` after inspecting an ambiguous image; `--threshold` defaults to 128.
- 16-bit grayscale PNG is normalized across its full range. Other 16-bit color formats are rejected.
- SVG viewBox and coordinates are retained; PNG empty margins are cropped.

Transforms, strokes, text, masks, clipping, gradients, scripts and active metadata are rejected. This is not photo segmentation, a complete SVG editor, or 3D reconstruction. Tiny features may not survive a renderer's sampling/bloom even when the vector trace preserves the thresholded pixels exactly.

## Optional interactive export

First supply a supported external runtime directory. See [runtime setup](docs/RUNTIME.md) and [license scope](THIRD_PARTY.md). The runtime is checked against fixed file hashes; there is no option to bypass the check.

```sh
python scripts/export.py \
  --runtime /path/to/compatible-runtime \
  --shape ../beacon-shape/shape.json \
  --dest ../beacon-particles
cd ../beacon-particles
npm ci
node build.mjs --check
node build.mjs
python serve.py --port 4195
```

Open `http://127.0.0.1:4195/`. Drag or use arrow keys to rotate, use R to replay, H to hide controls, and Esc to restore them. The public bridge calls the external API without patching its source. It uses a measured shape cue, so path rotation does not require a private hero-rotation patch.

Node.js 22.13+ is required to build. Installed dependencies are local to the export; this tool does not link to a previous project's node_modules. Once built, viewing needs only Python's local HTTP server and a WebGL-capable browser, not Node or the original runtime folder. The server exposes only dist.

**Keep local exports outside this repository.** They contain the supplied external runtime and keep its original license status. The tool's MIT license does not cover that copied runtime or your inputs.

## Test

```sh
python -m unittest discover -s tests -v
```

The GitHub Actions workflow installs fresh dependencies and checks conversion, boundaries, and a self-authored API/build fixture. It does not fetch or publish an unlicensed engine. The fixture proves adapter/build wiring, not particle visuals. [Validation notes](docs/VALIDATION.md) distinguish local real-runtime verification from CI, including the verified Ubuntu/macOS/Windows and Node 22/24 run.

## License and relationship to the local version

[MIT](LICENSE) covers this public tool repository. External runtimes, user inputs and installed dependencies retain their own terms; read [THIRD_PARTY.md](THIRD_PARTY.md).

The complete local version retains the renderer-specific sparkle patches and brand animation examples. Those files have not been silently repackaged here. This public repository is a smaller input-and-integration tool, not a claim to have independently written or relicensed the external engine.
