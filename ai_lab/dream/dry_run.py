"""Make ``--no-record`` a true dry run by redirecting repository writes to a scratch root.

``--no-record`` used to gate a single call (``lab.record_search``). Every other persistence site --
Night/Easy reports, Rooms, jobs, view presets, the coverage atlas, the discovery ledgers and the
Dream state -- still wrote into the working tree, so a CI dry-run or a local run left roughly fifteen
modified or untracked paths behind and could overwrite real evidence.

Threading a flag through ~40 write sites in ~20 modules would be a large and risky refactor, so this
module instead installs a process-wide path redirect while a dry run is active:

* a write whose target is inside the repository is rewritten to the same relative path under
  ``runtime/dry-run/<name>/`` (``runtime/`` is gitignored),
* a read prefers the scratch copy when this run already produced one and otherwise falls through to
  the real repository, so read-back paths such as ``adaptive_v8._enrich_easy`` and the CI ``grep``
  checks still observe exactly what the run produced.

The redirect is inert unless :func:`activate` is called, so recording runs are untouched. Worker
processes are started with ``fork`` on Linux and therefore inherit the active redirect;
``AETERNA_DRY_RUN_ROOT`` is exported as well so a ``spawn`` start method re-activates it on import.
"""
from __future__ import annotations

import builtins
import os
from pathlib import Path
from typing import Any, Callable

_REPO = Path(__file__).resolve().parents[2]
_ENV = "AETERNA_DRY_RUN_ROOT"

_scratch: Path | None = None
_originals: dict[str, Callable[..., Any]] = {}


def is_active() -> bool:
    return _scratch is not None


def scratch_root() -> Path | None:
    return _scratch


def _redirect(target: Any, *, for_write: bool) -> Any:
    """Map a repository path onto its scratch twin.

    Writes always map. Reads only map when the scratch twin exists, so a dry run still sees the
    real accumulated evidence it has not rewritten yet.
    """
    if _scratch is None:
        return target
    try:
        path = Path(target)
        if not path.is_absolute():
            path = Path.cwd() / path
        relative = path.resolve().relative_to(_REPO)
    except (ValueError, OSError, TypeError):
        return target
    if relative.parts and relative.parts[0] == "runtime":
        return target
    twin = _scratch / relative
    if for_write:
        twin.parent.mkdir(parents=True, exist_ok=True)
        return twin
    return twin if twin.exists() else target


def _is_write_mode(mode: str) -> bool:
    return any(flag in mode for flag in ("w", "a", "x", "+"))


def activate(name: str = "latest") -> Path:
    """Redirect repository writes under ``runtime/dry-run/<name>/`` until the process exits."""
    global _scratch
    if _scratch is not None:
        return _scratch
    _scratch = _REPO / "runtime" / "dry-run" / name
    _scratch.mkdir(parents=True, exist_ok=True)
    os.environ[_ENV] = str(_scratch)

    _originals.update({
        "write_text": Path.write_text,
        "write_bytes": Path.write_bytes,
        "read_text": Path.read_text,
        "read_bytes": Path.read_bytes,
        "exists": Path.exists,
        "path_open": Path.open,
        "mkdir": Path.mkdir,
        "open": builtins.open,
        "replace": os.replace,
        "makedirs": os.makedirs,
    })

    def write_text(self: Path, *a: Any, **kw: Any) -> Any:
        return _originals["write_text"](_redirect(self, for_write=True), *a, **kw)

    def write_bytes(self: Path, *a: Any, **kw: Any) -> Any:
        return _originals["write_bytes"](_redirect(self, for_write=True), *a, **kw)

    def read_text(self: Path, *a: Any, **kw: Any) -> Any:
        return _originals["read_text"](_redirect(self, for_write=False), *a, **kw)

    def read_bytes(self: Path, *a: Any, **kw: Any) -> Any:
        return _originals["read_bytes"](_redirect(self, for_write=False), *a, **kw)

    def exists(self: Path, *a: Any, **kw: Any) -> bool:
        return bool(_originals["exists"](_redirect(self, for_write=False), *a, **kw))

    def path_open(self: Path, mode: str = "r", *a: Any, **kw: Any) -> Any:
        target = _redirect(self, for_write=_is_write_mode(mode))
        return _originals["path_open"](target, mode, *a, **kw)

    def mkdir(self: Path, *a: Any, **kw: Any) -> Any:
        return _originals["mkdir"](_redirect(self, for_write=True), *a, **kw)

    def open_(file: Any, mode: str = "r", *a: Any, **kw: Any) -> Any:
        if isinstance(file, (str, os.PathLike)):
            file = _redirect(file, for_write=_is_write_mode(mode))
        return _originals["open"](file, mode, *a, **kw)

    def replace(src: Any, dst: Any, *a: Any, **kw: Any) -> Any:
        # Atomic writes are tmp.write_text() followed by os.replace(tmp, path); the temporary file
        # already landed in the scratch root, so the source has to be resolved there as well.
        return _originals["replace"](
            _redirect(src, for_write=False), _redirect(dst, for_write=True), *a, **kw
        )

    def makedirs(name: Any, *a: Any, **kw: Any) -> Any:
        return _originals["makedirs"](_redirect(name, for_write=True), *a, **kw)

    Path.write_text = write_text  # type: ignore[method-assign]
    Path.write_bytes = write_bytes  # type: ignore[method-assign]
    Path.read_text = read_text  # type: ignore[method-assign]
    Path.read_bytes = read_bytes  # type: ignore[method-assign]
    Path.exists = exists  # type: ignore[method-assign]
    Path.open = path_open  # type: ignore[method-assign]
    Path.mkdir = mkdir  # type: ignore[method-assign]
    builtins.open = open_  # type: ignore[assignment]
    os.replace = replace  # type: ignore[assignment]
    os.makedirs = makedirs  # type: ignore[assignment]
    return _scratch


def deactivate() -> None:
    """Restore real I/O. Used by tests; production processes simply exit."""
    global _scratch
    if _scratch is None:
        return
    Path.write_text = _originals["write_text"]  # type: ignore[method-assign]
    Path.write_bytes = _originals["write_bytes"]  # type: ignore[method-assign]
    Path.read_text = _originals["read_text"]  # type: ignore[method-assign]
    Path.read_bytes = _originals["read_bytes"]  # type: ignore[method-assign]
    Path.exists = _originals["exists"]  # type: ignore[method-assign]
    Path.open = _originals["path_open"]  # type: ignore[method-assign]
    Path.mkdir = _originals["mkdir"]  # type: ignore[method-assign]
    builtins.open = _originals["open"]  # type: ignore[assignment]
    os.replace = _originals["replace"]  # type: ignore[assignment]
    os.makedirs = _originals["makedirs"]  # type: ignore[assignment]
    _originals.clear()
    os.environ.pop(_ENV, None)
    _scratch = None


if os.environ.get(_ENV) and _scratch is None:  # re-activate inside a spawned worker
    activate(Path(os.environ[_ENV]).name)
