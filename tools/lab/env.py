"""Opt-in loading of server-only credentials. No shell evaluation and no credential output."""
from __future__ import annotations

import os
import re
from pathlib import Path

KEYS = {'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'DEEPSEEK_API_KEY', 'GEMINI_API_KEY'}


def load_credentials(path: Path) -> None:
    pending = {}
    for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, sep, value = line.removeprefix('export ').partition('=')
        name, value = name.strip(), value.strip()
        if not sep or name not in KEYS:
            raise ValueError(f'認証ファイルの {line_no} 行目は未対応の形式です（APIキーの変数だけ使用可能）')
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f'認証ファイルの {line_no} 行目の引用符を確認してください')
            value = value[1:-1]
        if not value or re.search(r'\s', value):
            raise ValueError(f'認証ファイルの {line_no} 行目の値を確認してください')
        pending[name] = value
    for name, value in pending.items():
        os.environ.setdefault(name, value)
