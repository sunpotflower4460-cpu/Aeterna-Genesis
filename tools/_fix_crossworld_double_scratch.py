from pathlib import Path

p = Path('ai_lab/dream/cross_world_emergence.py')
s = p.read_text()
old = '''    root = os.environ.get("AETERNA_DRY_RUN_ROOT")
    if not root:
        return path
    try:
        relative = path.resolve().relative_to(_REPO)
    except (OSError, ValueError):
        return path
    twin = Path(root) / relative
'''
new = '''    root = os.environ.get("AETERNA_DRY_RUN_ROOT")
    if not root:
        return path
    root_path = Path(root).resolve()
    try:
        resolved = path.resolve()
        # Multi-World may already have rebound this endpoint to the scratch tree.
        # Never wrap an already-scratch path a second time.
        resolved.relative_to(root_path)
        return path
    except ValueError:
        pass
    except OSError:
        return path
    try:
        relative = resolved.relative_to(_REPO)
    except (OSError, ValueError):
        return path
    twin = root_path / relative
'''
if old not in s:
    raise SystemExit('expected storage fragment not found')
p.write_text(s.replace(old, new, 1))
