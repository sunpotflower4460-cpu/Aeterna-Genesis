"""Download an argon archive and check its bytes against the versioned study ledger."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile

from tools.study_record import check_record, read_object, sha256


def fetch(campaign, destination, local_archive=None):
    expected = read_object(campaign / "ARCHIVE.json")
    record_file = campaign / "evidence" / "record.json"
    record = read_object(record_file)
    members = {"record.json"}
    for attempts in record["cases"].values():
        for attempt in attempts:
            members.update(attempt.get("artifacts", {}).keys())
    for name in members:
        if not name or Path(name).name != name or name in (".", "..") or "\\" in name:
            raise ValueError(f"expected a single relative filename: {name!r}")
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as work:
        root = Path(work)
        archive = local_archive
        if archive is None:
            archive = root / "evidence.zip"
            with urlopen(expected["url"], timeout=90) as response, archive.open("wb") as out:
                shutil.copyfileobj(response, out)
        if sha256(archive) != expected["sha256"]:
            raise ValueError("downloaded ZIP checksum differs from ARCHIVE.json")
        data = root / "verified"
        data.mkdir()
        with ZipFile(archive) as zipped:
            names = zipped.namelist()
            if len(names) != len(members) or set(names) != members:
                raise ValueError("ZIP members differ from the study ledger")
            for name in names:
                with zipped.open(name) as stream, (data / name).open("wb") as output:
                    shutil.copyfileobj(stream, output)
        if sha256(data / "record.json") != sha256(record_file):
            raise ValueError("archive ledger differs from the Git record")
        counts = check_record(campaign / "PLAN.json", data / "record.json")
        data.rename(destination)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--zip", type=Path)
    args = parser.parse_args()
    print(fetch(args.campaign.resolve(), args.out.resolve(), args.zip.resolve() if args.zip else None))


if __name__ == "__main__":
    main()
