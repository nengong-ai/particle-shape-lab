# Particle Shape Lab

**English** | [简体中文](README.zh-CN.md)

**Turn SVGs and images into clean, reusable shape data for particle renderers.**

![ChatGPT particle showcase](assets/chatgpt.gif)

| Claude | DeepSeek |
| --- | --- |
| ![Claude particle showcase](assets/claude.gif) | ![DeepSeek particle showcase](assets/deepseek.gif) |

*These renders come from a separate brand demonstration using an external engine and brand-specific presets. That engine and those presets are not included in this public toolkit. See [preview asset notes](assets/README.md).*

Particle Shape Lab is a graphics-processing toolkit designed for **AI Agents and automated creative workflows**.

Give it a simple SVG, transparent PNG, or black-and-white silhouette, and it converts the input into normalized graphics and standardized shape data that can be consumed by compatible particle renderers.

Where possible, it preserves important structural details such as:

* outer contours
* internal holes
* disconnected components
* relative proportions and layout

Connect the generated data to a compatible external particle engine, and you can build interactive showcase pages with features such as drag-to-rotate, replay, and hidden UI for clean recordings.

> **Important:** Particle Shape Lab does not include a complete particle rendering engine.
>
> The public repository provides graphics conversion tools, standardized shape data, and renderer integration adapters.
> Graphics conversion works independently. Dynamic particle rendering requires a compatible external engine.

---

## What it does

A typical workflow looks like this:

```text
SVG / Transparent PNG / B&W Shape
                ↓
      Particle Shape Lab
                ↓
     Normalized Shape Data
                ↓
       Your Particle Engine
                ↓
 Interactive particle showcase
```

Particle Shape Lab focuses on the middle of that pipeline.

Instead of repeatedly writing one-off scripts to validate simple SVGs, trace PNG contours, preserve holes, and adapt shape data for a renderer, the toolkit turns those steps into a reusable workflow.

---

## Highlights

### Built for AI Agent workflows

Particle Shape Lab is designed to fit naturally into Agent-driven pipelines.

An Agent can take a graphics input and run a predictable sequence:

```text
Read input
→ Detect format
→ Normalize geometry
→ Extract regions and contours
→ Generate shape data
→ Pass data to a renderer
```

The goal is simple: stop rebuilding the same graphics-preparation logic every time a new visual asset appears.

### Preserves holes and disconnected parts

Not every shape is a solid blob.

A useful graphics pipeline needs to understand things like:

* the hole inside the letter `O`
* hollow areas inside icons
* separate elements inside a logo
* multiple disconnected silhouettes

Particle Shape Lab attempts to preserve those structures instead of flattening everything into a single filled region.

### Supports practical input formats

The toolkit is primarily designed for:

* SVG
* transparent PNG
* black-and-white shapes

These formats cover many common use cases including logos, icons, symbols, simple typography, silhouettes, and generated vector assets.

### Standardized output

Inputs from different sources are converted into a consistent representation.

That means downstream particle systems do not need custom logic for every random SVG or image format encountered along the way.

They consume a predictable shape-data layer instead.

### Renderer integration

The public project also includes integration support for compatible external renderers.

Once connected to a particle engine, the resulting showcase can support capabilities such as:

* drag-to-rotate interaction
* animation replay
* hidden control UI
* clean recording mode
* logo and icon particle showcases

These rendering features come from the connected engine.

Particle Shape Lab prepares and adapts the data required to drive it.

---

## Use cases

### Logo and icon showcases

Convert logos, app icons, or brand symbols into shape data suitable for particle-based presentations, demos, landing pages, or video assets.

### Creative visual experiments

Quickly test how symbols, typography, silhouettes, or geometric graphics behave inside a particle system.

Spend less time repeating conversion steps and more time experimenting with the visual result. Unsupported inputs still need preparation in a graphics editor.

### Recording assets

When paired with a compatible renderer, Particle Shape Lab can help create clean interactive scenes for screen recording.

Typical controls may include:

* replaying an animation
* rotating the scene
* hiding UI controls
* adjusting the viewing angle
* capturing clean footage

Useful for short-form video, product demos, and visual content production.

### AI Agent pipelines

Particle Shape Lab can also act as one step inside a larger automated creative pipeline:

