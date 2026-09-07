# Code origin and license scope

The MIT license in this repository applies to this repository's tool code, documentation, and original generic test examples. It does not license an external renderer, user inputs, installed dependencies, or third-party content copied into a local export.

## What is included

The SVG validator, pixel-boundary PNG tracer, renderer-neutral data writer, optional API bridge, local build/server tools, and tests were written for this project. The bridge uses an external engine API; it does not contain that renderer's implementation. The contract JSON contains file paths and cryptographic digests, not the source of those files.

The original example `examples/beacon.svg` is simple project-created geometry, not a brand logo. CI's runtime fixture is independently written, does not render particles, and is only an API/build test. Passing that fixture is not visual acceptance.

## What is intentionally excluded

No renderer source, official brand SVGs, proprietary fonts, renderer reconstruction patches, private animation presets, copied upstream export script, compiled third-party viewer, or private runtime-building blueprint is included. The previous full local project is not being relicensed or released through this repository.

## Optional external engine

The current bridge has been tested with the API of [Hello-job/particle-showcase](https://github.com/Hello-job/particle-showcase) at commit `97c4de50117e86169c137fb62e26dd13e81059e1`, and a separately supplied local runtime variant. The referenced source's own license-status document did not provide a project-wide open-source license at that commit. Its availability online is not a license granted by this tool.

You supply the runtime locally and are responsible for having the applicable rights to use it. This tool does not download or redistribute it. Local exports preserve its license and source notices under `runtime-notices/` and the copied core README. An exported project contains that supplied code; do not redistribute the export merely because this input tool uses MIT.

The fixed manifest is a compatibility check, not an ownership or permission check. Removing brands alone would not have removed the copied engine patches; both have been left out of this public tree.

## Package dependencies

Pillow, NumPy, TypeScript, Vite, React, Three.js, postprocessing and their dependencies are obtained separately from package registries. They retain their own package licenses and notices. No dependency binaries or `node_modules` are bundled here. `requirements.txt` and `package-lock.json` record the dependency versions used in the local fresh-install verification.

## README demonstration images

The GIFs in assets/ are browser recordings of a separate brand showcase using an external renderer and brand-specific shapes and animation work. They are illustrations, not bundled renderer source or a guarantee that the public converter reproduces those presets. The OpenAI/ChatGPT, Claude and DeepSeek marks remain with their respective rights holders. These brand marks and demonstration GIFs are outside the toolkit MIT license. Their inclusion does not imply endorsement or affiliation. See assets/README.md for the capture and capability scope.
