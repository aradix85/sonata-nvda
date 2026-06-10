# Contributing to Sonata Neural Voices (maintenance fork)

This is a maintenance fork of [mush42/sonata-nvda](https://github.com/mush42/sonata-nvda). The upstream author can no longer maintain the project ([announcement](https://nvda-addons.groups.io/g/nvda-addons/message/27636)); this fork carries compatibility fixes and minor improvements so the add-on keeps working on current NVDA releases.

Contributions are welcome.

## Reporting a bug

Use the **Bug report** template at <https://github.com/austek/sonata-nvda/issues/new/choose>. The template asks for NVDA version, add-on version, OS, voice tested, steps to reproduce, and an NVDA log slice — please fill in as much as you can. Bugs filed without that info almost always end up labelled `needs-reproducer` until they have it.

For installation questions or general usage help, check the [readme](readme.md) first and then ask on the [NVDA add-ons community list](https://nvda-addons.groups.io/g/nvda-addons).

## Suggesting a feature

Use the **Feature request** template. Describe the *problem* you're trying to solve, not just the proposed feature — that often suggests cleaner alternatives.

## Development setup

The add-on is built with [SCons](https://scons.org/) targeting Python 3.13 (the version embedded in NVDA 2026.1+). On Windows or any platform with Python 3.13:

```bash
python -m pip install --upgrade pip wheel
pip install scons markdown pytest
```

## Building the add-on

From the repo root:

```bash
scons
```

The build produces a `.nvda-addon` file in the repo root. Install it by opening the file in NVDA (NVDA menu → Tools → Manage add-ons → Install from external source).

To rebuild the translation template (`.pot`):

```bash
scons pot
```

## Running tests

```bash
pytest
```

The test suite (under `tests/`) covers add-on metadata, build helpers, the TTS system, and several pure-Python parsers extracted from the synth driver. Tests stub NVDA-only modules in `tests/conftest.py` so they can run outside the NVDA runtime.

## Refreshing the bundled binaries

The add-on bundles three native dependencies built for Python 3.13 / Windows x64:

```bash
python update_grpc.py        # gRPC + protobuf
python update_miniaudio.py   # audio decoding
python update_cffi.py        # C FFI runtime
```

Each script fetches the matching `cp313-win_amd64` wheel from PyPI and swaps the contents under `addon/synthDrivers/sonata_neural_voices/lib/`.

## Submitting a PR

Use the pull request template. Link the issue with `Closes #N` in the PR body — GitHub will auto-close the issue when the PR merges.

Conventions used in this fork:

- **Commit messages**: short imperative subject, blank line, then a body that explains *why*. Reference the relevant issue or upstream report (e.g. "Closes #5", "mirrored from upstream mush42/sonata-nvda#30").
- **PR titles**: same conventional-commits style as the lead commit (`fix:`, `feat:`, `chore:`, `docs:`).
- **Branch naming**: `fix/<short-slug>`, `feat/<short-slug>`, `chore/<short-slug>`.
- **No `Co-Authored-By` trailers.**

## Cutting a release

Releases are tag-driven. Push an annotated tag from `main`:

```bash
git tag -a v3.2-beta.N -m "v3.2-beta.N: <summary>"
git push origin v3.2-beta.N
```

CI builds on Ubuntu, runs pytest on `windows-latest`, and publishes a GitHub Release with the `.nvda-addon`, the `.pot`, and an auto-generated `changelog.md` containing the SHA256.

Note: `addon_version` in `buildVars.py` must remain strict three-part semver (e.g. `3.2.0`) — there's a test enforcing it. The `-beta.N` signal lives only in the git tag.