```text
User request
     ↓
AI Agent generates SVG
     ↓
Particle Shape Lab converts it
     ↓
External particle renderer
     ↓
Interactive page / recording asset
```

This creates a stable interface between **graphics generation** and **particle rendering**.

---

## Quick start

Particle Shape Lab can be used purely as a graphics-conversion tool, or as the preparation layer for a larger particle-rendering workflow.

### 1. Prepare an input

Start with a simple graphic:

```text
input/
├── logo.svg
├── icon.png
└── shape.png
```

For best results, SVG is generally preferred when a clean vector source is available.

For PNG inputs, use images with:

* transparent backgrounds
* clear subject boundaries
* strong contrast
* sufficient resolution
* minimal unnecessary texture

---

### 2. Convert the graphic

Use Python 3.12 from the repository root. SVG conversion uses only the standard library. Start with the included example:

```sh
python scripts/shape.py --input examples/beacon.svg --out ../beacon-shape
```

PNG conversion additionally needs Pillow and NumPy. If those dependencies are not available, create an isolated environment and install the pinned versions:

```sh
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/shape.py --input examples/beacon.png --out ../beacon-png-shape
```

`python` should resolve to Python 3.12. The output directory must be new or empty. Actual outputs are:

```text
beacon-shape/
├── original.svg       # original.png for PNG input
├── normalized.svg
├── shape.json
└── manifest.json
```

PNG conversion also produces `traced.svg`. The manifest records source hashes, conversion settings, and checks. Creating these files does not establish browser or visual acceptance.

---

### 3. Use the generated shape data

At this point, the core Particle Shape Lab conversion workflow is complete.

The resulting data can be used by:

* custom WebGL applications
* Three.js scenes
* Canvas-based renderers
* existing particle systems
* other Agent tools
* graphics-processing pipelines

Custom renderers need their own adapter for `shape.json`. The bundled exporter supports only the fixed runtime contracts listed in [runtime setup](docs/RUNTIME.md).

A particle showcase page is optional.

The shape conversion pipeline is useful on its own.

---

### 4. Optional: connect a particle renderer

If you have a runtime matching a supported fixed contract and the rights to use it, follow [runtime setup](docs/RUNTIME.md). Keep the export outside both this repository and the runtime directory:

```sh
python scripts/export.py --runtime /path/to/compatible-runtime --shape ../beacon-shape/shape.json --dest ../beacon-particles
cd ../beacon-particles
npm ci
node build.mjs --check
node build.mjs
python serve.py --port 4195
```

Open `http://127.0.0.1:4195/`. Drag or use arrow keys to rotate, R to replay, H to hide controls, and Esc or the restore button to show them. Building requires Node.js 22.13+; viewing requires a WebGL-capable browser. Stop the local server with Ctrl+C.

`npm ci` downloads dependencies and runs their configured installation scripts. Install only in the new export directory; no global install or symlink to another project's node_modules is needed.

The full pipeline becomes:

```text
Graphic
  ↓
Particle Shape Lab
  ↓
Shape Data
  ↓
External Particle Renderer
  ↓
Interactive Showcase
```

Depending on the renderer, the final experience may include:

* particle assembly and dispersion
* drag or arrow-key rotation
* animation replay
* UI hiding
* recording-friendly presentation modes

These capabilities belong to the rendering layer and are **not provided by a bundled particle engine in this repository**.

---

## Input requirements

Particle Shape Lab works best with simple, clearly defined graphics.

### SVG

Currently accepted:

* an explicit `viewBox` with positive width and height
* 1–32 monochrome closed `<path>` elements, with each contour closed by `Z`
* `nonzero` / `evenodd` holes and disconnected components
* groups without transforms; files up to 256 KB

Convert basic shapes, text, and strokes to closed paths first. **Transforms, `<text>`, masks, clip paths, filters, gradients, patterns, scripts, and external resource references are rejected**, not merely discouraged when complex. Prepare these inputs in a graphics editor instead of bypassing validation.

SVG coordinates and viewBox are retained. White overlays do not create holes; use compound contours. Small details preserved in the data may still become hard to distinguish after particle sampling and bloom.

---

### Transparent PNG

Recommended:

* transparent background
* clearly defined subject
* clean alpha channel
* sharp boundaries
* minimal soft shadows
* limited texture

PNG inputs depend on contour and region extraction, so image quality directly affects the generated shape data.

