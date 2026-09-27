"""Architecture and import-boundary checks (§5, §20.4, D-107, D-125).

The static checks parse every module under ``src/frame_gallery`` that exists
when the tests run, so modules added later are covered without editing this
file. Each rule is a detector (one parsed module in, its violations out); the
``test_the_detectors_*`` tests run every detector over synthetic sources, so
the gate is shown to fail when a rule is broken. The runtime check imports the
parent-side package in a fresh interpreter and inspects ``sys.modules``. The
H2 network guard itself is tested in tests/unit/foundation/test_session_guards.py.
"""

from __future__ import annotations

import ast
import builtins
import json
import os
import re
import subprocess
import sys
import textwrap
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Final

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
PACKAGE = "frame_gallery"
PACKAGE_ROOT = SRC_ROOT / PACKAGE
IMAGING_ROOT = PACKAGE_ROOT / "imaging"
ISOLATION_ROOT = PACKAGE_ROOT / "isolation"
SELECTION_ROOT = PACKAGE_ROOT / "selection"
NET_ROOT = PACKAGE_ROOT / "net"
NET_TRANSPORT = NET_ROOT / "transport.py"
NET_TRANSPORT_MODULE = "frame_gallery.net.transport"
WORKER_TASKS = "frame_gallery.imaging.worker_tasks"
WORKER_PREFIX = "frame_gallery.imaging.worker_"
TV_WORKER = PACKAGE_ROOT / "tv" / "samsung_task.py"
TV_WORKER_MODULE = "frame_gallery.tv.samsung_task"
ISOLATION_PROCESS = ISOLATION_ROOT / "process.py"
ISOLATION_BOOTSTRAP = ISOLATION_ROOT / "bootstrap.py"
PROCESS_MODULE = "frame_gallery.isolation.process"
BOOTSTRAP_MODULE = "frame_gallery.isolation.bootstrap"
WORKER_MAIN_MODULE = "frame_gallery.isolation.worker_main"

TV_THIRD_PARTY = frozenset({"samsungtvws", "websocket", "requests"})
"""The television library and the two packages whose exception types the
television worker task catches: only in ``tv/samsung_task.py`` (Phase 5, D-107)."""

ALLOWED_THIRD_PARTY = frozenset({"PIL", "urllib3", "certifi", *TV_THIRD_PARTY})
"""Pillow only in ``imaging/worker_*.py`` (D-107); ``urllib3`` and ``certifi``
only in ``net/transport.py`` (Phase 3, D-131); the television library only in
the television worker task (Phase 5). Each extends this check deliberately."""

TRANSPORT_THIRD_PARTY = frozenset({"urllib3", "certifi"})
TRANSPORT_NETWORK_MODULES = frozenset({"socket", "ssl", "http"})
"""Networking modules that only ``net/transport.py`` may import (Phase 3)."""

NET_ONLY_MODULES = frozenset({"urllib.parse"})
"""Pure URL helpers that ``net`` modules may import; every other ``urllib``
module stays banned everywhere."""

BANNED_EVERYWHERE = frozenset(
    {
        "socket",
        "_socket",
        "ssl",
        "_ssl",
        "socketserver",
        "select",
        "selectors",
        "http",
        "urllib",
        "ftplib",
        "smtplib",
        "poplib",
        "imaplib",
        "xmlrpc",
        "asyncio",
        "subprocess",
        "multiprocessing",
        "concurrent",
        "pty",
        "ctypes",
        "telnetlib",
        "webbrowser",
    }
)
"""Networking, process and foreign-code modules banned in every module, with
deliberate exceptions: ``net/transport.py`` may import ``socket``, ``ssl``,
and ``http`` (Phase 3), and ``net`` modules may import ``urllib.parse``; from
Phase 5, ``isolation/process.py`` may import ``subprocess`` and ``select``,
``isolation/bootstrap.py`` ``ctypes`` (for ``prctl``), and the television
worker task ``socket`` (its connect guard). There is no ``asyncio`` at all
(D-106)."""

BANNED_IN_SELECTION = BANNED_EVERYWHERE | frozenset(
    {"os", "pathlib", "shutil", "tempfile", "glob", "io", "fileinput"}
)
"""Selection is pure: no file-system or network access (§5)."""

FILE_OPENERS = frozenset({"builtins.open", "io.open", "io.open_code", "_io.open", "codecs.open"})
"""File-opening callables that need no banned import; banned in selection."""

DYNAMIC_LOADERS = frozenset(
    {"importlib.import_module", "importlib.__import__", "builtins.__import__"}
)
"""Import by string: allowed with a constant name (then checked like an import
statement); with a computed name only in ``isolation`` (the executor seam)."""

PROCESS_FUNCTION = re.compile(
    r"(?:os|posix|nt)\.(?:system|popen|fork|forkpty|exec\w*|spawn\w*|posix_spawn\w*)"
)
"""Process creation through ``os`` (no import of a banned module needed)."""

FORBIDDEN_AT_RUNTIME = (
    "PIL",
    "samsungtvws",
    "urllib3",
    "certifi",
    "requests",
    "websocket",
    "socket",
    "_socket",
    "ssl",
    "_ssl",
    "http.client",
    "ctypes",
)
"""Modules the parent must not have loaded after importing the whole package,
apart from ``net.transport``, which only the entry point imports (Phase 6)."""

