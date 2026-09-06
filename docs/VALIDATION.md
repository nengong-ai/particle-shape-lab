# Validation status for 0.1.0

## Completed locally

Environment: macOS ARM64, Python 3.12.14 and Node 24.19.0.

- A new virtual environment installed Pillow 12.3.0 and NumPy 2.3.5 from PyPI without reusing the previous application environment.
- 28 unit tests passed, including 80 deterministic random contour round-trips. Tests cover SVG holes and active metadata rejection, PNG polarity/16-bit input, original preservation, destination protection, runtime tampering and symlink ancestors.
- An independently authored, non-rendering API fixture was exported. A fresh `npm ci` installed 33 packages; TypeScript and Vite builds passed. The fixture is only a contract/build test.
- The optional real-runtime integration used 34 files freshly retrieved from the fixed upstream commit through the GitHub read API. Their Git blob hashes and contract SHA-256 values matched. These files were kept outside the public repository.
- The real export installed another independent node_modules tree from npm, without links to old project dependencies. TypeScript and Vite builds passed.
- The local real-runtime page displayed the original two-window example and its detached triangle. Rotation, drag/release, replay, hide/restore, continuous motion and a 390×844 viewport were visually checked. No console errors or warnings were observed. Screenshots and the third-party local export are intentionally outside this public tree.

Testing found and corrected active metadata acceptance, missing original-input export, runtime ancestor symlink validation, and root lockfile license metadata. A visible restore button was added so hiding controls does not require a hardware keyboard to recover them.

The dependency package-lock records exact resolutions. The known Vite large-bundle warning remains in the external renderer build; it is not treated as a build failure.

## Configured, not yet executed remotely

The GitHub Actions workflow is prepared for Python 3.12 on Ubuntu/macOS/Windows and a Node 22/24 adapter-fixture build on Ubuntu. It does not download an engine, publish a viewer or upload third-party artifacts.

No GitHub repository or remote workflow run was created during this preparation. Therefore remote CI is **not yet reported as passing**, and local directory isolation is not claimed as a second physical machine or a Windows/Linux validation.

The workflow environment scopes were checked against GitHub's [context availability reference](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#context-availability); runner-dependent paths are used in step environments, not unsupported job-level contexts.

## What these checks do not establish

They do not establish ownership or redistribution rights for an externally supplied engine or user input. They do not prove private brand animations, arbitrary SVG support, 3D reconstruction, mobile-device behavior, long-term stability or GPU/recording FPS. The complete private project and its existing license status remain separate.
