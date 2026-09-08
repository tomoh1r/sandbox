#!/usr/bin/env python3
"""Generate a quick, dependency-free health report for a directory."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import html
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent
from typing import Iterable, TypedDict, cast


SKIP_DIRS: set[str] = {".git", ".venv", "__pycache__", "node_modules"}


@dataclass(frozen=True, slots=True)
class FileFact:
    """ファイルの相対パス・容量・UTC 更新日時・短縮ハッシュ・拡張子。"""

    path: str
    bytes: int
    modified: str
    sha256_12: str
    suffix: str


class FileRecord(TypedDict):
    """JSON に保存するファイル情報。"""

    path: str
    bytes: int
    modified: str
    sha256_12: str
    suffix: str


class Report(TypedDict):
    """集計結果と容量上位10件・全ファイルの情報。"""

    generated_at: str
    file_count: int
    total_bytes: int
    types: dict[str, int]
    largest: list[FileRecord]
    files: list[FileRecord]


def discover(root: Path) -> list[Path]:
    """root 以下の対象ファイルを、除外ディレクトリを除いて列挙する。"""
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part in SKIP_DIRS for part in path.parts)
    )


def inspect_file(path: Path, root: Path) -> FileFact:
    """ファイルを読み、root からの相対パスと属性・ハッシュを返す。"""
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return FileFact(
        path=path.relative_to(root).as_posix(),
        bytes=stat.st_size,
        modified=datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
        sha256_12=digest.hexdigest()[:12],
        suffix=path.suffix.lower() or "(none)",
    )


async def scan(root: Path) -> list[FileFact]:
    """root 以下のファイル情報をスレッドで並行収集する。"""
    paths = discover(root)
    tasks: list[asyncio.Task[FileFact]] = []
    async with asyncio.TaskGroup() as group:
        for path in paths:
            tasks.append(group.create_task(asyncio.to_thread(inspect_file, path, root)))
    return [task.result() for task in tasks]


def summarize(facts: Iterable[FileFact]) -> Report:
    """ファイル情報から件数・容量・拡張子別件数を集計する。"""
    rows = list(facts)
    suffixes = Counter(item.suffix for item in rows)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "file_count": len(rows),
        "total_bytes": sum(item.bytes for item in rows),
        "types": dict(suffixes.most_common()),
        "largest": [cast(FileRecord, asdict(item)) for item in sorted(rows, key=lambda x: x.bytes, reverse=True)[:10]],
        "files": [cast(FileRecord, asdict(item)) for item in rows],
    }


def render_html(report: Report, root: Path) -> str:
    """集計結果と対象パスを表示する HTML を生成する。"""
    template = dedent("""
        <!doctype html>
        <html lang="ja">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width">
            <title>Sandbox Pulse</title>
            <style>
                :root {{ color-scheme: dark; font-family: ui-sans-serif, system-ui; }}
                body {{ max-width: 920px; margin: 3rem auto; padding: 0 1.2rem; background:#0b1020; color:#e8ecf7; }}
                .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1rem; }}
                .card, table {{ background:#141b31; border:1px solid #283352; border-radius:14px; padding:1rem; }}
                .big {{ font-size:2rem; color:#76e6c2; }} table {{ width:100%; border-collapse:collapse; margin-top:1rem; }}
                td,th {{ text-align:left; padding:.65rem; border-bottom:1px solid #283352; }} code {{ color:#f5c76b; }}
            </style>
        </head>
        <body>
            <h1>⚡ Sandbox Pulse</h1>
            <p>{root_path}</p><div class="cards">
            <div class="card"><div>Files</div><div class="big">{file_count}</div></div>
            <div class="card"><div>Total size</div><div class="big">{total_bytes} B</div></div>
            <div class="card"><div>Types</div><div class="big">{types}</div></div>
            </div><h2>Largest files</h2><table><thead><tr><th>Path</th><th>Bytes</th><th>SHA-256</th></tr></thead>
            <tbody>{table}</tbody></table><h2>File types</h2><pre>{type_data}</pre>
            <p>Generated {generated_at}</p>
        </body>
        </html>
    """.strip())
    rows = report["largest"]
    assert isinstance(rows, list)
    table = "".join(
        f"<tr><td>{html.escape(str(row['path']))}</td><td>{int(row['bytes']):,}</td>"
        f"<td><code>{row['sha256_12']}</code></td></tr>"
        for row in rows
    )
    type_data = json.dumps(report["types"], ensure_ascii=False)
    params = {
        "root_path": html.escape(str(root)),
        "file_count": report['file_count'],
        "total_bytes": int(report['total_bytes']),
        "types": len(report['types']),
        "table": table,
        "type_data": html.escape(type_data),
        "generated_at": report['generated_at'],
    }
    return template.format(**params)


async def main() -> None:
    """CLI 引数を読み取り、対象フォルダーの JSON・HTML を保存する。"""
    parser = argparse.ArgumentParser(description="Scan a folder and generate JSON + HTML health reports.")
    parser.add_argument("path", nargs="?", default=".", type=Path)
    parser.add_argument("--out", default=Path("outputs"), type=Path)
    args = parser.parse_args()
    root: Path = args.path.resolve()
    out: Path = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    facts = await scan(root)
    report = summarize(facts)
    (out / "pulse.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "pulse.html").write_text(render_html(report, root), encoding="utf-8")
    print(f"Scanned {report['file_count']} files ({report['total_bytes']:,} bytes)")
    print(f"Open: {out / 'pulse.html'}")


if __name__ == "__main__":
    asyncio.run(main())