TRANSPORT_LOADS = ("urllib3", "certifi", "socket", "ssl", "http.client")
TRANSPORT_NEVER_LOADS = ("PIL", "samsungtvws", "requests", "websocket")

SKIPPED_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "htmlcov",
        "build",
        "dist",
        "node_modules",
    }
)


@dataclass(frozen=True, slots=True)
class ImportRef:
    """One imported module name as written in a source file."""

    module: str
    line: int
    dynamic: bool = False
    """Imported by string through one of :data:`DYNAMIC_LOADERS`."""

    @property
    def top(self) -> str:
        return self.module.split(".", 1)[0]


@dataclass(frozen=True, slots=True)
class SourceModule:
    path: Path
    tree: ast.Module

    @classmethod
    def synthetic(cls, relative: str, source: str) -> SourceModule:
        """A module at ``src/frame_gallery/<relative>`` that exists only in memory."""
        path = PACKAGE_ROOT / relative
        return cls(path, ast.parse(textwrap.dedent(source), filename=str(path)))

    @property
    def relative(self) -> str:
        return self.path.relative_to(PROJECT_ROOT).as_posix()

    @property
    def is_imaging_worker(self) -> bool:
        return self.path.parent == IMAGING_ROOT and self.path.name.startswith("worker_")

    @property
    def is_isolation(self) -> bool:
        return ISOLATION_ROOT in self.path.parents

    @property
    def is_selection(self) -> bool:
        return SELECTION_ROOT in self.path.parents

    @property
    def is_net(self) -> bool:
        return NET_ROOT in self.path.parents

    @property
    def is_net_transport(self) -> bool:
        return self.path == NET_TRANSPORT

    @property
    def is_tv_worker(self) -> bool:
        return self.path == TV_WORKER


Detector = Callable[[SourceModule], list[str]]


