# Separately supplied runtime

Shape conversion does not require a renderer. The optional export bridge accepts local directories matching `scripts/runtime-contracts.json`:

- `upstream-97c4de5`: the API subset from Hello-job/particle-showcase at `97c4de50117e86169c137fb62e26dd13e81059e1`.
- `local-runtime-1.0.0`: a compatible separately supplied local variant. This variant is not downloadable from this repository.

The source at the referenced upstream commit did not provide a project-wide open-source license. Its source URLs and this compatibility check do not grant permissions. Supply it only when you have the applicable rights; do not infer that this repository authorizes redistribution. The public tool never downloads a runtime automatically.

If you are entitled to obtain and use that upstream source, an ordinary local checkout must preserve its exact version and LF bytes:

```sh
git -c core.autocrlf=false clone https://github.com/Hello-job/particle-showcase.git external-runtime
git -C external-runtime checkout --detach 97c4de50117e86169c137fb62e26dd13e81059e1
```

Keep that checkout outside this public repository. You can instead supply an already acquired compatible directory. Runtime changes fail the manifest check; do not disable validation to make a different version pass.

The bridge reads only the approved engine/API files and notices. It copies them into your local export, preserves their notices, and adds the project-authored input adapter and screen controls. It does not run a runtime-supplied install script, copy a runtime package manifest, or reuse an old node_modules tree; the export uses this tool's dependency manifest and lockfile.

The output is not a blanket MIT project. Review its preserved notices before any further use or redistribution. `export.json` records which contract and hashes were used and whether original input was present; visual verification is a separate step.