Only static PNG is supported: up to 4,194,304 pixels and 4096 pixels on either side. Automatic foreground detection selects alpha, dark, or light; use `--foreground alpha|dark|light` and `--threshold` (default 128) for ambiguous inputs. Transparent inputs use alpha; dark/light modes require opaque grayscale. Only grayscale is supported at 16-bit depth; convert other 16-bit color inputs first.

Empty outer margins are cropped while internal structure is retained. Inputs exceeding contour complexity limits are rejected rather than silently losing small components.

Photographs, complex gradients, and heavily textured images are generally poor candidates without preprocessing.

---

### Black-and-white shapes

Black-and-white inputs should provide a clear distinction between foreground and background.

Good examples include:

* icons
* character outlines
* logos
* silhouettes
* geometric symbols

Images containing heavy compression artifacts, noise, or blurred edges should ideally be cleaned before conversion.

---

## What Particle Shape Lab is not

To keep expectations clear, this project is **not**:

* a complete particle rendering engine
* a one-click image-to-animation generator
* a full Three.js or WebGL visualization framework
* a general-purpose SVG renderer
* an image-effects platform

A more accurate description is:

> **A reusable graphics-normalization and adapter layer between static visual assets and particle renderers.**

If you already have a particle engine, Particle Shape Lab removes much of the repetitive graphics-preparation work required to feed assets into it.

If you do not have a particle engine, the conversion and shape-data generation tools can still be used independently.

---

## Dependencies

Particle Shape Lab has two conceptually separate dependency layers.

### Conversion dependencies

These are used for tasks such as:

* SVG parsing
* PNG and alpha-channel processing
* contour extraction
* region detection
* geometry normalization
* shape-data generation

SVG conversion uses the Python 3.12 standard library. PNG uses the Pillow and NumPy versions pinned in [requirements.txt](requirements.txt).

### Rendering dependencies

Rendering dependencies are **not bundled as a complete particle engine**.

To create dynamic particle showcases, provide a compatible rendering environment or engine based on technologies such as:

* WebGL
* Three.js
* Canvas
* custom GPU particle systems

These are possible targets for custom adapters, not a promise of universal built-in compatibility. The exporter supports fixed runtime contracts; [package-lock.json](package-lock.json) pins build dependencies and [THIRD_PARTY.md](THIRD_PARTY.md) explains license scope.

---

## Repository scope

The public version focuses on:

* graphics input processing
* geometry normalization
* shape-data generation
* preservation of holes and disconnected components
* reusable Agent-oriented conversion workflows
* adapters for external particle renderers
* examples and documentation

The repository does **not** redistribute third-party or private particle rendering engines that are not part of this project.

Examples that depend on additional rendering components may require separate setup.

---

## Validation

```sh
python -m unittest discover -s tests -v
```

[Validation notes](docs/VALIDATION.md) distinguish unit tests, GitHub CI, and actual page checks. The original non-rendering fixture checks adapter/build wiring, not particle visuals. Inspect new inputs in their actual renderer.

## License

Particle Shape Lab source code is licensed under the terms specified in the repository's `LICENSE` file.

MIT covers this toolkit’s code, documentation, and original generic test examples. **Brand logos and the demonstration GIFs are not relicensed under MIT by being included here.** They illustrate visual results and do not imply brand affiliation or endorsement. See [third-party notices](THIRD_PARTY.md) and [preview asset notes](assets/README.md).

External particle engines, third-party libraries, fonts, logos, graphics, and other integrated resources remain subject to their own licenses and terms.

Before publishing, redistributing, or using the project commercially, make sure you have the appropriate rights for any external assets or dependencies involved.

---

## Why Particle Shape Lab?

Before a particle effect ever reaches the rendering stage, there is usually a surprisingly boring chain of preparation work:

```text
Find graphic
→ Fix SVG
→ Clean geometry
→ Preserve holes
→ Split disconnected parts
→ Normalize coordinates
→ Convert data
→ Adapt renderer input
→ Finally see the result
```

None of those steps is especially exciting.

Unfortunately, computers have yet to develop enough shame to stop making humans repeat them.

**Particle Shape Lab exists to turn that preparation layer into a reusable workflow.**

Start with a static graphic.

End with clean shape data that an Agent, renderer, or creative pipeline can actually use.