@cache
def _source_modules() -> tuple[SourceModule, ...]:
    paths = sorted(PACKAGE_ROOT.rglob("*.py"))
    return tuple(
        SourceModule(path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        for path in paths
    )


# --- name resolution -----------------------------------------------------------


def _aliases(tree: ast.Module) -> dict[str, str]:
    """Names bound by import statements anywhere in the module, mapped to the
    dotted name they stand for (``import os as o`` binds ``o`` to ``os``)."""
    names: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    names[alias.asname] = alias.name
                else:
                    top = alias.name.split(".", 1)[0]
                    names[top] = top
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for alias in node.names:
                names[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return names


def _qualified(node: ast.AST, aliases: Mapping[str, str]) -> str | None:
    """The dotted name an expression refers to: ``o.system`` and
    ``getattr(os, "system")`` both give ``os.system``, ``open`` gives
    ``builtins.open``. ``None`` for anything else."""
    if isinstance(node, ast.Name):
        if node.id in aliases:
            return aliases[node.id]
        return f"builtins.{node.id}" if hasattr(builtins, node.id) else None
    if isinstance(node, ast.Attribute):
        base = _qualified(node.value, aliases)
        return None if base is None else f"{base}.{node.attr}"
    if (
        isinstance(node, ast.Call)
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and isinstance(node.args[1].value, str)
        and _qualified(node.func, aliases) == "builtins.getattr"
    ):
        base = _qualified(node.args[0], aliases)
        return None if base is None else f"{base}.{node.args[1].value}"
    return None


def _references(module: SourceModule) -> Iterator[tuple[str, int]]:
    """Every dotted name the module refers to, with its line: expressions, and
    the members of ``from ... import`` statements."""
    aliases = _aliases(module.tree)
    for node in ast.walk(module.tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for alias in node.names:
                yield f"{node.module}.{alias.name}", node.lineno
        elif isinstance(node, ast.Name | ast.Attribute | ast.Call):
            name = _qualified(node, aliases)
            if name is not None:
                yield name, node.lineno


def _module_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level names bound exactly once in the whole module, to a string."""
    bindings = Counter(
        node.id if isinstance(node, ast.Name) else node.arg
        for node in ast.walk(tree)
        if (isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load))
        or isinstance(node, ast.arg)
    )
    constants: dict[str, str] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target, value = statement.targets[0], statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            target, value = statement.target, statement.value
        else:
            continue
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            and bindings[target.id] == 1
        ):
            constants[target.id] = value.value
    return constants


def _string(node: ast.expr | None, constants: Mapping[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    return None


def _argument(call: ast.Call, position: int, keyword: str) -> ast.expr | None:
    if len(call.args) > position:
        return call.args[position]
    return next((item.value for item in call.keywords if item.arg == keyword), None)


def _import_targets(call: ast.Call, constants: Mapping[str, str]) -> list[str] | None:
    """The modules a loader call imports, or ``None`` when they are computed
    (anything but a literal or a module-level string constant, or relative)."""
    if any(isinstance(item, ast.Starred) for item in call.args) or any(
        item.arg is None for item in call.keywords
    ):
        return None
    name = _string(_argument(call, 0, "name"), constants)
    if name is None or name.startswith("."):
        return None
    targets = [name]
    fromlist = _argument(call, 3, "fromlist")
    if fromlist is None or (isinstance(fromlist, ast.Constant) and fromlist.value is None):
        return targets
    if not isinstance(fromlist, ast.List | ast.Tuple):
        return None
    for element in fromlist.elts:
        member = _string(element, constants)
        if member is None:
            return None
        targets.append(f"{name}.{member}")
    return targets


def _loader_calls(module: SourceModule) -> Iterator[tuple[ast.Call, list[str] | None]]:
    aliases = _aliases(module.tree)
    constants = _module_constants(module.tree)
    for node in ast.walk(module.tree):
        if isinstance(node, ast.Call) and _qualified(node.func, aliases) in DYNAMIC_LOADERS:
            yield node, _import_targets(node, constants)


def _imports(module: SourceModule, *, members: bool = False) -> Iterator[ImportRef]:
    """Every absolute import, including imports by constant string. With
    ``members``, ``from a import b`` also yields ``a.b``, since ``b`` may be a
    submodule."""
    for node in ast.walk(module.tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield ImportRef(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield ImportRef(node.module, node.lineno)
            if members:
                for alias in node.names:
                    yield ImportRef(f"{node.module}.{alias.name}", node.lineno)
    for call, targets in _loader_calls(module):
        for target in targets or ():
            yield ImportRef(target, call.lineno, dynamic=True)


def _describe(module: SourceModule, ref: ImportRef) -> str:
    how = "imports by string" if ref.dynamic else "imports"
    return f"{module.relative}:{ref.line} {how} {ref.module}"


# --- detectors -------------------------------------------------------------------


def _third_party_allowed(module: SourceModule, top: str) -> bool:
    if top == "PIL":
        return module.is_imaging_worker
    if top in TV_THIRD_PARTY:
        return module.is_tv_worker
    return top in TRANSPORT_THIRD_PARTY and module.is_net_transport


def third_party_violations(module: SourceModule) -> list[str]:
    """D-107: the parent never imports Pillow; ``urllib3`` and ``certifi`` only
    in ``net/transport.py`` (D-131)."""
    return [
        _describe(module, ref)
        for ref in _imports(module)
        if not (
            ref.top == PACKAGE
            or ref.top in sys.stdlib_module_names
            or (ref.top in ALLOWED_THIRD_PARTY and _third_party_allowed(module, ref.top))
        )
    ]


def _banned_allowed(module: SourceModule, ref: ImportRef) -> bool:
    """Imports are listed with their members (``from http import server``
    also gives ``http.server``), so a permitted package cannot hide a
    forbidden submodule."""
    if module.is_net_transport:
        if ref.module in ("socket", "ssl", "http", "http.client"):
            return True
        if ref.module.startswith(("socket.", "ssl.", "http.client.")):
            return True
    if module.is_tv_worker and (ref.module == "socket" or ref.module.startswith("socket.")):
        return True  # the television worker's connect guard (Phase 5)
    if module.path == ISOLATION_PROCESS and ref.module in ("subprocess", "select"):
        return True  # the process executor (Phase 5, D-163)
    if module.path == ISOLATION_BOOTSTRAP and ref.module == "ctypes":
        return True  # prctl in the worker bootstrap (Phase 5, D-163)
    return module.is_net and (
        ref.module in NET_ONLY_MODULES
        or any(ref.module.startswith(f"{name}.") for name in NET_ONLY_MODULES)
    )


def banned_module_violations(module: SourceModule) -> list[str]:
    return [
        _describe(module, ref)
        for ref in _imports(module, members=True)
        if ref.top in BANNED_EVERYWHERE and not _banned_allowed(module, ref)
    ]


def transport_import_violations(module: SourceModule) -> list[str]:
    """Only the entry point (Phase 6) may import the real transport; every
    other module works against the ``net.wire`` protocols."""
    if module.path == PACKAGE_ROOT / "__main__.py":
        return []
    return [
        _describe(module, ref)
        for ref in _imports(module, members=True)
        if ref.module == NET_TRANSPORT_MODULE
    ]


def process_import_violations(module: SourceModule) -> list[str]:
    """Only the entry point (Phase 6) builds the process executor; every other
    module works against the ``Executor`` protocol."""
    if module.path == PACKAGE_ROOT / "__main__.py":
        return []
    return [
        _describe(module, ref)
        for ref in _imports(module, members=True)
        if ref.module == PROCESS_MODULE
    ]


def child_module_violations(module: SourceModule) -> list[str]:
    """The worker's own modules run only in the worker: ``BOOT`` names
    ``worker_main`` in a string, and only ``worker_main`` imports the
    bootstrap."""
    in_worker_main = module.path == ISOLATION_ROOT / "worker_main.py"
    return [
        _describe(module, ref)
        for ref in _imports(module, members=True)
        if ref.module == WORKER_MAIN_MODULE
        or (ref.module == BOOTSTRAP_MODULE and not in_worker_main)
    ]


def process_call_violations(module: SourceModule) -> list[str]:
    return [
        f"{module.relative}:{line} uses {name}"
        for name, line in _references(module)
        if PROCESS_FUNCTION.fullmatch(name)
    ]


def dynamic_import_violations(module: SourceModule) -> list[str]:
    """Outside ``isolation``, every loader is called with a constant name."""
    if module.is_isolation:
        return []
    aliases = _aliases(module.tree)
    violations: list[str] = []
    called: set[int] = set()
    for call, targets in _loader_calls(module):
        called.add(id(call.func))
        if targets is None:
            violations.append(f"{module.relative}:{call.lineno} imports a computed module name")
    for node in ast.walk(module.tree):
        if not isinstance(node, ast.Name | ast.Attribute | ast.Call) or id(node) in called:
            continue
        name = _qualified(node, aliases)
        if name in DYNAMIC_LOADERS:
            violations.append(f"{module.relative}:{node.lineno} passes {name} around")
    return violations


def _is_worker_module(name: str) -> bool:
    return name.startswith(WORKER_PREFIX) or name == TV_WORKER_MODULE


def worker_import_violations(module: SourceModule) -> list[str]:
    """The parent reaches the worker modules (the imaging workers and, from
    Phase 5, the television worker task) only through the executor's lazy,
    string-based import in ``isolation``, never through an import statement."""
    violations = []
    for ref in _imports(module, members=True):
        if not _is_worker_module(ref.module):
            continue
        if ref.dynamic:
            allowed = module.is_isolation
        else:
            allowed = module.is_imaging_worker and ref.module.startswith(WORKER_PREFIX)
        if not allowed:
            violations.append(_describe(module, ref))
    return violations


def selection_violations(module: SourceModule) -> list[str]:
    """Selection is pure (§5): no file-system or network module, no ``open``."""
    if not module.is_selection:
        return []
    violations = [
        _describe(module, ref) for ref in _imports(module) if ref.top in BANNED_IN_SELECTION
    ]
    violations.extend(
        f"{module.relative}:{line} uses {name}"
        for name, line in _references(module)
        if name in FILE_OPENERS
    )
    return violations


def relative_import_violations(module: SourceModule) -> list[str]:
    return [
        f"{module.relative}:{node.lineno} uses a relative import"
        for node in ast.walk(module.tree)
        if isinstance(node, ast.ImportFrom) and node.level > 0
    ]


def _tree_violations(detector: Detector) -> list[str]:
    return [violation for module in _source_modules() for violation in detector(module)]


# --- the source tree -------------------------------------------------------------


def test_the_source_tree_is_discovered() -> None:
    # Guard against the checks below passing vacuously.
    modules = {module.relative: module for module in _source_modules()}
    assert "src/frame_gallery/budget/phases.py" in modules
    assert "src/frame_gallery/selection/geometry.py" in modules
    assert "src/frame_gallery/imaging/worker_tasks.py" in modules
    assert len(modules) >= 30
    # The executor's lazy import resolves, so the worker rule sees it.
    in_process = modules["src/frame_gallery/isolation/in_process.py"]
    assert WORKER_TASKS in {ref.module for ref in _imports(in_process) if ref.dynamic}


def test_third_party_imports_are_confined_to_the_imaging_workers() -> None:
    assert _tree_violations(third_party_violations) == []


def test_no_module_uses_networking_or_process_modules() -> None:
    assert _tree_violations(banned_module_violations) == []


def test_only_the_entry_point_imports_the_real_transport() -> None:
    assert _tree_violations(transport_import_violations) == []


def test_networking_is_confined_to_the_transport_module() -> None:
    # Guard against the exceptions above passing vacuously.
    modules = {module.relative: module for module in _source_modules()}
    transport = modules["src/frame_gallery/net/transport.py"]
    tops = {ref.top for ref in _imports(transport)}
    assert {"socket", "ssl", "http", "urllib3", "certifi"} <= tops
    tv_worker = modules["src/frame_gallery/tv/samsung_task.py"]
    assert {ref.top for ref in _imports(tv_worker)} & TRANSPORT_NETWORK_MODULES == {"socket"}
    for module in modules.values():
        if module.is_net_transport:
            continue
        forbidden = TRANSPORT_NETWORK_MODULES | TRANSPORT_THIRD_PARTY
        if module.is_tv_worker:
            forbidden -= {"socket"}  # the connect guard only (Phase 5)
        assert not {ref.top for ref in _imports(module)} & forbidden, module.relative


def test_only_the_entry_point_builds_the_process_executor() -> None:
    assert _tree_violations(process_import_violations) == []


def test_the_worker_modules_run_only_in_the_worker() -> None:
    assert _tree_violations(child_module_violations) == []


def test_process_management_is_confined_to_the_executor() -> None:
    # Guard against the exceptions above passing vacuously.
    modules = {module.path: module for module in _source_modules()}
    assert {"subprocess", "select"} <= {ref.top for ref in _imports(modules[ISOLATION_PROCESS])}
    assert "ctypes" in {ref.top for ref in _imports(modules[ISOLATION_BOOTSTRAP])}
    for path, module in modules.items():
        tops = {ref.top for ref in _imports(module)}
        if path != ISOLATION_PROCESS:
            assert not tops & {"subprocess", "select"}, module.relative
        if path != ISOLATION_BOOTSTRAP:
            assert "ctypes" not in tops, module.relative


def test_the_isolation_code_is_covered_without_exemptions() -> None:
    """No branch of the worker's own code may be excluded from coverage: each
    is reached in-process through the injected seams (D-163)."""
    for path in (
        ISOLATION_ROOT / "bootstrap.py",
        ISOLATION_ROOT / "worker_main.py",
        ISOLATION_PROCESS,
        TV_WORKER,
    ):
        assert "pragma: no cover" not in path.read_text(encoding="utf-8"), path.name


def test_no_module_starts_a_process_through_os() -> None:
    assert _tree_violations(process_call_violations) == []


def test_only_isolation_imports_a_computed_module_name() -> None:
    assert _tree_violations(dynamic_import_violations) == []


def test_selection_has_no_file_system_or_network_access() -> None:
    assert any(module.is_selection for module in _source_modules())
    assert _tree_violations(selection_violations) == []


def test_worker_modules_are_imported_only_through_isolation() -> None:
    assert _tree_violations(worker_import_violations) == []


def test_no_relative_imports() -> None:
    assert _tree_violations(relative_import_violations) == []


# --- the detectors fail when a rule is broken --------------------------------------

VIOLATIONS: Final = [
    # Networking, process and foreign-code modules, wherever they are imported.
    *(
        pytest.param(banned_module_violations, "app/runner.py", source, id=source)
        for source in (
            "import _socket",
            "import _ssl",
            "import socket",
            "import socketserver",
            "import select",
            "import selectors",
            "import ctypes",
            "import pty",
            "from concurrent.futures import ThreadPoolExecutor",
            "import urllib.request as fetch",
            "def f():\n    import socketserver",
            "import importlib\nimportlib.import_module('socket')",
            "import importlib\nimportlib.import_module(name='_socket')",
            "import importlib\nimportlib.__import__('socket')",
            "__import__('ssl')",
            "import importlib as il\nNAME = 'socket'\nil.import_module(NAME)",
            "import importlib\ngetattr(importlib, 'import_module')('select')",
            "import urllib.parse",
        )
    ),
    # Networking modules elsewhere in net, or other urllib modules in net.
    *(
        pytest.param(banned_module_violations, relative, source, id=f"{relative}: {source}")
        for relative, source in (
            ("net/gateway.py", "import socket"),
            ("net/gateway.py", "import ssl"),
            ("net/policy.py", "import http.client"),
            ("net/policy.py", "from urllib.request import urlopen"),
            ("net/transport.py", "import urllib.request"),
            ("net/transport.py", "import select"),
            ("net/transport.py", "import subprocess"),
            ("net/transport.py", "import http.server"),
            ("net/transport.py", "from http import server"),
            ("net/transport.py", "from http import cookiejar"),
            ("net/transport.py", "from http import cookies"),
            ("net/transport.py", "from http.server import HTTPServer"),
            ("net/policy.py", "from urllib import request"),
            ("net/policy.py", "from urllib import parse"),
            ("ha/client.py", "import socket"),
            ("tv/samsung.py", "import socket"),
            ("tv/samsung_task.py", "import ssl"),
            ("tv/samsung_task.py", "import subprocess"),
            ("isolation/in_process.py", "import subprocess"),
            ("isolation/bootstrap.py", "import subprocess"),
            ("isolation/worker_main.py", "import select"),
            ("isolation/process.py", "import ctypes"),
            ("isolation/process.py", "import multiprocessing"),
            ("isolation/process.py", "import selectors"),
            ("isolation/bootstrap.py", "import socket"),
            ("providers/aic.py", "from urllib.parse import quote"),
        )
    ),
    # The process executor outside the entry point; the worker's modules
    # outside the worker.
    *(
        pytest.param(process_import_violations, relative, source, id=f"{relative}: {source}")
        for relative, source in (
            ("app/runner.py", "from frame_gallery.isolation.process import ProcessExecutor"),
            ("tv/samsung.py", "import frame_gallery.isolation.process"),
            ("isolation/in_process.py", "from frame_gallery.isolation import process"),
        )
    ),
    *(
        pytest.param(child_module_violations, relative, source, id=f"{relative}: {source}")
        for relative, source in (
            ("isolation/process.py", "from frame_gallery.isolation.bootstrap import run"),
            ("app/runner.py", "import frame_gallery.isolation.worker_main"),
            ("isolation/in_process.py", "from frame_gallery.isolation import worker_main"),
            ("isolation/bootstrap.py", "from frame_gallery.isolation.worker_main import main"),
        )
    ),
    # The real transport outside the entry point.
    *(
        pytest.param(transport_import_violations, relative, source, id=f"{relative}: {source}")
        for relative, source in (
            ("net/gateway.py", "from frame_gallery.net.transport import Urllib3Transport"),
            ("app/runner.py", "import frame_gallery.net.transport"),
            ("ha/client.py", "from frame_gallery.net import transport"),
        )
    ),
    # Process creation through os, in any spelling.
    *(
        pytest.param(process_call_violations, "budget/watchdog.py", source, id=source)
        for source in (
            "import os\nos.system('true')",
            "import os\nos.popen('true')",
            "import os\nos.fork()",
            "import os\nos.forkpty()",
            "import os\nos.execv('/bin/true', ['true'])",
            "import os\nos.execvpe('true', ['true'], {})",
            "import os\nos.spawnl(os.P_WAIT, '/bin/true', 'true')",
            "import os\nos.posix_spawn('/bin/true', ['true'], {})",
            "import os\nos.posix_spawnp('true', ['true'], {})",
            "import os as system_calls\nsystem_calls.system('true')",
            "from os import system",
            "from os import fork as clone\nclone()",
            "import os\nrun = getattr(os, 'system')",
            "import posix\nposix.fork()",
        )
    ),
    # Computed module names, and loaders passed around, outside isolation.
    *(
        pytest.param(dynamic_import_violations, "app/runner.py", source, id=source)
        for source in (
            "import importlib\ndef f(n: str) -> object:\n    return importlib.import_module(n)",
            "import importlib\nimportlib.import_module('frame_gallery.' + 'x')",
            "import importlib\nimportlib.__import__(NAME)",
            "__import__(NAME)",
            "__import__('frame_gallery', None, None, [MEMBER])",
            "import importlib\nimportlib.import_module('.worker_tasks', 'frame_gallery.imaging')",
            "import importlib\nimportlib.import_module(*names)",
            "import importlib\nimportlib.import_module(**options)",
            "from importlib import import_module as load\nload(NAME)",
            "import importlib\nload = importlib.import_module",
            "import importlib\nload = getattr(importlib, 'import_module')",
            "import builtins\nload = builtins.__import__",
            "NAME = 'json'\nNAME = 'socket'\n__import__(NAME)",
            "NAME = 'json'\ndef f(NAME: str) -> object:\n    return __import__(NAME)",
        )
    ),
    # Worker modules outside isolation's lazy import.
    *(
        pytest.param(worker_import_violations, relative, source, id=f"{relative}: {source}")
        for relative, source in (
            ("app/runner.py", f"import importlib\nimportlib.import_module({WORKER_TASKS!r})"),
            ("app/runner.py", "__import__('frame_gallery.imaging', fromlist=['worker_tasks'])"),
            ("app/runner.py", "from frame_gallery.imaging import worker_tasks"),
            ("app/runner.py", "import frame_gallery.imaging.worker_extra as extra"),
            ("isolation/in_process.py", "from frame_gallery.imaging.worker_tasks import prepare"),
            ("imaging/fit.py", "from frame_gallery.imaging.worker_tasks import prepare"),
            ("tv/samsung.py", "from frame_gallery.tv.samsung_task import run_delivery"),
            ("tv/samsung.py", "from frame_gallery.tv import samsung_task"),
            ("app/runner.py", f"import importlib\nimportlib.import_module({TV_WORKER_MODULE!r})"),
            ("imaging/worker_tasks.py", "from frame_gallery.tv.samsung_task import run_delivery"),
        )
    ),
    # Selection opens nothing and imports no file-system module.
    *(
        pytest.param(selection_violations, "selection/shortlist.py", source, id=source)
        for source in (
            "open('artwork.jpg')",
            "reader = open",
            "import builtins\nbuiltins.open('artwork.jpg')",
            "from builtins import open as read\nread('artwork.jpg')",
            "import io\nio.open('artwork.jpg')",
            "import codecs\ncodecs.open('artwork.jpg')",
            "import pathlib",
            "from os import path",
            "import shutil",
        )
    ),
    # Third-party modules outside the imaging workers.
    *(
        pytest.param(third_party_violations, relative, source, id=f"{relative}: {source}")
        for relative, source in (
            ("app/runner.py", "import requests"),
            ("app/runner.py", "import urllib3"),
            ("net/gateway.py", "import urllib3"),
            ("net/policy.py", "import certifi"),
            ("imaging/worker_tasks.py", "import urllib3"),
            ("net/transport.py", "from PIL import Image"),
            ("net/transport.py", "import requests"),
            ("imaging/fit.py", "from PIL import Image"),
            ("app/runner.py", "import importlib\nimportlib.import_module('PIL.Image')"),
            ("isolation/worker_tasks.py", "import PIL"),
            ("tv/samsung.py", "import samsungtvws"),
            ("tv/port.py", "import websocket"),
            ("isolation/process.py", "import requests"),
            ("imaging/worker_tasks.py", "from samsungtvws import SamsungTVArt"),
        )
    ),
    pytest.param(relative_import_violations, "app/runner.py", "from . import ports", id="relative"),
]


@pytest.mark.parametrize(("detector", "relative", "source"), VIOLATIONS)
def test_the_detectors_flag_every_violation(detector: Detector, relative: str, source: str) -> None:
    module = SourceModule.synthetic(relative, source)
    violations = detector(module)
    assert violations
    assert all(violation.startswith(f"src/frame_gallery/{relative}:") for violation in violations)


ALLOWED: Final = [
    pytest.param(
        banned_module_violations,
        "app/runner.py",
        "import os\nimport signal\nimport threading\nimport json\nimport importlib\n"
        "importlib.import_module('json')\nfrom frame_gallery.app import ports",
        id="standard-library",
    ),
    pytest.param(
        process_call_violations,
        "budget/watchdog.py",
        "import os\nos._exit(70)\nos.kill(os.getpid(), 15)\nos.open('x', os.O_RDONLY)\n"
        "os.fsync(3)\nos.environ.get('X')\nclass A:\n    def system(self) -> None:\n"
        "        self.system()",
        id="os-without-processes",
    ),
    pytest.param(
        dynamic_import_violations,
        "isolation/process.py",
        "import importlib\ndef f(name: str) -> object:\n    return importlib.import_module(name)",
        id="isolation-computes-names",
    ),
    pytest.param(
        dynamic_import_violations,
        "app/runner.py",
        "import importlib\nMODULE: str = 'json'\nimportlib.import_module(MODULE)\n"
        "importlib.import_module('json')\n__import__('json', fromlist=['decoder'])\n"
        "__import__('json', None, None, None)",
        id="constant-names",
    ),
    pytest.param(
        worker_import_violations,
        "isolation/in_process.py",
        "import importlib\nfrom typing import Final\n"
        "_WORKER_TASKS_MODULE: Final = " + repr(WORKER_TASKS) + "\n"
        "def _prepare() -> object:\n    return importlib.import_module(_WORKER_TASKS_MODULE)",
        id="isolation-lazy-import",
    ),
    pytest.param(
        worker_import_violations,
        "imaging/worker_extra.py",
        "from frame_gallery.imaging import worker_tasks",
        id="worker-to-worker",
    ),
    pytest.param(
        selection_violations,
        "selection/shortlist.py",
        "import heapq\nimport math\nfrom frame_gallery.domain import Size\n"
        "def f(item: object) -> object:\n    return item.open()",
        id="pure-selection",
    ),
    pytest.param(
        selection_violations, "app/records.py", "open('last_run.json')", id="not-selection"
    ),
    pytest.param(
        third_party_violations,
        "imaging/worker_tasks.py",
        "from PIL import Image\nimport importlib\nimportlib.import_module('PIL.ImageOps')",
        id="pillow-in-a-worker",
    ),
    pytest.param(
        relative_import_violations,
        "app/runner.py",
        "from frame_gallery.app import ports",
        id="absolute",
    ),
    pytest.param(
        banned_module_violations,
        "net/transport.py",
        "import socket\nimport ssl\nimport http.client\nfrom http.client import HTTPException",
        id="networking-in-the-transport",
    ),
    pytest.param(
        banned_module_violations,
        "net/policy.py",
        "from urllib.parse import quote, urlsplit\nimport urllib.parse",
        id="url-parsing-in-net",
    ),
    pytest.param(
        third_party_violations,
        "net/transport.py",
        "import certifi\nimport urllib3\nfrom urllib3.connection import HTTPSConnection",
        id="urllib3-in-the-transport",
    ),
    pytest.param(
        third_party_violations,
        "tv/samsung_task.py",
        "import samsungtvws\nimport websocket\nimport requests\nfrom samsungtvws import exceptions",
        id="the-library-in-the-television-worker",
    ),
    pytest.param(
        banned_module_violations,
        "tv/samsung_task.py",
        "import socket\nfrom socket import gaierror",
        id="the-connect-guard-in-the-television-worker",
    ),
    pytest.param(
        worker_import_violations,
        "isolation/process.py",
        "import importlib\nimportlib.import_module(" + repr(TV_WORKER_MODULE) + ")",
        id="isolation-lazy-import-of-the-television-worker",
    ),
    pytest.param(
        transport_import_violations,
        "__main__.py",
        "from frame_gallery.net.transport import Urllib3Transport",
        id="entry-point-wires-the-transport",
    ),
    pytest.param(
        banned_module_violations,
        "isolation/process.py",
        "import select\nimport subprocess",
        id="the-process-executor-manages-processes",
    ),
    pytest.param(
        banned_module_violations,
        "isolation/bootstrap.py",
        "def controls():\n    import ctypes",
        id="the-bootstrap-calls-prctl",
    ),
    pytest.param(
        process_import_violations,
        "__main__.py",
        "from frame_gallery.isolation.process import Launch, ProcessExecutor",
        id="entry-point-builds-the-process-executor",
    ),
    pytest.param(
        child_module_violations,
        "isolation/worker_main.py",
        "from frame_gallery.isolation.bootstrap import run",
        id="the-worker-entry-runs-the-bootstrap",
    ),
]


@pytest.mark.parametrize(("detector", "relative", "source"), ALLOWED)
def test_the_detectors_accept_allowed_code(detector: Detector, relative: str, source: str) -> None:
    assert detector(SourceModule.synthetic(relative, source)) == []


# --- the runtime check ------------------------------------------------------------

_CHILD_SCRIPT = """
import importlib
import json
import pkgutil
import sys

forbidden = sys.argv[1:]


def present():
    return sorted(name for name in forbidden if name in sys.modules)


baseline = present()
import frame_gallery

imported, skipped, culprits = [], [], {}
for info in pkgutil.walk_packages(frame_gallery.__path__, "frame_gallery."):
    leaf = info.name.rsplit(".", 1)[-1]
    if info.name.startswith("frame_gallery.imaging.") and leaf.startswith("worker_"):
        skipped.append(info.name)
        continue
    if info.name in ("frame_gallery.net.transport", "frame_gallery.tv.samsung_task"):
        skipped.append(info.name)
        continue
    before = set(present())
    importlib.import_module(info.name)
    imported.append(info.name)
    for name in sorted(set(present()) - before):
        culprits[name] = info.name

print(json.dumps({
    "baseline": baseline,
    "present": present(),
    "imported": imported,
    "skipped": skipped,
    "culprits": culprits,
}))
"""


def test_the_parent_package_loads_no_worker_or_network_library() -> None:
    # A fresh interpreter, so that nothing the test run loaded interferes.
    # The environment is minimal: no coverage start-up hooks, no bytecode files.
    env = {
        "PATH": os.environ.get("PATH", os.defpath),
        "PYTHONPATH": str(SRC_ROOT),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    completed = subprocess.run(  # noqa: S603 - fixed arguments: this interpreter and a literal
        [sys.executable, "-P", "-c", _CHILD_SCRIPT, *FORBIDDEN_AT_RUNTIME],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_ROOT,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)

    assert report["baseline"] == [], "the bare interpreter already loads a forbidden module"
    assert "frame_gallery.budget.phases" in report["imported"]
    assert "frame_gallery.app.ports" in report["imported"]
    assert WORKER_TASKS in report["skipped"]
    assert NET_TRANSPORT_MODULE in report["skipped"]
    assert TV_WORKER_MODULE in report["skipped"]
    assert "frame_gallery.tv.samsung" in report["imported"]
    assert "frame_gallery.net.gateway" in report["imported"]
    assert not any(name.startswith("frame_gallery.imaging.worker_") for name in report["imported"])
    assert report["present"] == [], f"loaded by: {report['culprits']}"


_TRANSPORT_SCRIPT = """
import json
import sys

names = sys.argv[1:]
before = sorted(name for name in names if name in sys.modules)
import frame_gallery.net.transport
after = sorted(name for name in names if name in sys.modules)
print(json.dumps({"before": before, "after": after}))
"""


def test_the_transport_loads_only_the_network_stack() -> None:
    env = {
        "PATH": os.environ.get("PATH", os.defpath),
        "PYTHONPATH": str(SRC_ROOT),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    names = (*TRANSPORT_LOADS, *TRANSPORT_NEVER_LOADS)
    completed = subprocess.run(  # noqa: S603 - fixed arguments: this interpreter and a literal
        [sys.executable, "-P", "-c", _TRANSPORT_SCRIPT, *names],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_ROOT,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["before"] == []
    assert set(report["after"]) == set(TRANSPORT_LOADS)


# --- D-125: the user's television address ----------------------------------------


def _project_files(root: Path) -> Iterator[Path]:
    """Every regular file under ``root``, without caches and environments.

    ``Path.walk`` lists symbolic links (to directories too) among the file
    names; they are skipped, so the scan never leaves ``root`` (L5-16).
    """
    for directory, subdirectories, files in root.walk():
        subdirectories[:] = [name for name in subdirectories if name not in SKIPPED_DIRECTORIES]
        for name in files:
            path = directory / name
            if (
                name in SKIPPED_DIRECTORIES
                or name.startswith(".coverage")
                or path.is_symlink()
                or not path.is_file()
            ):
                continue
            yield path


def _files_containing(root: Path, needle: bytes) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in _project_files(root)
        if needle in path.read_bytes()
    )


def _test_address() -> bytes:
    # Assembled at run time so that this file does not contain it either.
    return ("192.168.178" + ".30").encode()


def test_the_test_address_is_not_in_the_source() -> None:
    # D-125: the user's Phase 8 television address is never hard-coded.
    assert _files_containing(PACKAGE_ROOT, _test_address()) == []


def test_the_test_address_is_nowhere_in_the_app_directory() -> None:
    assert _files_containing(PROJECT_ROOT, _test_address()) == []


def test_the_address_scan_reads_only_regular_files_inside_the_directory(tmp_path: Path) -> None:
    app, outside = tmp_path / "app", tmp_path / "outside"
    (app / "src").mkdir(parents=True)
    (app / "__pycache__").mkdir()
    outside.mkdir()
    needle = b"frame-gallery-needle"
    (app / "src" / "module.py").write_bytes(b"VALUE = '" + needle + b"'\n")
    (app / "__pycache__" / "module.pyc").write_bytes(needle)
    (app / ".coverage.host").write_bytes(needle)
    (app / "build").write_bytes(needle)  # a file named like a skipped directory
    (outside / "shared.txt").write_bytes(needle)
    (app / ".venv").symlink_to(outside, target_is_directory=True)
    (app / "linked_directory").symlink_to(outside, target_is_directory=True)
    (app / "linked_file.txt").symlink_to(outside / "shared.txt")
    os.mkfifo(app / "pipe")  # reading it would block

    assert sorted(_project_files(app)) == [app / "src" / "module.py"]
    assert _files_containing(app, needle) == ["src/module.py"]
