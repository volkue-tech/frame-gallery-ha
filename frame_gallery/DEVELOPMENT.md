# Development

All commands run from this directory (`frame_gallery/`). The environment is managed with `uv` 0.12.19 (D-128), pinned in `pyproject.toml` (`required-version`).

## Environment

`uv` never downloads Python interpreters for this project (`python-downloads = "never"`), so a local CPython 3.12, 3.13, or 3.14 must be available. Point `UV_PYTHON` at it if it is not on `PATH`.

```bash
uv sync --locked
```

The lock (`uv.lock`) pins every package with hashes. It covers macOS (development) and Linux (the container) only.

## Quality gates (§20.4)

```bash
scripts/check.sh
```

The script runs, and fails on the first failure:

1. `ruff check` and `ruff format --check`;
2. `mypy` in strict mode, over `src` and `tests`;
3. `pytest` with branch coverage: at least 90 % overall, and 100 % of lines and branches for the modules the architecture requires (§20.4): `budget`, `net` (the whole package, including the real transport), `selection`, `isolation`, `providers`, the outcome classification and the runner, and the imaging worker tasks with their header pre-scan and JPEG header parser.

`mypy` runs in strict mode over `src` and `tests`, with no per-module relaxations.

Tests never use the network (acceptance item `H2`). For the whole session, collection included, `tests/conftest.py` makes these raise: `connect`, `connect_ex`, `sendto`, and `sendmsg` on `socket.socket`; `socket.create_connection`; and `getaddrinfo`, `gethostbyname`, `gethostbyname_ex`, `gethostbyaddr`, and `getnameinfo` on both `socket` and `_socket`. The architecture boundary test enforces the import rules of D-107, D-145, and D-147, and proves with self-tests that each of its detectors fires. Only `net/transport.py` may import `socket`, `ssl`, `http.client`, `urllib3`, and `certifi`, and only the entry point may import that module; the gateway and the adapters are tested against the fakes in `tests/support/net.py`. Tests never use the real project contact in a header: they pass a placeholder identity (D-119).

## Runtime requirements

`requirements/runtime.txt` is exported from the lock, with hashes, for the container build (Phase 6):

```bash
uv export --locked --no-dev --no-emit-project --format requirements-txt -o requirements/runtime.txt
```

Regenerate it whenever `uv.lock` changes. Pillow and `samsungtvws` are upgraded only in dedicated commits, with the full test suite and an updated inventory (D-128).
