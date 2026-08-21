"""Science Bridge: import established scientific ideas as *inspiration*, never as Aeterna evidence.

The bridge has three jobs:
1. Keep a curated registry of canonical papers/mechanisms relevant to emergence.
2. Optionally refresh metadata and discover additional candidate literature from public scholarly APIs.
3. Translate only explicitly curated mechanism cards into Free Hypothesis Lab directions.

A paper saying a mechanism exists elsewhere does not prove it exists in Aeterna.  Likewise a
literature-inspired intervention is exploratory/scaffolded evidence and can never promote a Room,
change an official Level, or count as strict-zero emergence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_SOURCES = _REPO / "ai_lab" / "discoveries" / "science_bridge_sources.json"
_DIRECTIONS = _REPO / "ai_lab" / "discoveries" / "science_bridge_directions.json"
_LEDGER = _REPO / "ai_lab" / "discoveries" / "science_bridge_ledger.json"
_REPORT_JSON = _REPO / "ai_lab" / "reports" / "easy" / "science_bridge_latest.json"
_REPORT_MD = _REPO / "ai_lab" / "reports" / "easy" / "science_bridge_latest.md"


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_doi(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text.strip() or None


def _fetch_json(url: str, *, timeout: float = 12.0) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Aeterna-Genesis-Science-Bridge/1.0 (+https://github.com/sunpotflower4460-cpu/Aeterna-Genesis)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - fixed public scholarly APIs
        return json.loads(response.read().decode("utf-8"))


def crossref_metadata(doi: str) -> dict[str, Any]:
    norm = normalize_doi(doi)
    if not norm:
        return {}
    url = "https://api.crossref.org/works/" + urllib.parse.quote(norm, safe="")
    payload = _fetch_json(url)
    msg = payload.get("message") or {}
    title = (msg.get("title") or [None])[0]
    authors = []
    for row in msg.get("author") or []:
        if not isinstance(row, dict):
            continue
        name = " ".join(x for x in (row.get("given"), row.get("family")) if x)
        if name:
            authors.append(name)
    published = msg.get("published-print") or msg.get("published-online") or msg.get("issued") or {}
    parts = published.get("date-parts") or []
    year = parts[0][0] if parts and parts[0] else None
    return {
        "doi": norm,
        "title": title,
        "authors": authors,
        "year": year,
        "publisher": msg.get("publisher"),
        "container_title": (msg.get("container-title") or [None])[0],
        "url": msg.get("URL"),
        "source": "crossref",
    }


def openalex_search(query: str, *, per_page: int = 4) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({
        "search": query,
        "per-page": max(1, min(10, int(per_page))),
        "select": "id,doi,title,publication_year,cited_by_count,primary_location,type,authorships",
    })
    payload = _fetch_json("https://api.openalex.org/works?" + params)
    rows: list[dict[str, Any]] = []
    for raw in payload.get("results") or []:
        if not isinstance(raw, dict):
            continue
        authors = []
        for auth in raw.get("authorships") or []:
            author = (auth or {}).get("author") or {}
            if author.get("display_name"):
                authors.append(author["display_name"])
        location = raw.get("primary_location") or {}
        rows.append({
            "openalex_id": raw.get("id"),
            "doi": normalize_doi(raw.get("doi")),
            "title": raw.get("title"),
            "year": raw.get("publication_year"),
            "cited_by_count": int(raw.get("cited_by_count", 0) or 0),
            "type": raw.get("type"),
            "authors": authors[:8],
            "landing_page_url": location.get("landing_page_url"),
            "source": "openalex-live-search",
            "query": query,
        })
    return rows


def _stable_source_key(row: dict[str, Any]) -> str:
    doi = normalize_doi(row.get("doi"))
    if doi:
        return "doi:" + doi
    if row.get("openalex_id"):
        return "openalex:" + str(row["openalex_id"]).rstrip("/").split("/")[-1]
    raw = f"{row.get('title')}|{row.get('year')}"
    return "title:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_directions(registry: dict[str, Any]) -> dict[str, Any]:
    directions: list[dict[str, Any]] = []
    for source in registry.get("sources") or []:
        if not isinstance(source, dict):
            continue
        doi = normalize_doi(source.get("doi"))
        for template in source.get("experiment_templates") or []:
            if not isinstance(template, dict) or not template.get("experiment_type"):
                continue
            directions.append({
                "id": "science-" + str(template.get("id") or source.get("id")),
                "enabled": True,
                "title": f"Science Bridge: {source.get('title')}",
                "question": template.get("question"),
                "rationale": (
                    f"Literature mechanism: {source.get('mechanism')}  "
                    f"Translation warning: {source.get('translation_warning')}"
                ),
                "experiment_type": template.get("experiment_type"),
                "parameters": dict(template.get("parameters") or {}),
                "author": f"science-bridge:{source.get('id')}:{doi or 'no-doi'}",
                "source_reference": {
                    "source_id": source.get("id"),
                    "title": source.get("title"),
                    "doi": doi,
                    "year": source.get("year"),
                    "domain": source.get("domain"),
                },
                "strict_transfer_question": template.get("strict_transfer_question"),
                "counts_as_strict_zero_evidence": False,
                "may_promote_room_or_level": False,
                "translation_is_analogy_not_reproduction": True,
            })
    return {
        "version": 1,
        "mode": "science-bridge-free-lab-directions",
        "generated_at": _now(),
        "directions": directions,
        "policy": {
            "literature_is_scientific_context_not_aeterna_evidence": True,
            "directions_run_only_in_exploratory_lane": True,
            "counts_as_strict_zero_evidence": False,
            "room_or_level_promotion_allowed": False,
            "target_morphology_may_be_copied_to_strict_lane": False,
        },
    }


def _merge_ledger(existing: dict[str, Any], rows: list[dict[str, Any]], *, seen_at: str) -> dict[str, Any]:
    by_key = {
        str(row.get("key")): dict(row)
        for row in (existing.get("sources") or [])
        if isinstance(row, dict) and row.get("key")
    }
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        key = _stable_source_key(raw)
        prior = by_key.get(key, {})
        seen_times = list(prior.get("seen_at") or [])
        if not seen_times or seen_times[-1] != seen_at:
            seen_times.append(seen_at)
        merged = {**prior, **raw}
        merged.update({
            "key": key,
            "first_seen_at": prior.get("first_seen_at") or seen_at,
            "last_seen_at": seen_at,
            "times_seen": int(prior.get("times_seen", 0) or 0) + int(prior.get("last_seen_at") != seen_at),
            "seen_at": seen_times[-24:],
        })
        by_key[key] = merged
    ordered = sorted(
        by_key.values(),
        key=lambda row: (int(row.get("cited_by_count", 0) or 0), str(row.get("year") or ""), str(row.get("key"))),
        reverse=True,
    )
    return {
        "version": 1,
        "mode": "science-bridge-literature-ledger",
        "sources": ordered,
        "count": len(ordered),
        "policy": {
            "dedupe_key_prefers_doi": True,
            "sources_are_deleted": False,
            "paper_claim_counts_as_aeterna_observation": False,
            "citation_count_is_scientific_truth_score": False,
        },
    }


def run(*, online: bool = False, max_live_results: int = 12, persist: bool = True) -> dict[str, Any]:
    registry = _read(_SOURCES, {"sources": []})
    now = _now()
    curated: list[dict[str, Any]] = []
    online_errors: list[dict[str, Any]] = []
    queries: list[str] = []
    for source in registry.get("sources") or []:
        if not isinstance(source, dict):
            continue
        row = dict(source)
        row["doi"] = normalize_doi(row.get("doi"))
        if online and row.get("doi"):
            try:
                row["live_metadata"] = crossref_metadata(str(row["doi"]))
            except Exception as exc:  # network failure is evidence-ingestion failure, not physics
                online_errors.append({"kind": "crossref", "source_id": row.get("id"), "error": type(exc).__name__})
        curated.append(row)
        queries.extend(str(q) for q in (row.get("search_queries") or []) if q)

    live: list[dict[str, Any]] = []
    if online:
        remaining = max(0, int(max_live_results))
        for query in queries:
            if remaining <= 0:
                break
            try:
                found = openalex_search(query, per_page=min(3, remaining))
                live.extend(found)
                remaining -= len(found)
            except Exception as exc:
                online_errors.append({"kind": "openalex", "query": query, "error": type(exc).__name__})

    # De-duplicate the current live discovery batch before writing the durable ledger.
    dedup: dict[str, dict[str, Any]] = {}
    for row in live:
        dedup[_stable_source_key(row)] = row
    live = list(dedup.values())[: max(0, int(max_live_results))]

    directions = build_directions(registry)
    report = {
        "version": 1,
        "mode": "science-bridge",
        "generated_at": now,
        "curated_sources": curated,
        "curated_source_count": len(curated),
        "executable_direction_count": len(directions.get("directions") or []),
        "live_candidates": live,
        "live_candidate_count": len(live),
        "online_requested": bool(online),
        "online_errors": online_errors,
        "interpretation": (
            "既存科学を答えとして移植するのではなく、既知の機構をAeternaで壊せる問いへ翻訳する。"
            "一致しても同じ物理の証明にはならず、不一致も重要な結果として残す。"
        ),
        "integrity": {
            "changes_strict_physics": False,
            "changes_strict_initial_conditions": False,
            "literature_claim_is_aeterna_evidence": False,
            "literature_inspired_experiment_is_strict_zero": False,
            "may_promote_rooms": False,
            "may_change_official_levels": False,
            "live_candidate_auto_becomes_experiment": False,
        },
    }

    if persist:
        existing = _read(_LEDGER, {"sources": []})
        ledger_rows: list[dict[str, Any]] = []
        for source in curated:
            ledger_rows.append({
                "source_id": source.get("id"),
                "doi": source.get("doi"),
                "title": source.get("title"),
                "year": source.get("year"),
                "authors": source.get("authors"),
                "domain": source.get("domain"),
                "mechanism": source.get("mechanism"),
                "curated": True,
                "live_metadata": source.get("live_metadata"),
            })
        ledger_rows.extend(live)
        ledger = _merge_ledger(existing, ledger_rows, seen_at=now)
        _write(_DIRECTIONS, directions)
        _write(_LEDGER, ledger)
        _write(_REPORT_JSON, report)
        _REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Science Bridge — latest",
            "",
            "既存科学から機構のヒントを取り込み、**Free/探索レーンだけ**で試すための橋です。論文の結果はAeternaの証拠ではありません。",
            "",
            f"- curated sources: {len(curated)}",
            f"- executable literature-inspired directions: {len(directions.get('directions') or [])}",
            f"- live literature candidates: {len(live)}",
            f"- online metadata/search errors: {len(online_errors)}",
            "",
        ]
        for source in curated:
            lines += [
                f"## {source.get('title')}",
                f"- DOI: `{source.get('doi')}`",
                f"- mechanism: {source.get('mechanism')}",
                f"- Aeternaへの翻訳上の注意: {source.get('translation_warning')}",
                "",
            ]
        lines += [
            "Live candidates are reading material for the AI Scientist. They are **not automatically treated as true or run as strict experiments**.",
            "",
        ]
        _REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Import scientific literature as separated experimental inspiration")
    ap.add_argument("--online", action="store_true", help="refresh Crossref metadata and discover OpenAlex candidates")
    ap.add_argument("--max-live-results", type=int, default=12)
    ap.add_argument("--no-record", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run(
        online=args.online,
        max_live_results=max(0, args.max_live_results),
        persist=not args.no_record,
    )
    print(
        "Science Bridge: "
        f"curated={report.get('curated_source_count')} "
        f"directions={report.get('executable_direction_count')} "
        f"live={report.get('live_candidate_count')} "
        f"errors={len(report.get('online_errors') or [])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
