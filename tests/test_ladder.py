"""The ladder (docs/LADDER.md, research/ladder.json) stays consistent: evidence exists, hypotheses exist."""
import copy

from tools import ladder


def test_the_real_ladder_passes_the_check():
    assert ladder.check(ladder.load()) == []


def test_the_summary_names_the_top_reached_rung():
    lines = ladder.summary(ladder.load())
    assert lines[1].startswith("いま：")
    assert any(line.startswith("○ R7") or line.startswith("● R7") or line.startswith("◐ R7") for line in lines)


def test_broken_ladders_are_caught():
    d = ladder.load()
    bad = copy.deepcopy(d)
    bad["rungs"][7]["status"] = "reached"                       # reached with no evidence
    assert any("証拠がない" in p for p in ladder.check(bad))
    bad = copy.deepcopy(d)
    bad["rungs"][1]["evidence"] = [{"claim": "x", "file": "docs/does-not-exist.md"}]
    assert any("ファイル" in p for p in ladder.check(bad))
    bad = copy.deepcopy(d)
    bad["rungs"][4]["hypotheses"] = ["H999"]
    assert any("H999" in p for p in ladder.check(bad))
    bad = copy.deepcopy(d)
    bad["rungs"][2]["status"] = "done"
    assert any("status" in p for p in ladder.check(bad))
    bad = copy.deepcopy(d)
    bad["integrated"] = True
    assert any("integrated" in p for p in ladder.check(bad))
    bad = copy.deepcopy(d)
    bad["rungs"][3]["note"] = ""
    assert any("partial" in p for p in ladder.check(bad))


def test_the_cli(capsys):
    assert ladder.main(["--check"]) == 0
    assert capsys.readouterr().out.strip().endswith("ok")
    assert ladder.main([]) == 0
    assert "北極星" in capsys.readouterr().out
