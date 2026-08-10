from pathlib import Path

p = Path('ai_lab/dream/cross_world_emergence.py')
s = p.read_text()

def rep(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit(f'missing expected fragment: {old[:80]!r}')
    s = s.replace(old, new, 1)

rep('import math\nfrom pathlib import Path', 'import math\nimport os\nfrom pathlib import Path')
rep(
    '_REPORT = _REPO / "ai_lab" / "reports" / "crossworld" / "latest.json"\n\nOBSERVABLE_DEFINITION_VERSION = 2',
    '_REPORT = _REPO / "ai_lab" / "reports" / "crossworld" / "latest.json"\n\n\ndef _storage_path(path: Path, *, for_write: bool = False) -> Path:\n    """Honor the process dry-run root explicitly for comparator persistence.\n\n    The generic dry-run I/O redirect remains the broad safety net, but this comparator owns two\n    durable files and therefore resolves them explicitly as a second integrity barrier.\n    """\n    root = os.environ.get("AETERNA_DRY_RUN_ROOT")\n    if not root:\n        return path\n    try:\n        relative = path.resolve().relative_to(_REPO)\n    except (OSError, ValueError):\n        return path\n    twin = Path(root) / relative\n    if for_write:\n        twin.parent.mkdir(parents=True, exist_ok=True)\n        return twin\n    return twin if twin.exists() else path\n\n\nOBSERVABLE_DEFINITION_VERSION = 2'
)
rep(
    'def _load_json(path: Path, fallback: Any) -> Any:\n    if path.exists():\n        try:\n            return json.loads(path.read_text())',
    'def _load_json(path: Path, fallback: Any) -> Any:\n    path = _storage_path(path, for_write=False)\n    if path.exists():\n        try:\n            return json.loads(path.read_text())'
)
rep(
    '    _LEDGER.parent.mkdir(parents=True, exist_ok=True)\n    _LEDGER.write_text(json.dumps(ledger, indent=2, ensure_ascii=False))\n    return ledger',
    '    ledger_path = _storage_path(_LEDGER, for_write=True)\n    ledger_path.parent.mkdir(parents=True, exist_ok=True)\n    ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False))\n    return ledger'
)
rep(
    '    _REPORT.parent.mkdir(parents=True, exist_ok=True)\n    _REPORT.write_text(json.dumps(summary, indent=2, ensure_ascii=False))\n    return summary',
    '    report_path = _storage_path(_REPORT, for_write=True)\n    report_path.parent.mkdir(parents=True, exist_ok=True)\n    report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))\n    return summary'
)
p.write_text(s)
print('cross-world dry-run persistence patched')
