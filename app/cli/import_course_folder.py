from __future__ import annotations

import argparse
import re
from pathlib import Path

from ..db import SessionLocal, init_db
from ..services.course_ingestion import DuplicateDocumentError, ingest_document_bytes
from ..services.documents import SUPPORTED_SUFFIXES, infer_document_type


def _path_metadata(root: Path, path: Path) -> tuple[str | None, str | None]:
    relative_parts = list(path.relative_to(root).parts[:-1])
    week = None
    topic = None
    for part in relative_parts:
        match = re.search(r"\bweek\s*([0-9]{1,2})\b", part, re.I)
        if match:
            week = f"Week {match.group(1)}"
    non_week = [p for p in relative_parts if not re.search(r"\bweek\s*[0-9]{1,2}\b", p, re.I)]
    if non_week:
        topic = non_week[-1]
    return week, topic


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recursively ingest a university module folder into the local Life OS academic index."
    )
    parser.add_argument("folder", type=Path)
    parser.add_argument("--module", required=True)
    parser.add_argument("--academic-year")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = args.folder.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"folder does not exist: {root}")

    files = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.casefold() in SUPPORTED_SUFFIXES
    )
    print(f"Found {len(files)} supported files under {root}")
    if args.dry_run:
        for path in files:
            week, topic = _path_metadata(root, path)
            print(
                f"DRY RUN | {path.relative_to(root)} | "
                f"type={infer_document_type(path.name)} | week={week} | topic={topic}"
            )
        return 0

    init_db()
    ingested = 0
    duplicate = 0
    failed = 0
    with SessionLocal() as db:
        for path in files:
            week, topic = _path_metadata(root, path)
            try:
                result = ingest_document_bytes(
                    db,
                    filename=path.name,
                    data=path.read_bytes(),
                    title=path.stem,
                    module=args.module,
                    week=week,
                    topic=topic,
                    document_type=infer_document_type(path.name),
                    academic_year=args.academic_year,
                    source="local_folder_import",
                    analyse=True,
                )
                ingested += 1
                print(
                    f"INGESTED | {path.relative_to(root)} | "
                    f"chunks={result['chunks']} | type={result['document_type']}"
                )
            except DuplicateDocumentError:
                duplicate += 1
                print(f"DUPLICATE | {path.relative_to(root)}")
            except Exception as exc:
                db.rollback()
                failed += 1
                print(f"FAILED | {path.relative_to(root)} | {type(exc).__name__}: {exc}")

    print(f"Done: {ingested} ingested, {duplicate} duplicates, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
