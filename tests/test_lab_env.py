"""Credential files are opt-in, never executed, and never disclosed in errors."""
import os

import pytest

from tools.lab.env import load_credentials


def test_credentials_preserve_existing_environment_and_do_not_execute(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('OPENAI_API_KEY', 'existing-test-key')
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    file = tmp_path / '.env.local'
    file.write_text('# comment\nOPENAI_API_KEY="another-test-key"\nexport GEMINI_API_KEY=literal-$(ignored)\n')
    load_credentials(file)
    assert os.environ['OPENAI_API_KEY'] == 'existing-test-key'
    assert os.environ['GEMINI_API_KEY'] == 'literal-$(ignored)'
    assert not capsys.readouterr().out


def test_malformed_file_is_atomic_and_error_does_not_echo_secrets(tmp_path, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    file = tmp_path / '.env.local'
    file.write_text('OPENAI_API_KEY=test-key-only\nUNKNOWN=private-test-value\n')
    with pytest.raises(ValueError) as error:
        load_credentials(file)
    assert 'private-test-value' not in str(error.value) and 'test-key-only' not in str(error.value)
    assert 'OPENAI_API_KEY' not in os.environ
